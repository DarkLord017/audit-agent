"""The instancer: takes jobs off the queue and runs them.

Concurrency lives in two places that have to agree.

prefetch_count caps how many messages RabbitMQ will hand us at once.
A thread pool of the same size actually runs them. Both are needed: the
prefetch alone does nothing if one thread handles messages serially,
which also starves pika's heartbeats and gets the connection dropped
mid-job.

So on_message does no work. It hands the job to the pool and returns
immediately, leaving the connection thread free to answer heartbeats.
The ack goes back through add_callback_threadsafe, because a pika
channel may only be touched from the connection thread.
"""

import json
import logging
import os
import signal
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pika

from backend.broker.connection import QUEUE_NAME, connect, declare_queue
from backend.broker.messages import JobMessage
from backend.database.db import DatabaseOperations
from backend.instancer.docker_backend import DockerWorkerBackend
from backend.utils.utils import JobStatus, Report
from backend.worker_runner.profiles import registry

log = logging.getLogger(__name__)


class Instancer:
    def __init__(
        self,
        db_ops: DatabaseOperations | None = None,
        backend: DockerWorkerBackend | None = None,
        concurrency: int | None = None,
        timeout_seconds: int | None = None,
    ):
        self.db_ops = db_ops or DatabaseOperations()
        self.backend = backend or DockerWorkerBackend()
        self.concurrency = concurrency or int(os.getenv("INSTANCER_CONCURRENCY", "3"))
        self.timeout = timeout_seconds or int(os.getenv("JOB_TIMEOUT_SECONDS", str(3 * 60 * 60)))
        self._stopping = threading.Event()
        self._connection: pika.BlockingConnection | None = None
        self._channel: pika.adapters.blocking_connection.BlockingChannel | None = None
        self._pool: ThreadPoolExecutor | None = None

    # --- the loop -----------------------------------------------------

    def run(self) -> None:
        self._connection = connect()
        channel = self._channel = self._connection.channel()
        declare_queue(channel)

        channel.basic_qos(prefetch_count=self.concurrency)
        channel.basic_consume(queue=QUEUE_NAME, on_message_callback=self.on_message)

        # Only the main thread may install signal handlers. Running the
        # instancer from a worker thread (tests, embedding) is fine, it
        # just does not get graceful shutdown.
        try:
            for sig in (signal.SIGINT, signal.SIGTERM):
                signal.signal(sig, lambda *_: self.stop(channel))
        except ValueError:
            log.debug("not on the main thread; no signal handlers")

        self._pool = ThreadPoolExecutor(max_workers=self.concurrency, thread_name_prefix="job")
        log.info("instancer up, %d at a time", self.concurrency)
        try:
            channel.start_consuming()
        finally:
            # Let in-flight jobs finish and ack before the socket closes.
            self._pool.shutdown(wait=True)
            if self._connection.is_open:
                self._connection.close()

    def stop(self, channel) -> None:
        log.info("shutting down, waiting for running jobs")
        self._stopping.set()
        channel.stop_consuming()

    # --- connection thread: hand off and return ------------------------

    def on_message(self, channel, method, properties, body) -> None:
        """Runs on the connection thread. Must not block.

        Anything slow here stops heartbeats, and RabbitMQ closes the
        connection roughly two missed heartbeats later -- which for a
        three-hour audit is a guaranteed failure.
        """
        try:
            message = JobMessage.from_bytes(body)
        except (ValueError, KeyError, TypeError):
            log.exception("unreadable message, dropping it")
            # Malformed: never requeue, or it loops forever.
            channel.basic_nack(method.delivery_tag, requeue=False)
            return

        self._pool.submit(self._run_job, message, method.delivery_tag)

    def _ack_later(self, delivery_tag: int) -> None:
        """Ask the connection thread to ack.

        A pika channel may only be touched from the thread that owns the
        connection. add_callback_threadsafe is the supported way to send
        it an instruction from a worker thread.
        """
        connection, channel = self._connection, self._channel
        if connection is None or connection.is_closed:
            log.warning("connection gone before ack of %s; it will be redelivered", delivery_tag)
            return

        def ack():
            try:
                if channel is not None and channel.is_open:
                    channel.basic_ack(delivery_tag)
            except Exception:
                log.exception("could not ack %s; it will be redelivered", delivery_tag)

        try:
            connection.add_callback_threadsafe(ack)
        except Exception:
            log.exception("could not schedule ack of %s", delivery_tag)

    # --- worker threads: the slow part ---------------------------------

    def _run_job(self, message: JobMessage, delivery_tag: int) -> None:
        try:
            self.handle(message)
        except Exception:
            log.exception("job %s blew up", message.job_id)
            try:
                self.db_ops.job_failed(message.job_id, "instancer error")
            except Exception:
                log.exception("could not even record the failure for %s", message.job_id)
        finally:
            # Ack last, whatever happened. Until this runs the job still
            # belongs to us as far as RabbitMQ is concerned.
            self._ack_later(delivery_tag)

    def handle(self, message: JobMessage) -> None:
        # A redelivered message can arrive for a job that already ran --
        # if we died after starting a container but before acking. So
        # check first: this handler has to be safe to run twice.
        job = self.db_ops.get_job(message.job_id)
        if job is None:
            log.warning("job %s is not in the database, skipping", message.job_id)
            return
        if job.status != JobStatus.QUEUED:
            log.info("job %s is already %s, skipping", message.job_id, job.status)
            return

        # Everything but the token comes from the row, not the message.
        # A message is a nudge saying "go look"; the database is the
        # truth. Trusting message.upload_path would let anyone who can
        # publish to the queue mount any host path into the container.
        # The image comes from the registry too, keyed by profile. A queue
        # publisher does not get to choose which image we run.
        try:
            image = registry.get(message.profile).toolchain.image
        except KeyError:
            log.error("job %s names unknown profile %s", job.id, message.profile)
            self.db_ops.job_failed(job.id, f"unknown profile: {message.profile}")
            return

        container_id = self.backend.start_worker(
            job_id=job.id,
            upload_path=job.upload_path,
            model=job.model,
            profile=message.profile,
            proxy_token=message.proxy_token,
            image=image,
        )
        self.db_ops.job_started(job.id, container_id)

        try:
            self.wait_for(job.id, container_id)
        finally:
            # The job is over one way or another. Their zip is untrusted
            # and we are done with it, so it does not sit on our disk.
            self.discard_upload(job.upload_path)

    @staticmethod
    def discard_upload(upload_path: str) -> None:
        try:
            Path(upload_path).unlink(missing_ok=True)
        except OSError:
            log.warning("could not delete upload %s", upload_path)

    def wait_for(self, job_id: str, container_id: str) -> None:
        """Block until the container stops, then record what happened.

        Runs on a pool thread, so blocking here is fine.
        """
        try:
            exit_code = self.backend.wait(container_id, timeout=self.timeout)
        except TimeoutError:
            log.warning("job %s ran past %ds, killing it", job_id, self.timeout)
            self.db_ops.job_timed_out(job_id)
            self.backend.stop_worker(container_id)
            return

        if exit_code != 0:
            logs = self.backend.logs(container_id, tail=50)
            self.db_ops.job_failed(job_id, f"worker exited {exit_code}: {logs}")
            self.backend.stop_worker(container_id)
            return

        self.save_report(job_id, container_id)
        self.backend.stop_worker(container_id)

    def save_report(self, job_id: str, container_id: str) -> None:
        try:
            raw = self.backend.read_report(job_id)
        finally:
            # The output directory is the only place the container could
            # write on our disk. Empty it either way.
            self.backend.clear_output(job_id)
        if raw is None:
            self.db_ops.job_failed(job_id, "worker exited cleanly but wrote no report")
            return
        try:
            # The agent read untrusted code, so its output is untrusted
            # too. Validate before it goes anywhere near the database.
            report = Report.model_validate(json.loads(raw))
        except Exception as exc:
            self.db_ops.job_failed(job_id, f"report failed validation: {exc}")
            return
        self.db_ops.job_succeeded(job_id, report)
        log.info("job %s done, %d findings", job_id, len(report.vulnerabilities))


def main() -> None:
    logging.basicConfig(
        level=os.getenv("LOG_LEVEL", "INFO"),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    Instancer().run()


if __name__ == "__main__":
    main()
