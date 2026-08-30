"""Starts one throwaway container per job.

Everything here exists to make the box worth nothing to break into:
no privileges, no internet, a hard memory and CPU ceiling, and one
read-only file mounted in.
"""

import logging
import os
import shutil
from pathlib import Path

import requests
from docker.errors import NotFound

import docker

log = logging.getLogger(__name__)


class DockerWorkerBackend:
    # The worker sits on an internal network with no route to the
    # internet. The proxy is the only thing it can reach, which is what
    # makes the token scheme hold
    ISOLATED_NETWORK = "evmbench_isolated"
    EGRESS_NETWORK = "evmbench_egress"

    MEMORY = "1g"
    NANO_CPUS = int(1_000_000_000 * 0.5)   # half a core
    PIDS_LIMIT = 1024
    TIMEOUT_SECONDS = 3 * 60 * 60
    # Paths inside the container. Root is read-only, so /work is the
    # only writable place -- and it is a tmpfs, so it dies with the box.
    UPLOAD_MOUNT = "/input/upload.zip"
    WORK_DIR = "/work"
    HOME_DIR = "/home/auditor"

    OUT_MOUNT = "/out"
    REPORT_PATH = "/out/report.json"

    # Must match the user created in docker/worker/Dockerfile.
    UID = 10001
    GID = 10001
    
    PLATFORM = os.getenv("WORKER_PLATFORM", "linux/amd64")
    MAX_REPORT_BYTES = 5 * 1024 * 1024

    def __init__(
        self,
        image: str | None = None,
        client: docker.DockerClient | None = None,
        output_dir: str | None = None,
    ):
        self.client = client or docker.from_env()
        self.image = image or os.getenv("WORKER_IMAGE", "evmbench/worker:latest")
        self.output_dir = Path(output_dir or os.getenv("OUTPUT_DIR", "outputs")).resolve()
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def job_output_dir(self, job_id: str) -> Path:
        return self.output_dir / job_id

    # --- networks -----------------------------------------------------

    def ensure_networks(self) -> None:
        """Create both networks if they are missing.

        isolated: internal=True, so Docker installs no default route out.
                  Worker and proxy both sit here.
        egress:   a normal bridge. Only the proxy joins it, and that is
                  the single path to the internet.
        """
        for name, internal in ((self.ISOLATED_NETWORK, True), (self.EGRESS_NETWORK, False)):
            try:
                self.client.networks.get(name)
            except NotFound:
                self.client.networks.create(name, driver="bridge", internal=internal)
                log.info("created network %s (internal=%s)", name, internal)

    # --- workers ------------------------------------------------------

    def start_worker(
        self,
        job_id: str,
        upload_path: str,
        model: str,
        profile: str,
        proxy_token: str,
        image: str | None = None,
    ) -> str:
        """Launch the container for one job. Returns its id."""
        self.ensure_networks()

        out_dir = self.job_output_dir(job_id)
        out_dir.mkdir(parents=True, exist_ok=True)
        out_dir.chmod(0o770)
        os.chown(out_dir, self.UID, self.GID) if hasattr(os, "chown") else None

        # Each ecosystem ships its own image: solidity carries Foundry and
        # Slither, another would carry cargo. self.image is only a fallback.
        container = self.client.containers.run(
            image or self.image,
            detach=True,
            platform=self.PLATFORM,
            name=f"evmbench-worker-{job_id}",
            network=self.ISOLATED_NETWORK,          # no internet, only the proxy
            environment={
                "JOB_ID": job_id,
                "MODEL": model,
                "PROFILE": profile,
                # A worthless token, not the real key. See proxy/tokens.py.
                "ANTHROPIC_API_KEY": proxy_token,
                "ANTHROPIC_BASE_URL": "http://evmbench-proxy:8084",
                "UPLOAD_PATH": self.UPLOAD_MOUNT,
                "WORK_DIR": self.WORK_DIR,
                "REPORT_PATH": self.REPORT_PATH,
                "HOME": self.HOME_DIR,
            },
            volumes={
                # In: their zip, read-only.
                str(Path(upload_path).resolve()): {
                    "bind": self.UPLOAD_MOUNT,
                    "mode": "ro",
                },
                # Out: one empty directory, this job only. The single
                # place the container may write on our disk, emptied as
                # soon as we have read the report.
                str(out_dir): {
                    "bind": self.OUT_MOUNT,
                    "mode": "rw",
                },
            },
            # --- the cage ---
            cap_drop=["ALL"],                       # no Linux superpowers
            security_opt=["no-new-privileges"],     # cannot gain any later
            read_only=True,                         # root filesystem frozen
            # The workspace: skills copied in, their code unpacked, the
            # report written. All of it vanishes when the container goes.
            #
            # A tmpfs mounts OVER whatever the image had there, so the
            # Dockerfile's `chown auditor /work` is buried and the mount
            # lands root-owned 0755. Without uid/gid here the non-root
            # user cannot write and every job dies at CONFIG_ERROR.
            #
            # exec is needed too: Docker defaults tmpfs to noexec, and
            # node, npm and forge all run binaries out of temp dirs.
            tmpfs={
                self.WORK_DIR: f"size=1g,exec,mode=0770,uid={self.UID},gid={self.GID}",
                "/tmp": f"size=256m,exec,mode=1777,uid={self.UID},gid={self.GID}",
                # claude-code writes ~/.claude; the root filesystem is
                # read-only, so HOME needs its own writable mount.
                self.HOME_DIR: f"size=128m,exec,mode=0770,uid={self.UID},gid={self.GID}",
            },
            mem_limit=self.MEMORY,
            memswap_limit=self.MEMORY,              # equal, so no swap
            nano_cpus=self.NANO_CPUS,
            pids_limit=self.PIDS_LIMIT,
            restart_policy={"Name": "no"},          # dies once, stays dead
            labels={"io.evmbench.job_id": job_id},
        )
        log.info(
            "started worker %s for job %s on %s",
            container.short_id, job_id, image or self.image,
        )
        return container.id

    def wait(self, container_id: str, timeout: int) -> int:
        """Block until the container stops. Returns its exit code.

        Raises TimeoutError if it outlives `timeout` seconds -- the
        caller kills it and marks the job timed_out.
        """
        container = self.client.containers.get(container_id)
        try:
            result = container.wait(timeout=timeout)
        except requests.exceptions.ReadTimeout as exc:
            raise TimeoutError(f"container {container_id} ran past {timeout}s") from exc
        return int(result.get("StatusCode", 1))

    def logs(self, container_id: str, tail: int = 50) -> str:
        """Last few lines, for the error message on a failed job."""
        try:
            container = self.client.containers.get(container_id)
        except NotFound:
            return ""
        return container.logs(tail=tail).decode("utf-8", errors="replace")

    def read_report(self, job_id: str) -> str | None:
        """Read the report the worker wrote, from its output directory.

        The cap is applied while reading, not after. The container is
        untrusted and could write gigabytes; loading that into memory
        first would take down the instancer and every other job on it.
        """
        path = self.job_output_dir(job_id) / "report.json"
        try:
            if path.is_symlink() or not path.is_file():
                return None
            size = path.stat().st_size
            if size > self.MAX_REPORT_BYTES:
                log.warning("job %s wrote a %d byte report; refusing", job_id, size)
                return None
            with path.open("rb") as fh:
                # One byte past the cap, so a file that grows between
                # the stat and the read is still caught.
                body = fh.read(self.MAX_REPORT_BYTES + 1)
        except OSError:
            log.exception("could not read the report for job %s", job_id)
            return None

        if len(body) > self.MAX_REPORT_BYTES:
            log.warning("job %s report exceeded the cap while reading", job_id)
            return None
        return body.decode("utf-8", errors="replace")

    def clear_output(self, job_id: str) -> None:
        """Delete the job's output directory once the report is saved."""
        shutil.rmtree(self.job_output_dir(job_id), ignore_errors=True)

    def stop_worker(self, container_id: str) -> None:
        try:
            container = self.client.containers.get(container_id)
        except NotFound:
            return
        container.remove(force=True)

    def running_workers(self) -> int:
        return len(self.client.containers.list(filters={"label": "io.evmbench.job_id"}))
