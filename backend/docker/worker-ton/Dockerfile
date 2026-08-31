# The TON worker: FunC + Tact compilers and a vendored @ton/sandbox tree.
# The worker has no network at runtime, so npm installs happen here at build.
FROM evmbench/base:latest

# Base image already has Node (Claude Code). Vendor compilers, sandbox, and
# a node_modules cache Blueprint/Jest PoCs can resolve without npm install.
WORKDIR /opt/ton-sandbox
RUN npm init -y \
    && npm install --no-fund --no-audit \
        @ton/sandbox \
        @ton/core \
        @ton/crypto \
        @ton/blueprint \
        @ton/test-utils \
        @ton/ton \
        @ton-community/func-js \
        @tact-lang/compiler \
        typescript \
        jest \
        ts-jest \
        @types/jest \
        @types/node \
    && npm cache clean --force \
    && chmod -R a+rX /opt/ton-sandbox

# FunC stdlib. Blueprint templates `#include "stdlib.fc"`; compileFunc
# resolvers map that name here. Tact ships its own stdlib inside the compiler.
RUN mkdir -p /opt/func-stdlib \
    && curl -fsSL -o /opt/func-stdlib/stdlib.fc \
        https://raw.githubusercontent.com/ton-blockchain/ton/master/crypto/smartcont/stdlib.fc \
    && chmod -R a+rX /opt/func-stdlib

# `func` is the FunC compiler the briefing names; Blueprint uses func-js WASM.
RUN ln -sf /opt/ton-sandbox/node_modules/.bin/func-js /usr/local/bin/func-js \
    && ln -sf /opt/ton-sandbox/node_modules/.bin/func-js /usr/local/bin/func \
    && ln -sf /opt/ton-sandbox/node_modules/.bin/tact /usr/local/bin/tact \
    && ln -sf /opt/ton-sandbox/node_modules/.bin/blueprint /usr/local/bin/blueprint \
    && ln -sf /opt/ton-sandbox/node_modules/.bin/jest /usr/local/bin/jest

WORKDIR /opt/evmbench

RUN uv pip install --system --no-cache \
        pydantic pydantic-settings claude-agent-sdk

COPY backend/ ./backend/
COPY skills/ ./skills/

ENV PYTHONPATH=/opt/evmbench \
    SKILLS_DIR=/opt/evmbench/skills \
    TON_SANDBOX_DIR=/opt/ton-sandbox \
    NODE_PATH=/opt/ton-sandbox/node_modules \
    FUNC_STDLIB=/opt/func-stdlib/stdlib.fc \
    PATH="/opt/ton-sandbox/node_modules/.bin:${PATH}" \
    npm_config_offline=true \
    UPLOAD_PATH=/input/upload.zip \
    WORK_DIR=/work \
    REPORT_PATH=/work/report.json

RUN useradd --uid 10001 --create-home auditor \
    && mkdir -p /work /input \
    && chown auditor:auditor /work

USER auditor
ENTRYPOINT ["python", "-m", "backend.worker_runner.main"]
