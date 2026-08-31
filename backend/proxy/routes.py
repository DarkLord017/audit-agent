"""The chokepoint. Every request the worker makes passes through here."""

import json
import logging
import os

import httpx
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse

from backend.proxy.spend import (
    DEFAULT_MAX_TOKENS,
    BudgetExceeded,
    JobNotSpendable,
    SpendTracker,
)
from backend.proxy.tokens import BadToken, TokenVault
from backend.utils.models import MODELS, UnknownModel

log = logging.getLogger(__name__)


class ProxyAPI:
    """Relays worker requests to Anthropic, swapping the token for the key.

    The worker never holds the real key. It is attached here, outside the
    container, after the request has left. Because every call passes
    through, this is also where budget and liveness are enforced.
    """

    UPSTREAM = "https://api.anthropic.com"

    # The worker has no business calling anything else.
    ALLOWED_PATHS = {"messages", "messages/count_tokens"}

    # Allowlist, not denylist. The worker is untrusted
    # (permission_mode=bypassPermissions plus attacker-controlled unzipped
    # code) and can inject hop-by-hop or Anthropic-specific headers a
    # denylist would miss: x-forwarded-*, extra anthropic-*, authorization.
    # Only headers the Claude Agent SDK / Claude Code CLI actually needs
    # are copied; x-api-key, workspace id, and accept-encoding are set
    # here, never taken from the worker.
    ALLOWED_HEADERS = {
        "content-type",
        "anthropic-version",
        # Claude Code CLI sends this for prompt caching and other betas.
        "anthropic-beta",
    }

    # Identity-linked keys are scoped to a workspace and the API refuses a
    # request that does not name one:
    #   400 anthropic-workspace-id is required when authenticating with an
    #   identity-linked API key
    # Blank for an ordinary key, which needs no such header.
    WORKSPACE_ID = os.getenv("ANTHROPIC_WORKSPACE_ID", "").strip()

    def __init__(self, vault: TokenVault | None = None, spend: SpendTracker | None = None):
        self.vault = vault or TokenVault()
        self.spend = spend or SpendTracker()
        self.client = httpx.AsyncClient(timeout=httpx.Timeout(600.0, connect=10.0))
        self.router = APIRouter(tags=["proxy"])
        self.router.add_api_route("/v1/{path:path}", self.forward, methods=["POST"])

    # --- checks, all run before we spend anything ---------------------

    def read_token(self, request: Request) -> str:
        """Pull the job token off the request.

        The Anthropic SDK -- and so the Claude Code CLI the worker runs --
        sends its key as `x-api-key`, not as a bearer token. Reading only
        `authorization` meant every worker request was rejected 401 before
        it reached the vault. Bearer is still accepted for anything that
        speaks that dialect.
        """
        api_key = (request.headers.get("x-api-key") or "").strip()
        if api_key:
            return api_key

        header = request.headers.get("authorization") or ""
        if header.startswith("Bearer "):
            return header.removeprefix("Bearer ").strip()

        raise HTTPException(
            status_code=401, detail="missing x-api-key or bearer token"
        )

    def check_path(self, path: str) -> None:
        if path.strip("/") not in self.ALLOWED_PATHS:
            raise HTTPException(status_code=403, detail=f"path not allowed: {path}")

    def check_model(self, body: dict) -> str:
        """One list, in backend.utils.models. A model with no price would
        cost nothing to track, and therefore have no budget at all."""
        try:
            return MODELS.get(body.get("model")).key
        except UnknownModel as exc:
            raise HTTPException(status_code=403, detail=str(exc)) from None

    # --- the relay ----------------------------------------------------

    async def forward(self, path: str, request: Request):
        self.check_path(path)
        token = self.read_token(request)

        try:
            real_key, job_id = self.vault.redeem(token)
        except BadToken as exc:
            raise HTTPException(status_code=401, detail=str(exc)) from None

        body = await request.body()
        try:
            payload = json.loads(body)
        except ValueError:
            raise HTTPException(status_code=400, detail="body must be JSON") from None
        model = self.check_model(payload)

        # Charge the worst case up front, atomically. Twelve subagents
        # firing at once cannot all pass the same check any more --
        # whoever cannot afford their reservation is refused here, and
        # the request never reaches Anthropic.
        try:
            reserved = self.spend.reserve(
                job_id,
                model,
                input_tokens=self._rough_input_tokens(body),
                max_tokens=int(payload.get("max_tokens") or DEFAULT_MAX_TOKENS),
            )
        except JobNotSpendable as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from None
        except BudgetExceeded as exc:
            raise HTTPException(status_code=402, detail=str(exc)) from None
        except UnknownModel as exc:
            raise HTTPException(status_code=403, detail=str(exc)) from None

        headers = self._upstream_headers(request.headers.items(), real_key)

        upstream = self.client.build_request(
            "POST", f"{self.UPSTREAM}/v1/{path.strip('/')}", headers=headers, content=body,
        )
        resp = await self.client.send(upstream, stream=True)

        # Stream both ways. Agent replies are long; buffering them whole
        # would add seconds of delay to every turn. We tee the bytes as
        # they pass so usage can be billed once the reply is complete.
        return StreamingResponse(
            self._relay_and_bill(resp, job_id, model, reserved),
            status_code=resp.status_code,
            media_type=resp.headers.get("content-type"),
        )

    @classmethod
    def _upstream_headers(cls, incoming, real_key: str) -> dict[str, str]:
        """Copy only allowlisted worker headers; attach the real key here.

        Incoming keys are matched case-insensitively. `x-api-key` and
        `anthropic-workspace-id` are never taken from the worker.
        """
        incoming = list(incoming)
        headers = {
            k: v for k, v in incoming
            if k.lower() in cls.ALLOWED_HEADERS
        }
        headers["x-api-key"] = real_key          # <- the swap; never from the worker
        if cls.WORKSPACE_ID:
            headers["anthropic-workspace-id"] = cls.WORKSPACE_ID
        headers.setdefault("anthropic-version", "2023-06-01")
        headers["accept-encoding"] = "identity"
        return headers

    @staticmethod
    def _rough_input_tokens(body: bytes) -> int:
        """A cheap over-estimate: roughly four bytes per token."""
        return len(body) // 4 + 1

    async def _relay_and_bill(self, resp, job_id: str, model: str, reserved):
        chunks: list[bytes] = []
        try:
            # Decoded, not raw. aiter_raw yields the bytes exactly as
            # upstream sent them -- gzip included -- while the response we
            # build never re-declares content-encoding. The worker would
            # get compressed bytes labelled as JSON and fail to parse
            # them, and _settle would fail to find usage in them and keep
            # the pessimistic reservation.
            async for chunk in resp.aiter_bytes():
                chunks.append(chunk)
                yield chunk
        finally:
            await resp.aclose()
            try:
                self._settle(b"".join(chunks), job_id, model, reserved)
            except Exception:
                # Never let billing break the response the worker is reading.
                log.exception("could not settle spend for job %s", job_id)

    def _settle(self, body: bytes, job_id: str, model: str, reserved) -> None:
        """Swap the reservation for what it really cost.

        If usage is missing -- a worker that hangs up before the final
        message_delta, for instance -- the reservation stands. Keeping
        the pessimistic charge is the safe direction to be wrong in.
        """
        usage = self._read_usage(body)
        if usage is None:
            log.warning("no usage in reply for job %s; keeping the reservation", job_id)
            return
        self.spend.settle(job_id, model, reserved, *usage)

    @staticmethod
    def _read_usage(body: bytes) -> tuple[int, int, int, int] | None:
        """Pull (input, output, cache_write, cache_read) out of a reply.

        Non-streaming replies carry `usage` at the top level. Streaming
        replies send it across two events: message_start has the input
        counts, and the final message_delta has the output count.

        The cache counters matter as much as input_tokens: Claude Code
        caches its system prompt, so a warm request reports input_tokens
        in the tens while reading tens of thousands from cache.
        """
        def counts(u: dict) -> tuple[int, int, int]:
            return (
                int(u.get("input_tokens", 0) or 0),
                int(u.get("cache_creation_input_tokens", 0) or 0),
                int(u.get("cache_read_input_tokens", 0) or 0),
            )

        text = body.decode("utf-8", errors="replace")

        if not text.lstrip().startswith("event:") and "data:" not in text:
            try:
                usage = json.loads(text).get("usage") or {}
                inp, cw, cr = counts(usage)
                return inp, int(usage.get("output_tokens", 0) or 0), cw, cr
            except (ValueError, AttributeError, TypeError):
                return None

        inp = out = cw = cr = 0
        for line in text.splitlines():
            if not line.startswith("data:"):
                continue
            try:
                event = json.loads(line[5:].strip())
            except ValueError:
                continue
            if event.get("type") == "message_start":
                inp, cw, cr = counts(event.get("message", {}).get("usage", {}))
            elif event.get("type") == "message_delta":
                out = int(event.get("usage", {}).get("output_tokens", out) or out)
        return (inp, out, cw, cr) if (inp or out or cw or cr) else None

    async def aclose(self) -> None:
        await self.client.aclose()
