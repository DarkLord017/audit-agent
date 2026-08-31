# Skills

Audit skills baked into each worker image at build time.

The worker container runs with no route to the internet, so anything the agent
needs must be present in the image. Each `backend/docker/worker-<lang>/Dockerfile`
copies this directory to `/opt/evmbench/skills`, and
`backend/worker_runner/workspace.py` installs the profile's skill from
`skills/<toolchain.key>/<skill>/` into `.claude/skills/<skill>/` for each job.

Layout: **`skills/<toolchain.key>/<skill>/`**. Adding an ecosystem means a
directory here, a profile module in `backend/worker_runner/ecosystems/<lang>.py`,
and a worker Dockerfile — language agents fill the skill trees and
`ATTRIBUTION.md`; this file only lists the structure.

## Contents

Skills are grouped by ecosystem. Licence, author, and pinned-commit details
live in **each skill's `ATTRIBUTION.md`** — the tables below are an index,
not a substitute for those files.

### Solidity

| Skill | Author | Licence | Upstream |
|---|---|---|---|
| [`solidity-auditor`](./solidity/solidity-auditor) | [Pashov Audit Group](https://github.com/pashov) — **third party** | MIT | [pashov/skills](https://github.com/pashov/skills/tree/main/solidity-auditor) |
| [`optimism-auditor`](./solidity/optimism-auditor) | this project | original | chain overlay for OP Mainnet / OP Stack |
| [`bug-breaker`](./solidity/bug-breaker) | this project, except `references/triage.md` | mixed — see note | [trailofbits/skills](https://github.com/trailofbits/skills) (triage only) |

EVM **chain** overlays sit next to `solidity-auditor` as `<chain>-auditor`
(Optimism first). They share the Solidity worker image. The
`solidity-optimism` profile runs `optimism-auditor` then `bug-breaker`.
Generic L1-style jobs keep using profile `solidity`.

> **Note on `bug-breaker`:** it is original work apart from
> `references/triage.md`, which adapts Trail of Bits' vulnerability-triage
> brocards. Those are **CC-BY-SA-4.0**, and ShareAlike is copyleft, so that
> one file carries CC-BY-SA-4.0 too. The obligation covers the adapted file,
> not the rest of the repository. See
> [`bug-breaker/ATTRIBUTION.md`](./solidity/bug-breaker/ATTRIBUTION.md).

### Solana

| Skill | Author | Licence | Upstream |
|---|---|---|---|
| [`solana-auditor`](./solana/solana-auditor) | see skill | see skill | see each skill's `ATTRIBUTION.md` |
| [`bug-breaker`](./solana/bug-breaker) | see skill | see skill | see each skill's `ATTRIBUTION.md` |

### Cairo

| Skill | Author | Licence | Upstream |
|---|---|---|---|
| [`cairo-auditor`](./cairo/cairo-auditor) | see skill | see skill | see each skill's `ATTRIBUTION.md` |
| [`bug-breaker`](./cairo/bug-breaker) | see skill | see skill | see each skill's `ATTRIBUTION.md` |

### Move

| Skill | Author | Licence | Upstream |
|---|---|---|---|
| [`move-auditor`](./move/move-auditor) | see skill | see skill | see each skill's `ATTRIBUTION.md` |
| [`bug-breaker`](./move/bug-breaker) | see skill | see skill | see each skill's `ATTRIBUTION.md` |

### Cosmos

| Skill | Author | Licence | Upstream |
|---|---|---|---|
| [`cosmos-auditor`](./cosmos/cosmos-auditor) | see skill | see skill | see each skill's `ATTRIBUTION.md` |
| [`bug-breaker`](./cosmos/bug-breaker) | see skill | see skill | see each skill's `ATTRIBUTION.md` |

### TON

| Skill | Author | Licence | Upstream |
|---|---|---|---|
| [`ton-auditor`](./ton/ton-auditor) | see skill | see skill | see each skill's `ATTRIBUTION.md` |
| [`bug-breaker`](./ton/bug-breaker) | see skill | see skill | see each skill's `ATTRIBUTION.md` |

### Vyper

| Skill | Author | Licence | Upstream |
|---|---|---|---|
| [`vyper-auditor`](./vyper/vyper-auditor) | see skill | see skill | see each skill's `ATTRIBUTION.md` |
| [`bug-breaker`](./vyper/bug-breaker) | see skill | see skill | see each skill's `ATTRIBUTION.md` |

### Algorand

| Skill | Author | Licence | Upstream |
|---|---|---|---|
| [`algorand-auditor`](./algorand/algorand-auditor) | see skill | see skill | see each skill's `ATTRIBUTION.md` |
| [`bug-breaker`](./algorand/bug-breaker) | see skill | see skill | see each skill's `ATTRIBUTION.md` |

## Vendoring policy

Skills live at `skills/<toolchain.key>/<skill>/`. They are vendored copies of
upstream work and are **not authored by this project** unless stated otherwise
in that skill's `ATTRIBUTION.md`. Each vendored skill carries:

- `LICENSE` — the upstream licence, verbatim
- `ATTRIBUTION.md` — author, upstream URL, pinned commit, and any local changes

Keep the skill body byte-identical to upstream wherever possible so that
re-vendoring stays a straight copy and local changes remain auditable. Record
the pinned commit in `ATTRIBUTION.md` when updating.

Adding a new skill also means registering an `AuditProfile` (Solidity in
`backend/worker_runner/profiles.py`; every other ecosystem in
`backend/worker_runner/ecosystems/<lang>.py`), whose `source` field should
carry the same upstream URL.
