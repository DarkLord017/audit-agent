# The Cairo worker: neutral base plus Scarb, snforge and vendored packages.
FROM evmbench/base:latest

ARG TARGETARCH
ENV SCARB_VERSION=2.20.1 \
    SNFORGE_VERSION=0.63.0 \
    USC_VERSION=2.10.0 \
    SCARB_CACHE=/opt/scarb-cache

# Scarb, Starknet Foundry and Universal Sierra Compiler. Runtime has no
# network, so compilers and the package cache have to land in the image.
RUN set -eux; \
    case "$TARGETARCH" in \
      amd64) ARCH=x86_64 ;; \
      arm64) ARCH=aarch64 ;; \
      *) echo "unsupported TARGETARCH=$TARGETARCH" >&2; exit 1 ;; \
    esac; \
    curl -fsSL "https://github.com/software-mansion/scarb/releases/download/v${SCARB_VERSION}/scarb-v${SCARB_VERSION}-${ARCH}-unknown-linux-gnu.tar.gz" \
      | tar -xz -C /tmp; \
    mkdir -p /opt/scarb; \
    mv /tmp/scarb-v${SCARB_VERSION}-${ARCH}-unknown-linux-gnu/* /opt/scarb/; \
    curl -fsSL "https://github.com/foundry-rs/starknet-foundry/releases/download/v${SNFORGE_VERSION}/starknet-foundry-v${SNFORGE_VERSION}-${ARCH}-unknown-linux-gnu.tar.gz" \
      | tar -xz -C /tmp; \
    mkdir -p /opt/snfoundry; \
    mv /tmp/starknet-foundry-v${SNFORGE_VERSION}-${ARCH}-unknown-linux-gnu/* /opt/snfoundry/; \
    curl -fsSL "https://github.com/software-mansion/universal-sierra-compiler/releases/download/v${USC_VERSION}/universal-sierra-compiler-v${USC_VERSION}-${ARCH}-unknown-linux-gnu.tar.gz" \
      | tar -xz -C /tmp; \
    mkdir -p /opt/usc; \
    mv /tmp/universal-sierra-compiler-v${USC_VERSION}-${ARCH}-unknown-linux-gnu/* /opt/usc/; \
    chmod -R a+rX /opt/scarb /opt/snfoundry /opt/usc

ENV PATH="/opt/scarb/bin:/opt/snfoundry/bin:/opt/usc/bin:${PATH}"

# OpenZeppelin Cairo contracts, vendored for path deps. snforge_std and
# other registry packages are fetched into SCARB_CACHE below.
RUN git clone --depth 1 --branch v4.0.1 \
        https://github.com/OpenZeppelin/cairo-contracts \
        /opt/cairo-contracts \
    && rm -rf /opt/cairo-contracts/.git \
    && chmod -R a+rX /opt/cairo-contracts

# Warm the Scarb cache so `scarb --offline` works. snforge new writes a
# Scarb.toml that matches this snforge version, including prebuilt plugins.
RUN mkdir -p /opt/scarb-cache /tmp/cairo-vendor \
    && snforge new /tmp/cairo-vendor --name vendor --no-vcs \
    && cd /tmp/cairo-vendor \
    && scarb fetch \
    && (cd /opt/cairo-contracts && scarb fetch) \
    && chmod -R a+rX /opt/scarb-cache \
    && rm -rf /tmp/cairo-vendor

# Caracal is not installed: last prebuilt (v0.2.3) targets Cairo <= 2.5.0.

RUN uv pip install --system --no-cache \
        pydantic pydantic-settings claude-agent-sdk

COPY backend/ ./backend/
COPY skills/ ./skills/

ENV PYTHONPATH=/opt/evmbench \
    SKILLS_DIR=/opt/evmbench/skills \
    SCARB_CACHE=/opt/scarb-cache \
    PATH="/opt/scarb/bin:/opt/snfoundry/bin:/opt/usc/bin:${PATH}" \
    UPLOAD_PATH=/input/upload.zip \
    WORK_DIR=/work \
    REPORT_PATH=/work/report.json

RUN useradd --uid 10001 --create-home auditor \
    && mkdir -p /work /input \
    && chown auditor:auditor /work

USER auditor
ENTRYPOINT ["python", "-m", "backend.worker_runner.main"]
