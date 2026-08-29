"""The chokepoint. Every request the worker makes passes through here."""

import json
import logging

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

    # Headers we refuse to pass on. Authorization is replaced, and the
    # hop-by-hop ones describe our connection, not the upstream one.
    DROP_HEADERS = {
        "authorization", "x-api-key", "host", "content-length",
        "connection", "keep-alive", "transfer-encoding",
    }

    def __init__(self, vault: TokenVault | None = None, spend: SpendTracker | None = None):
        self.vault = vault or TokenVault()
        self.spend = spend or SpendTracker()
        self.client = httpx.AsyncClient(timeout=httpx.Timeout(600.0, connect=10.0))
        self.router = APIRouter(tags=["proxy"])
        self.router.add_api_route("/v1/{path:path}", self.forward, methods=["POST"])

    # --- checks, all run before we spend anything ---------------------

    def read_token(self, request: Request) -> str:
        header = request.headers.get("authorization") or ""
        if not header.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="missing bearer token")
        return header.removeprefix("Bearer ").strip()

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

        headers = {
            k: v for k, v in request.headers.items()
            if k.lower() not in self.DROP_HEADERS
        }
        headers["x-api-key"] = real_key          # <- the swap
        headers.setdefault("anthropic-version", "2023-06-01")

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

    @staticmethod
    def _rough_input_tokens(body: bytes) -> int:
        """A cheap over-estimate: roughly four bytes per token."""
        return len(body) // 4 + 1

    async def _relay_and_bill(self, resp, job_id: str, model: str, reserved):
        chunks: list[bytes] = []
        try:
            async for chunk in resp.aiter_raw():
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
        self.spend.settle(job_id, model, reserved, usage[0], usage[1])

    @staticmethod
    def _read_usage(body: bytes) -> tuple[int, int] | None:
        """Pull (input_tokens, output_tokens) out of a reply.

        Non-streaming replies carry `usage` at the top level. Streaming
        replies send it across two events: message_start has the input
        count, and the final message_delta has the output count.
        """
        text = body.decode("utf-8", errors="replace")

        if not text.lstrip().startswith("event:") and "data:" not in text:
            try:
                usage = json.loads(text).get("usage") or {}
                return int(usage.get("input_tokens", 0)), int(usage.get("output_tokens", 0))
            except (ValueError, AttributeError, TypeError):
                return None

        inp = out = 0
        for line in text.splitlines():
            if not line.startswith("data:"):
                continue
            try:
                event = json.loads(line[5:].strip())
            except ValueError:
                continue
            if event.get("type") == "message_start":
                usage = event.get("message", {}).get("usage", {})
                inp = int(usage.get("input_tokens", 0))
            elif event.get("type") == "message_delta":
                out = int(event.get("usage", {}).get("output_tokens", out))
        return (inp, out) if (inp or out) else None

    async def aclose(self) -> None:
        await self.client.aclose()
