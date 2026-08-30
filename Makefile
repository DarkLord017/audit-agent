# evmbench -- see `make help`
SHELL := /bin/bash
.DEFAULT_GOAL := help
export PWD := $(shell pwd)

COMPOSE := docker compose
API     := http://localhost:1337

.PHONY: help
help:  ## show this help
	@grep -hE '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) \
	  | awk 'BEGIN{FS=":.*?## "}{printf "  \033[36m%-16s\033[0m %s\n", $$1, $$2}'

# --- setup -----------------------------------------------------------

.PHONY: secret
secret:  ## generate a PROXY_SECRET_KEY
	@python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())" \
	  2>/dev/null || docker run --rm python:3.12-slim sh -c \
	  "pip install -q cryptography && python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'"

.PHONY: env
env:  ## create .env from the template
	@test -f .env && echo ".env exists, leaving it alone" || { \
	  cp .env.example .env; \
	  key=$$($(MAKE) -s secret); \
	  sed -i.bak "s|^PROXY_SECRET_KEY=.*|PROXY_SECRET_KEY=$$key|" .env && rm -f .env.bak; \
	  echo "wrote .env -- now put your ANTHROPIC_API_KEY in it"; }

# --- images ----------------------------------------------------------

.PHONY: build
build: build-base build-worker build-backend  ## build every image

.PHONY: build-base
build-base:  ## neutral base (python, node, claude-code)
	docker build -t evmbench/base:latest -f backend/docker/base/Dockerfile .

.PHONY: build-worker
build-worker:  ## solidity worker (foundry, slither, solc, forge-std)
	docker build -t evmbench/worker-solidity:latest -f backend/docker/worker-solidity/Dockerfile .

.PHONY: build-backend
build-backend:  ## api / proxy / instancer
	docker build -t evmbench/backend:latest -f backend/docker/backend/Dockerfile .

# --- running ---------------------------------------------------------

.PHONY: up
up:  ## start everything
	@mkdir -p uploads
	$(COMPOSE) up -d
	@echo "api on $(API)  ·  rabbit ui on http://localhost:15672"

.PHONY: down
down:  ## stop everything (keeps the database)
	$(COMPOSE) down

.PHONY: clean
clean:  ## stop everything and delete the database and uploads
	$(COMPOSE) down -v
	rm -rf uploads/*.zip

.PHONY: logs
logs:  ## tail all logs
	$(COMPOSE) logs -f

.PHONY: ps
ps:  ## what is running, including live workers
	@$(COMPOSE) ps
	@echo "--- workers ---"
	@docker ps --filter label=io.evmbench.job_id \
	  --format '  {{.Names}}  {{.Status}}' || true

.PHONY: psql
psql:  ## open a database shell
	$(COMPOSE) exec postgres psql -U evmbench -d evmbench

# --- using it --------------------------------------------------------

.PHONY: health
health:  ## check the api is up
	@curl -fsS $(API)/health && echo

ZIP ?= fixtures/vulnerable.zip
MODEL ?= claude-opus-5

.PHONY: submit
submit:  ## submit an audit.  make submit ZIP=path/to/code.zip
	@test -f $(ZIP) || { echo "no such zip: $(ZIP) -- try 'make fixture'"; exit 1; }
	@curl -fsS -X POST $(API)/v1/jobs/start \
	  -F "file=@$(ZIP)" -F "model=$(MODEL)" -F "profile=solidity"
	@echo

.PHONY: jobs
jobs:  ## list recent jobs
	@curl -fsS "$(API)/v1/jobs/history?limit=10" \
	  | python3 -m json.tool 2>/dev/null || echo "api not reachable"

JOB ?=
.PHONY: job
job:  ## show one job.  make job JOB=<uuid>
	@test -n "$(JOB)" || { echo "usage: make job JOB=<uuid>"; exit 1; }
	@curl -fsS $(API)/v1/jobs/$(JOB) | python3 -m json.tool

.PHONY: fixture
fixture:  ## build a deliberately vulnerable test zip
	@mkdir -p fixtures/src
	@printf '%s\n' \
	  'pragma solidity ^0.8.20;' \
	  'contract Vault {' \
	  '    mapping(address => uint256) public balance;' \
	  '    function deposit() external payable { balance[msg.sender] += msg.value; }' \
	  '    // no access control: anyone can drain the vault' \
	  '    function withdraw(address to, uint256 amt) external { payable(to).transfer(amt); }' \
	  '}' > fixtures/src/Vault.sol
	@cd fixtures && rm -f vulnerable.zip && zip -qr vulnerable.zip src && echo "wrote fixtures/vulnerable.zip"

# --- checks ----------------------------------------------------------

.PHONY: lint
lint:  ## ruff
	cd backend && .venv/bin/ruff check . --exclude .venv

.PHONY: smoke
smoke:  ## end-to-end: build, up, submit, watch
	$(MAKE) build && $(MAKE) up && sleep 5 && $(MAKE) health \
	  && $(MAKE) fixture && $(MAKE) submit && $(MAKE) jobs
