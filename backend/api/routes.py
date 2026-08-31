"""HTTP routes, grouped in a class."""

import hmac
import logging
import os
import uuid

import psycopg
from fastapi import APIRouter, Depends, Form, HTTPException, Query, Request, UploadFile

from backend.api.service import JobService
from backend.utils.utils import JobHistoryResponse, JobResponse

log = logging.getLogger(__name__)


class JobsAPI:
    """Owns an APIRouter and binds its own methods as endpoints.

    Registration order matters: /history must be added BEFORE /{job_id},
    or FastAPI matches "history" as a job id.
    """

    def __init__(self, service: JobService | None = None):
        token = os.getenv("API_AUTH_TOKEN")
        if not token:
            raise RuntimeError("API_AUTH_TOKEN is not set")
        self.token = token
        self.service = service or JobService()
        self.router = APIRouter(
            prefix="/v1/jobs",
            tags=["jobs"],
            dependencies=[Depends(self._require_auth)],
        )

        self.router.add_api_route(
            "/history", self.history, methods=["GET"], response_model=JobHistoryResponse
        )
        self.router.add_api_route("/start", self.start, methods=["POST"], status_code=201)
        self.router.add_api_route(
            "/{job_id}", self.get, methods=["GET"], response_model=JobResponse
        )

    def _require_auth(self, request: Request) -> None:
        """Reject anyone who does not present API_AUTH_TOKEN.

        The API is published on :1337. Without this, anyone who can reach
        the port can start jobs (and spend the Anthropic key) or read
        reports. Health stays on a different router and is not gated.
        """
        provided = (request.headers.get("x-api-key") or "").strip()
        if not provided:
            header = request.headers.get("authorization") or ""
            if header.startswith("Bearer "):
                provided = header.removeprefix("Bearer ").strip()
        if not provided or not hmac.compare_digest(
            provided.encode("utf-8"), self.token.encode("utf-8")
        ):
            raise HTTPException(status_code=401, detail="unauthorized")

    def history(
        self,
        limit: int = Query(50, ge=1, le=200),
        offset: int = Query(0, ge=0),
    ):
        try:
            jobs = self.service.get_history(limit=limit, offset=offset)
        except psycopg.Error:
            log.exception("history query failed")
            raise HTTPException(status_code=503, detail="database unavailable") from None
        # An empty list is a valid answer, not an error.
        public = [JobResponse.from_job(job) for job in jobs]
        return {"jobs": public, "limit": limit, "offset": offset, "count": len(public)}

    def get(self, job_id: uuid.UUID):
        try:
            job = self.service.get_job(job_id)
        except psycopg.Error:
            log.exception("job lookup failed for %s", job_id)
            raise HTTPException(status_code=503, detail="database unavailable") from None

        if job is None:
            raise HTTPException(status_code=404, detail=f"no job with id {job_id}")
        return JobResponse.from_job(job)

    async def start(
        self,
        file: UploadFile,
        model: str = Form(...),
        profile: str = Form("solidity"),
    ):
        try:
            job = await self.service.start_job(file, model, profile)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except psycopg.Error:
            log.exception("could not create job")
            raise HTTPException(status_code=503, detail="database unavailable") from None
        return {"job_id": job.id, "status": job.status.value}


class HealthAPI:
    def __init__(self):
        self.router = APIRouter(tags=["health"])
        self.router.add_api_route("/health", self.health, methods=["GET"])

    def health(self):
        return {"status": "ok"}
