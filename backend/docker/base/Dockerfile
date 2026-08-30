# Neutral base: the Claude Code runtime and nothing ecosystem-specific.
# Solidity tools live in worker-solidity; another ecosystem adds its own
# image beside it rather than growing this one.
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

RUN pip install --no-cache-dir uv

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /opt/evmbench
