"""Job business logic. Routes stay thin; the real work lives here."""

import logging
import os
import uuid
import zipfile
from datetime import UTC, datetime
from pathlib import Path

from backend.broker.messages import JobMessage
from backend.broker.publisher import JobPublisher
from backend.database.db import DatabaseOperations, Job
from backend.proxy.tokens import TokenVault
from backend.utils.models import MODELS
from backend.utils.utils import JobStatus
from backend.worker_runner.profiles import registry

log = logging.getLogger(__name__)


class JobService:
    MAX_UPLOAD_BYTES = 25 * 1024 * 1024   # 25 MB

    def __init__(
        self,
        db_ops: DatabaseOperations | None = None,
        upload_dir: str | None = None,
        vault: TokenVault | None = None,
        publisher: JobPublisher | None = None,
    ):
        self.db_ops = db_ops or DatabaseOperations()
        self.upload_dir = Path(upload_dir or os.getenv("UPLOAD_DIR", "uploads"))
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        self.vault = vault or TokenVault()
        self.publisher = publisher or JobPublisher()
        
        self.api_key = os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise RuntimeError("ANTHROPIC_API_KEY is not set")

    def check_model(self, model: str) -> None:
        # One list, in backend.utils.models, so a model can never be
        # runnable here but unpriced in the proxy.
        if model not in MODELS:
            raise ValueError(f"unknown model: {model}")

    def check_profile(self, profile: str) -> None:
        if profile not in registry.keys():
            raise ValueError(f"unknown profile: {profile}")

    # --- upload -----------------------------------------------------

    async def save_upload(self, file, job_id: uuid.UUID) -> Path:
        """Stream the upload to disk in chunks, then prove it is a zip.

        Chunked so a huge upload cannot eat all our memory. Deletes the
        partial file if anything goes wrong.
        """
        dest = self.upload_dir / f"{job_id}.zip"
        written = 0
        try:
            with dest.open("wb") as out:
                while chunk := await file.read(1024 * 1024):
                    written += len(chunk)
                    if written > self.MAX_UPLOAD_BYTES:
                        raise ValueError("upload too large")
                    out.write(chunk)
            if not zipfile.is_zipfile(dest):
                raise ValueError("file is not a zip archive")
        except Exception:
            dest.unlink(missing_ok=True)
            raise
        return dest

    # --- job lifecycle ----------------------------------------------

    async def start_job(self, file, model: str, profile: str = "solidity") -> Job:
        self.check_model(model)
        self.check_profile(profile)

        # The server picks the id. Never let the client choose it.
        job_id = uuid.uuid4()
        dest = await self.save_upload(file, job_id)

        job = Job(
            id=str(job_id),
            status=JobStatus.QUEUED,
            model=model,
            upload_path=str(dest),
            container_id=None,
            created_at=datetime.now(UTC).isoformat(),
            started_at=None,
            finished_at=None,
            error=None,
            report=None,
        )
        self.db_ops.create_job(job)
        self.launch(job, profile)
        return job

    def launch(self, job: Job, profile: str) -> None:
        """Mint a token for this job and put it on the queue.

        No container is started here. The API answers in milliseconds
        and the instancer picks the job up when it has a free slot.

        The token is worthless outside our proxy and dies with the job,
        so the real key never enters the container.
        """
        message = JobMessage(
            job_id=job.id,
            model=job.model,
            profile=profile,
            upload_path=job.upload_path,
            proxy_token=self.vault.issue(self.api_key, job.id),
        )
        try:
            self.publisher.publish(message)
        except Exception as exc:
            log.exception("could not queue job %s", job.id)
            self.db_ops.job_failed(job.id, f"could not queue job: {exc}")
            raise

    def get_job(self, job_id: uuid.UUID) -> Job | None:
        return self.db_ops.get_job(str(job_id))

    def get_history(self, limit: int = 50, offset: int = 0) -> list[Job]:
        return self.db_ops.get_job_history(limit=limit, offset=offset)
