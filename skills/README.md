# Skills

Audit skills baked into the worker image at build time.

The worker container runs with no route to the internet, so anything the agent
needs must be present in the image. `backend/docker/worker/Dockerfile` copies
this directory to `/opt/evmbench/skills`, and
`backend/worker_runner/workspace.py` installs the profile's skill into the
agent's workspace for each job.

## Contents

| Skill | Author | Licence | Upstream |
|---|---|---|---|
| [`solidity-auditor`](./solidity-auditor) | [Pashov Audit Group](https://github.com/pashov) — **third party** | MIT | [pashov/skills](https://github.com/pashov/skills/tree/main/solidity-auditor) |

## Vendoring policy

Skills in this directory are vendored copies of upstream work and are **not
authored by this project** unless stated otherwise above. Each vendored skill
carries:

- `LICENSE` — the upstream licence, verbatim
- `ATTRIBUTION.md` — author, upstream URL, pinned commit, and any local changes

Keep the skill body byte-identical to upstream wherever possible so that
re-vendoring stays a straight copy and local changes remain auditable. Record
the pinned commit in `ATTRIBUTION.md` when updating.

Adding a new skill also means registering an `AuditProfile` in
`backend/worker_runner/profiles.py`, whose `source` field should carry the same
upstream URL.
