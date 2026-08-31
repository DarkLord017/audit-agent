# Attribution

The `cosmos-auditor` skill is written for this project. Orchestration, generic
lenses, judging, and report formatting are original. The Cosmos/IBC/CosmWasm
pattern catalogs under `references/hacking-agents/cosmos-*-agent.md` are
adapted from third-party work.

## Original to this project

- `SKILL.md`
- `references/senior-auditor-sop.md`
- `references/judging.md`
- `references/report-formatting.md`
- `references/hacking-agents/shared-rules.md`
- `references/hacking-agents/access-control-agent.md`
- `references/hacking-agents/economic-security-agent.md`
- `references/hacking-agents/invariant-agent.md`
- `references/hacking-agents/execution-trace-agent.md`
- `references/hacking-agents/periphery-agent.md`
- `references/hacking-agents/first-principles-agent.md`
- `references/hacking-agents/boundary-agent.md`
- `references/hacking-agents/trust-gap-agent.md`
- `references/hacking-agents/flow-gap-agent.md`
- `references/hacking-agents/numerical-gap-agent.md`

## Adapted from Trail of Bits

These hacking-agent files wrap the numbered pattern catalogs from the
`cosmos-vulnerability-scanner` skill. Each keeps the upstream pattern text
and adds an agent role plus FINDING/LEAD output fields.

| File | Upstream resource |
|---|---|
| `references/hacking-agents/cosmos-core-agent.md` | `resources/VULNERABILITY_PATTERNS.md` |
| `references/hacking-agents/cosmos-state-agent.md` | `resources/STATE_VULNERABILITY_PATTERNS.md` |
| `references/hacking-agents/cosmos-advanced-agent.md` | `resources/ADVANCED_VULNERABILITY_PATTERNS.md` |
| `references/hacking-agents/cosmos-ibc-agent.md` | `resources/IBC_VULNERABILITY_PATTERNS.md` |
| `references/hacking-agents/cosmos-cosmwasm-agent.md` | `resources/COSMWASM_VULNERABILITY_PATTERNS.md` |

| | |
|---|---|
| **Source** | [`cosmos-vulnerability-scanner`](https://github.com/trailofbits/skills/tree/main/plugins/building-secure-contracts/skills/cosmos-vulnerability-scanner) in [trailofbits/skills](https://github.com/trailofbits/skills) |
| **Licence** | **CC-BY-SA-4.0** (repository LICENSE) |
| **Adapted at commit** | [`d7f76b5`](https://github.com/trailofbits/skills/commit/d7f76b532d1e4c6e7757e04d25c99ab60dd5e32c) |
| **Adapted on** | 2026-08-31 |

### What CC-BY-SA-4.0 requires

**ShareAlike is copyleft.** A derivative of CC-BY-SA material must itself
be released under CC-BY-SA-4.0. The five `cosmos-*-agent.md` files listed
above are such derivatives, so **those files are licensed CC-BY-SA-4.0**,
not under whatever licence this repository otherwise uses.

This does not spread to the rest of the repository. The obligation covers
the adapted work, not everything that sits beside it or calls it. The other
files above are original and unaffected.
