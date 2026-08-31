# The solana worker: neutral base plus rustc/cargo and a LiteSVM crate cache.
FROM evmbench/base:latest

# Host toolchain for `cargo test`. SBF/cargo-build-sbf is not installed;
# LiteSVM tests that need a .so must load one from the upload or mark
# UNVERIFIED. Missing crates at runtime also mean UNVERIFIED — there is
# no network to fetch them.
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential pkg-config libssl-dev \
    && rm -rf /var/lib/apt/lists/*

ENV RUSTUP_HOME=/opt/rustup \
    CARGO_HOME=/opt/cargo \
    PATH="/opt/cargo/bin:${PATH}"

RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs \
        | sh -s -- -y --default-toolchain stable --profile minimal \
    && chmod -R a+rX /opt/rustup /opt/cargo

# Populate CARGO_HOME with LiteSVM-capable graphs so `cargo test --offline`
# works for common Solana 1.18 and 2.2 programs. Additional lockfile
# versions are not fetched at runtime: breaker marks those UNVERIFIED.
WORKDIR /tmp/solana-vendor
RUN set -eux; \
    fetch_graph() { \
      d=$(mktemp -d); \
      cargo init --name solana_vendor_tmp --lib "$d"; \
      printf '%s\n' "$@" >> "$d/Cargo.toml"; \
      (cd "$d" && cargo fetch); \
      rm -rf "$d"; \
    }; \
    fetch_graph \
      '[dev-dependencies]' \
      'litesvm = "0.6"' \
      'solana-sdk = "2.2"' \
      'solana-program = "2.2"'; \
    fetch_graph \
      '[dev-dependencies]' \
      'solana-program-test = "2.2"' \
      'solana-sdk = "2.2"' \
      'solana-program = "2.2"'; \
    fetch_graph \
      '[dev-dependencies]' \
      'solana-program = "1.18"' \
      'solana-sdk = "1.18"' \
      'solana-program-test = "1.18"'; \
    fetch_graph \
      '[dependencies]' \
      'spl-token = "4"' \
      'spl-associated-token-account = "3"'; \
    rm -rf /tmp/solana-vendor /tmp/tmp.* /tmp/solana_vendor_tmp* \
    && chmod -R a+rwX /opt/cargo \
    && chmod -R a+rX /opt/rustup

WORKDIR /opt/evmbench

RUN uv pip install --system --no-cache \
        pydantic pydantic-settings claude-agent-sdk

COPY backend/ ./backend/
COPY skills/ ./skills/

ENV PYTHONPATH=/opt/evmbench \
    SKILLS_DIR=/opt/evmbench/skills \
    RUSTUP_HOME=/opt/rustup \
    CARGO_HOME=/opt/cargo \
    CARGO_NET_OFFLINE=true \
    CARGO_INCREMENTAL=0 \
    CARGO_PROFILE_DEV_DEBUG=0 \
    PATH="/opt/cargo/bin:${PATH}" \
    UPLOAD_PATH=/input/upload.zip \
    WORK_DIR=/work \
    REPORT_PATH=/work/report.json

RUN useradd --uid 10001 --create-home auditor \
    && mkdir -p /work /input \
    && chown auditor:auditor /work

USER auditor
ENTRYPOINT ["python", "-m", "backend.worker_runner.main"]
