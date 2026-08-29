"""Swaps a real API key for a worthless token, and back again.

The worker container only ever holds the token. The real key lives here,
outside the container, and is attached to requests on their way out.
"""

import json
import os

from cryptography.fernet import Fernet, InvalidToken


class BadToken(Exception):
    """The token is forged, corrupted, or past its expiry."""


class TokenVault:
    # A token is only good for one job. Anything longer and a stolen
    # token outlives the container it came from.
    DEFAULT_TTL_SECONDS = 3 * 60 * 60   # 3 hours

    def __init__(self, secret: str | None = None, ttl_seconds: int | None = None):
        secret = secret or os.getenv("PROXY_SECRET_KEY")
        if not secret:
            raise RuntimeError("PROXY_SECRET_KEY is not set")
        self.fernet = Fernet(secret)
        self.ttl = ttl_seconds or self.DEFAULT_TTL_SECONDS

    @staticmethod
    def generate_secret() -> str:
        """Make a PROXY_SECRET_KEY. Run once, put the result in .env."""
        return Fernet.generate_key().decode()

    def issue(self, api_key: str, job_id: str) -> str:
        """Encrypt the real key plus its job id into one token.

        The job id rides along so the proxy knows whose budget to charge
        and whether that job is still allowed to spend.
        """
        payload = json.dumps({"k": api_key, "j": job_id})
        return self.fernet.encrypt(payload.encode()).decode()

    def redeem(self, token: str) -> tuple[str, str]:
        """Turn a token back into (real key, job id).

        Raises BadToken if it is forged, corrupted, or older than the TTL.
        """
        try:
            raw = self.fernet.decrypt(token.encode(), ttl=self.ttl)
        except InvalidToken as exc:
            raise BadToken("token is invalid or expired") from exc
        try:
            payload = json.loads(raw)
            return payload["k"], payload["j"]
        except (ValueError, KeyError, TypeError) as exc:
            raise BadToken("token payload is malformed") from exc
