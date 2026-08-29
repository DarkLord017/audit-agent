# The worker: what runs inside the locked box, one per job.
# Build context is the repository root.
FROM evmbench/base:latest

WORKDIR /opt/evmbench

RUN uv pip install --system --no-cache \
        pydantic pydantic-settings claude-agent-sdk

COPY backend/ ./backend/
COPY skills/ ./skills/

ENV PYTHONPATH=/opt/evmbench \
    SKILLS_DIR=/opt/evmbench/skills \
    UPLOAD_PATH=/input/upload.zip \
    WORK_DIR=/work \
    REPORT_PATH=/work/report.json

RUN useradd --uid 10001 --create-home auditor \
    && mkdir -p /work /input \
    && chown auditor:auditor /work

USER auditor
ENTRYPOINT ["python", "-m", "backend.worker_runner.main"]
