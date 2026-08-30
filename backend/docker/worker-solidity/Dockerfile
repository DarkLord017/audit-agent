# The solidity worker: neutral base plus Foundry, Slither and solc.
FROM evmbench/base:latest

RUN FOUNDRY_DIR=/opt/foundry sh -c 'curl -L https://foundry.paradigm.xyz | bash' \
    && FOUNDRY_DIR=/opt/foundry /opt/foundry/bin/foundryup \
    && chmod -R a+rX /opt/foundry

# forge-std, vendored. The worker has no network, so `forge init` cannot
# clone it at run time -- it dies with "Could not resolve host: github.com".
RUN git clone --depth 1 https://github.com/foundry-rs/forge-std /opt/forge-std \
    && rm -rf /opt/forge-std/.git \
    && chmod -R a+rX /opt/forge-std

ENV VIRTUAL_ENV=/opt/solc
RUN pip install --no-cache-dir slither-analyzer solc-select \
    && solc-select install 0.8.28 \
    && solc-select use 0.8.28 \
    && chmod -R a+rX /opt/solc

RUN uv pip install --system --no-cache \
        pydantic pydantic-settings claude-agent-sdk

COPY backend/ ./backend/
COPY skills/ ./skills/

ENV PYTHONPATH=/opt/evmbench \
    SKILLS_DIR=/opt/evmbench/skills \
    FOUNDRY_DIR=/opt/foundry \
    FORGE_STD_DIR=/opt/forge-std \
    VIRTUAL_ENV=/opt/solc \
    SOLC_BIN=/opt/solc/.solc-select/artifacts/solc-0.8.28/solc-0.8.28 \
    PATH="/opt/foundry/bin:${PATH}" \
    UPLOAD_PATH=/input/upload.zip \
    WORK_DIR=/work \
    REPORT_PATH=/work/report.json

RUN useradd --uid 10001 --create-home auditor \
    && mkdir -p /work /input \
    && chown auditor:auditor /work

USER auditor
ENTRYPOINT ["python", "-m", "backend.worker_runner.main"]
