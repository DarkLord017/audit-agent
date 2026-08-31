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
| [`bug-breaker`](./solidity/bug-breaker) | this project, except `references/triage.md` | mixed — see note | [trailofbits/skills](https://github.com/trailofbits/skills) (triage only) |

> **Note on `bug-breaker`:** it is original work apart from
> `references/triage.md`, which adapts Trail of Bits' vulnerability-triage
> brocards. Those are **CC-BY-SA-4.0**, and ShareAlike is copyleft, so that
> one file carries CC-BY-SA-4.0 too. The obligation covers the adapted file,
> not the rest of the repository. See
> [`bug-breaker/ATTRIBUTION.md`](./solidity/bug-breaker/ATTRIBUTION.md).

### Solana

| Skill | Author | Licence | Upstream |
|---|---|---|---|
| [`solana-auditor`](./solana/solana-auditor) | this project, adapted from [Pashov Audit Group](https://github.com/pashov); ToB patterns **third party** | mixed — MIT + CC-BY-SA-4.0 | [pashov/skills](https://github.com/pashov/skills/tree/main/solidity-auditor) (structure); [trailofbits solana scanner](https://github.com/trailofbits/skills/tree/main/plugins/building-secure-contracts/skills/solana-vulnerability-scanner) (patterns) |
| [`bug-breaker`](./solana/bug-breaker) | this project, except `references/triage.md` | mixed — see note | [trailofbits/skills](https://github.com/trailofbits/skills) (triage only) |

> **Note on `solana-auditor`:** orchestration is a Pashov-shaped original adaptation (MIT); `references/tob-patterns/` is adapted from Trail of Bits (**CC-BY-SA-4.0**). See [`solana-auditor/ATTRIBUTION.md`](./solana/solana-auditor/ATTRIBUTION.md). `bug-breaker` follows the same mixed-licence pattern as Solidity (triage file only). See [`bug-breaker/ATTRIBUTION.md`](./solana/bug-breaker/ATTRIBUTION.md).

### Cairo

| Skill | Author | Licence | Upstream |
|---|---|---|---|
| [`cairo-auditor`](./cairo/cairo-auditor) | [Keep Starknet Strange](https://github.com/keep-starknet-strange) — **third party** | MIT (skill body); extra ToB files CC-BY-SA-4.0 | [keep-starknet-strange/starknet-skills](https://github.com/keep-starknet-strange/starknet-skills/tree/main/cairo-auditor) |
| [`bug-breaker`](./cairo/bug-breaker) | this project, except `references/triage.md` | mixed — see note | [trailofbits/skills](https://github.com/trailofbits/skills) (triage only) |

> **Note on extra files:** the skill body is unmodified upstream MIT; `references/tob-cairo/` is extra Trail of Bits material under **CC-BY-SA-4.0**. See [`cairo-auditor/ATTRIBUTION.md`](./cairo/cairo-auditor/ATTRIBUTION.md). `bug-breaker` follows the same mixed-licence pattern as Solidity. See [`bug-breaker/ATTRIBUTION.md`](./cairo/bug-breaker/ATTRIBUTION.md).

### Move

| Skill | Author | Licence | Upstream |
|---|---|---|---|
| [`move-auditor`](./move/move-auditor) | [sanbir](https://github.com/sanbir) — **third party** | MIT | [sanbir/move-auditor-skills](https://github.com/sanbir/move-auditor-skills/tree/main/move-auditor) |
| [`bug-breaker`](./move/bug-breaker) | this project, except `references/triage.md` | mixed — see note | [trailofbits/skills](https://github.com/trailofbits/skills) (triage only) |

> **Note on `bug-breaker`:** same mixed-licence pattern as Solidity (`references/triage.md` is **CC-BY-SA-4.0**). See [`bug-breaker/ATTRIBUTION.md`](./move/bug-breaker/ATTRIBUTION.md).

### Cosmos

| Skill | Author | Licence | Upstream |
|---|---|---|---|
| [`cosmos-auditor`](./cosmos/cosmos-auditor) | this project, except five `cosmos-*-agent.md` pattern catalogs | mixed — original + CC-BY-SA-4.0 | [trailofbits cosmos scanner](https://github.com/trailofbits/skills/tree/main/plugins/building-secure-contracts/skills/cosmos-vulnerability-scanner) (patterns) |
| [`bug-breaker`](./cosmos/bug-breaker) | this project, except `references/triage.md` | mixed — see note | [trailofbits/skills](https://github.com/trailofbits/skills) (triage only) |

> **Note on `cosmos-auditor`:** original except the five `cosmos-*-agent.md` catalogs, adapted from Trail of Bits (**CC-BY-SA-4.0**). See [`cosmos-auditor/ATTRIBUTION.md`](./cosmos/cosmos-auditor/ATTRIBUTION.md). `bug-breaker` follows the same mixed-licence pattern as Solidity. See [`bug-breaker/ATTRIBUTION.md`](./cosmos/bug-breaker/ATTRIBUTION.md).

### TON

| Skill | Author | Licence | Upstream |
|---|---|---|---|
| [`ton-auditor`](./ton/ton-auditor) | this project, adapted from [Pashov Audit Group](https://github.com/pashov); ToB patterns **third party** | mixed — MIT + CC-BY-SA-4.0 | [pashov/skills](https://github.com/pashov/skills/tree/main/solidity-auditor) (structure); [trailofbits ton scanner](https://github.com/trailofbits/skills/tree/main/plugins/building-secure-contracts/skills/ton-vulnerability-scanner) (patterns) |
| [`bug-breaker`](./ton/bug-breaker) | this project, except `references/triage.md` | mixed — see note | [trailofbits/skills](https://github.com/trailofbits/skills) (triage only) |

> **Note on `ton-auditor`:** orchestration is a Pashov-shaped original adaptation (MIT); three files under `references/ton-patterns/` are adapted from Trail of Bits (**CC-BY-SA-4.0**). See [`ton-auditor/ATTRIBUTION.md`](./ton/ton-auditor/ATTRIBUTION.md). `bug-breaker` follows the same mixed-licence pattern as Solidity. See [`bug-breaker/ATTRIBUTION.md`](./ton/bug-breaker/ATTRIBUTION.md).

### Vyper

| Skill | Author | Licence | Upstream |
|---|---|---|---|
| [`vyper-auditor`](./vyper/vyper-auditor) | this project, adapted from [Pashov Audit Group](https://github.com/pashov) | MIT | [pashov/skills](https://github.com/pashov/skills/tree/main/solidity-auditor) (structure) |
| [`bug-breaker`](./vyper/bug-breaker) | this project, except `references/triage.md` | mixed — see note | [trailofbits/skills](https://github.com/trailofbits/skills) (triage only) |

> **Note on `bug-breaker`:** same mixed-licence pattern as Solidity (`references/triage.md` is **CC-BY-SA-4.0**). See [`bug-breaker/ATTRIBUTION.md`](./vyper/bug-breaker/ATTRIBUTION.md).

### Algorand

| Skill | Author | Licence | Upstream |
|---|---|---|---|
| [`algorand-auditor`](./algorand/algorand-auditor) | this project, adapted from [Pashov Audit Group](https://github.com/pashov); ToB patterns **third party** | mixed — MIT + CC-BY-SA-4.0 | [pashov/skills](https://github.com/pashov/skills/tree/main/solidity-auditor) (structure); [trailofbits algorand scanner](https://github.com/trailofbits/skills/tree/main/plugins/building-secure-contracts/skills/algorand-vulnerability-scanner) (patterns) |
| [`bug-breaker`](./algorand/bug-breaker) | this project, except `references/triage.md` | mixed — see note | [trailofbits/skills](https://github.com/trailofbits/skills) (triage only) |

> **Note on `algorand-auditor`:** orchestration is a Pashov-shaped original adaptation (MIT); ToB Algorand pattern files under `references/hacking-agents/` are **CC-BY-SA-4.0**. See [`algorand-auditor/ATTRIBUTION.md`](./algorand/algorand-auditor/ATTRIBUTION.md). `bug-breaker` follows the same mixed-licence pattern as Solidity. See [`bug-breaker/ATTRIBUTION.md`](./algorand/bug-breaker/ATTRIBUTION.md).

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
