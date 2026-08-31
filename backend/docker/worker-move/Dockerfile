# The Move / Sui worker: neutral base plus the Sui CLI and a vendored
# Move stdlib + sui-framework. The worker has no network at runtime, so
# `sui move test` cannot fetch git deps -- they have to be in the image.
FROM evmbench/base:latest

# libssl3: the official ubuntu `sui` binary is dynamically linked.
RUN apt-get update && apt-get install -y --no-install-recommends \
        libssl3 \
    && rm -rf /var/lib/apt/lists/*

ARG SUI_VERSION=mainnet-v1.78.1

# CLI only. The release tarball also ships sui-node / faucet / etc.; we
# keep the `sui` binary so the layer stays smaller than the full archive.
RUN set -eux; \
    arch="$(dpkg --print-architecture)"; \
    case "$arch" in \
      amd64) sui_arch=ubuntu-x86_64 ;; \
      arm64) sui_arch=ubuntu-aarch64 ;; \
      *) echo "unsupported architecture: $arch" >&2; exit 1 ;; \
    esac; \
    curl -fsSL \
      "https://github.com/MystenLabs/sui/releases/download/${SUI_VERSION}/sui-${SUI_VERSION}-${sui_arch}.tgz" \
      -o /tmp/sui.tgz; \
    mkdir -p /tmp/sui-extract /opt/sui/bin; \
    tar -xzf /tmp/sui.tgz -C /tmp/sui-extract; \
    sui_bin="$(find /tmp/sui-extract -type f -name sui -print -quit)"; \
    test -n "$sui_bin"; \
    mv "$sui_bin" /opt/sui/bin/sui; \
    chmod a+rx /opt/sui/bin/sui; \
    rm -rf /tmp/sui.tgz /tmp/sui-extract

# Move stdlib + Sui framework, same tag as the CLI. `sui move test`
# --skip-fetch-latest-git-deps uses these via a local path in Move.toml.
RUN git clone --depth 1 --filter=blob:none --sparse \
        --branch "${SUI_VERSION}" \
        https://github.com/MystenLabs/sui.git /tmp/sui-src \
    && git -C /tmp/sui-src sparse-checkout set crates/sui-framework/packages \
    && mkdir -p /opt/sui-framework \
    && cp -a /tmp/sui-src/crates/sui-framework/packages /opt/sui-framework/ \
    && rm -rf /tmp/sui-src \
    && chmod -R a+rX /opt/sui-framework

RUN uv pip install --system --no-cache \
        pydantic pydantic-settings claude-agent-sdk

COPY backend/ ./backend/
COPY skills/ ./skills/

ENV PYTHONPATH=/opt/evmbench \
    SKILLS_DIR=/opt/evmbench/skills \
    SUI_FRAMEWORK_DIR=/opt/sui-framework/packages/sui-framework \
    PATH="/opt/sui/bin:${PATH}" \
    UPLOAD_PATH=/input/upload.zip \
    WORK_DIR=/work \
    REPORT_PATH=/work/report.json

RUN useradd --uid 10001 --create-home auditor \
    && mkdir -p /work /input \
    && chown auditor:auditor /work

USER auditor
ENTRYPOINT ["python", "-m", "backend.worker_runner.main"]
