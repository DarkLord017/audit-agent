# The vyper worker: neutral base plus Vyper, Titanoboa and Slither.
FROM evmbench/base:latest

RUN pip install --no-cache-dir vyper titanoboa slither-analyzer

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
