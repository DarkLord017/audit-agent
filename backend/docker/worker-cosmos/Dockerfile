# The cosmos worker: neutral base plus Go, Rust, and vendored
# cosmos-sdk / cosmwasm-std caches. The worker has no network at
# runtime, so anything go/cargo would fetch is baked in at build.
FROM evmbench/base:latest

ARG TARGETARCH

RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential pkg-config libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# --- Go ---------------------------------------------------------------

ENV GOLANG_VERSION=1.23.8 \
    GOPATH=/opt/go \
    GOMODCACHE=/opt/go/pkg/mod \
    GOCACHE=/opt/go-cache \
    GOPROXY=https://proxy.golang.org,direct \
    GOTOOLCHAIN=local

RUN arch="$(echo "${TARGETARCH:-amd64}" | sed 's/arm64/arm64/;s/amd64/amd64/')" \
    && curl -fsSL "https://go.dev/dl/go${GOLANG_VERSION}.linux-${arch}.tar.gz" \
        | tar -C /usr/local -xz \
    && mkdir -p "${GOPATH}" "${GOMODCACHE}" "${GOCACHE}"

ENV PATH="/usr/local/go/bin:${PATH}"

# Populate the module cache with the SDK / IBC graphs the breaker is
# likely to need. Both versions stay in GOMODCACHE even though go.mod
# can only require one at a time.
RUN go mod download github.com/cosmos/cosmos-sdk@v0.50.13 \
    && go mod download github.com/cosmos/cosmos-sdk@v0.53.4 \
    && go mod download github.com/cosmos/ibc-go/v8@v8.7.0 \
    && go mod download github.com/cosmos/ibc-go/v10@v10.1.1 \
    && go mod download cosmossdk.io/math@v1.5.3 \
    && go mod download cosmossdk.io/core@v0.11.3 \
    && go mod download github.com/cometbft/cometbft@v0.38.17 \
    && go mod download github.com/stretchr/testify@v1.10.0 \
    && chmod -R a+rX /opt/go /usr/local/go \
    && rm -rf /opt/go-cache/*

# --- Rust + CosmWasm crate cache -------------------------------------

ENV RUSTUP_HOME=/opt/rustup \
    CARGO_HOME=/opt/cargo \
    RUSTUP_TOOLCHAIN=1.81.0

RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs \
        | sh -s -- -y --default-toolchain "${RUSTUP_TOOLCHAIN}" --profile minimal \
    && chmod -R a+rX /opt/rustup

ENV PATH="/opt/cargo/bin:${PATH}"

# Two tiny crates so cargo fetch pulls 1.x and 2.x of cosmwasm-std plus
# the usual test helpers. Runtime uses --offline against this cache.
WORKDIR /tmp/cw-cache

RUN mkdir -p v1/src v2/src \
    && printf '%s\n' \
        '[package]' \
        'name = "cw-cache-v1"' \
        'version = "0.0.0"' \
        'edition = "2021"' \
        '' \
        '[dependencies]' \
        'cosmwasm-std = { version = "=1.5.11", features = ["staking", "stargate"] }' \
        'cosmwasm-schema = "=1.5.11"' \
        'cw-storage-plus = "=1.2.0"' \
        'cw-multi-test = "=0.20.1"' \
        'cw2 = "=1.1.2"' \
        'cw20 = "=1.1.2"' \
        'sha2 = "0.10"' \
        'serde = { version = "1", features = ["derive"] }' \
        'thiserror = "1"' \
        > v1/Cargo.toml \
    && printf '%s\n' \
        '[package]' \
        'name = "cw-cache-v2"' \
        'version = "0.0.0"' \
        'edition = "2021"' \
        '' \
        '[dependencies]' \
        'cosmwasm-std = { version = "=2.2.2", features = ["std", "staking", "stargate"] }' \
        'cosmwasm-schema = "=2.2.2"' \
        'cw-storage-plus = "=2.0.0"' \
        'cw-multi-test = "=2.3.3"' \
        'cw2 = "=2.0.0"' \
        'cw20 = "=2.0.0"' \
        'sha2 = "0.10"' \
        'serde = { version = "1", features = ["derive"] }' \
        'thiserror = "1"' \
        > v2/Cargo.toml \
    && : > v1/src/lib.rs && : > v2/src/lib.rs \
    && cargo fetch --manifest-path v1/Cargo.toml \
    && cargo fetch --manifest-path v2/Cargo.toml \
    && chmod -R a+rwX /opt/cargo \
    && rm -rf /tmp/cw-cache

WORKDIR /opt/evmbench

# Runtime: no network. These override the build-time proxies.
ENV GOPROXY=off \
    GOSUMDB=off \
    CGO_ENABLED=1 \
    CARGO_NET_OFFLINE=true \
    CARGO_TARGET_DIR=/tmp/target \
    CARGO_INCREMENTAL=0 \
    CARGO_PROFILE_DEV_DEBUG=0 \
    GOCACHE=/tmp/gocache

RUN uv pip install --system --no-cache \
        pydantic pydantic-settings claude-agent-sdk

COPY backend/ ./backend/
COPY skills/ ./skills/

ENV PYTHONPATH=/opt/evmbench \
    SKILLS_DIR=/opt/evmbench/skills \
    PATH="/opt/cargo/bin:/usr/local/go/bin:${PATH}" \
    RUSTUP_HOME=/opt/rustup \
    CARGO_HOME=/opt/cargo \
    GOPATH=/opt/go \
    GOMODCACHE=/opt/go/pkg/mod \
    UPLOAD_PATH=/input/upload.zip \
    WORK_DIR=/work \
    REPORT_PATH=/work/report.json

RUN useradd --uid 10001 --create-home auditor \
    && mkdir -p /work /input /tmp/target /tmp/gocache \
    && chown auditor:auditor /work /tmp/target /tmp/gocache

USER auditor
ENTRYPOINT ["python", "-m", "backend.worker_runner.main"]
