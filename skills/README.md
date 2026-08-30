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
| [`bug-breaker`](./bug-breaker) | this project, except `references/triage.md` | mixed — see note | [trailofbits/skills](https://github.com/trailofbits/skills) (triage only) |

> **Note on `bug-breaker`:** it is original work apart from
> `references/triage.md`, which adapts Trail of Bits' vulnerability-triage
> brocards. Those are **CC-BY-SA-4.0**, and ShareAlike is copyleft, so that
> one file carries CC-BY-SA-4.0 too. The obligation covers the adapted file,
> not the rest of the repository. See
> [`bug-breaker/ATTRIBUTION.md`](./bug-breaker/ATTRIBUTION.md).

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
