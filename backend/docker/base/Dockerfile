# Base image: the tools an auditor needs, plus the Claude Code runtime.
# Built once and shared, because Foundry and the Node install are slow.
#
# Layer order matters. Docker caches each step, but a cached step is only
# reused if everything above it is unchanged. So the slow, never-changing
# installs go first, and cheap settings go last -- otherwise editing one
# ENV line rebuilds the whole image.
FROM python:3.12-slim-bookworm

ENV DEBIAN_FRONTEND=noninteractive

# --- slow layers, top to bottom by how rarely they change --------------

RUN apt-get update && apt-get install -y --no-install-recommends \
        ca-certificates curl git unzip xz-utils \
    && rm -rf /var/lib/apt/lists/*

# Node, because the Claude Agent SDK drives the Claude Code CLI.
RUN curl -fsSL https://deb.nodesource.com/setup_22.x | bash - \
    && apt-get install -y --no-install-recommends nodejs \
    && rm -rf /var/lib/apt/lists/*

RUN npm install -g @anthropic-ai/claude-code && npm cache clean --force

RUN FOUNDRY_DIR=/opt/foundry sh -c 'curl -L https://foundry.paradigm.xyz | bash' \
    && FOUNDRY_DIR=/opt/foundry /opt/foundry/bin/foundryup \
    && chmod -R a+rX /opt/foundry

# forge-std, vendored. The worker has no network, so `forge init` cannot
# clone it at run time -- it dies with "Could not resolve host: github.com".
# Baking it in is what lets the breaker scaffold a PoC project offline.
RUN git clone --depth 1 https://github.com/foundry-rs/forge-std /opt/forge-std \
    && rm -rf /opt/forge-std/.git \
    && chmod -R a+rX /opt/forge-std

ENV VIRTUAL_ENV=/opt/solc
RUN pip install --no-cache-dir slither-analyzer solc-select \
    && solc-select install 0.8.28 \
    && solc-select use 0.8.28 \
    && chmod -R a+rX /opt/solc

RUN pip install --no-cache-dir uv

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    FOUNDRY_DIR=/opt/foundry \
    FORGE_STD_DIR=/opt/forge-std \
    VIRTUAL_ENV=/opt/solc \
    SOLC_BIN=/opt/solc/.solc-select/artifacts/solc-0.8.28/solc-0.8.28 \
    PATH="/opt/foundry/bin:${PATH}"

WORKDIR /opt/evmbench
