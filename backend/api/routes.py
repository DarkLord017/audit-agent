"""HTTP routes, grouped in a class."""

import logging
import uuid

import psycopg
from fastapi import APIRouter, Form, HTTPException, Query, UploadFile

from backend.api.service import JobService
from backend.utils.utils import JobHistoryResponse, JobResponse

log = logging.getLogger(__name__)


class JobsAPI:
    """Owns an APIRouter and binds its own methods as endpoints.

    Registration order matters: /history must be added BEFORE /{job_id},
    or FastAPI matches "history" as a job id.
    """

    def __init__(self, service: JobService | None = None):
        self.service = service or JobService()
        self.router = APIRouter(prefix="/v1/jobs", tags=["jobs"])

        self.router.add_api_route(
            "/history", self.history, methods=["GET"], response_model=JobHistoryResponse
        )
        self.router.add_api_route("/start", self.start, methods=["POST"], status_code=201)
        self.router.add_api_route(
            "/{job_id}", self.get, methods=["GET"], response_model=JobResponse
        )

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
