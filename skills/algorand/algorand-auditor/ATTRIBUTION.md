# Attribution

The `algorand-auditor` skill is an **original adaptation** for this project.
It is not a byte-identical vendor of upstream. Its orchestration, FINDING/LEAD
shape, judging gates, report formatting, and 12-agent specialty layout are
adapted from the Pashov Solidity auditor under MIT, which permits this.

Algorand-specific vulnerability patterns are adapted from Trail of Bits'
algorand-vulnerability-scanner (CC-BY-SA-4.0) and live in the files listed
below. Those files are licensed CC-BY-SA-4.0; the rest of this skill is not.

| | |
|---|---|
| **Structural source** | [pashov/skills `solidity-auditor`](https://github.com/pashov/skills/tree/main/solidity-auditor) |
| **Author of that source** | Pashov Audit Group ([@pashov](https://github.com/pashov)) |
| **Licence of that source** | MIT — see [`LICENSE`](./LICENSE), reproduced so the copyright notice travels with this derivative |
| **Upstream commit referenced** | [`c577eb7`](https://github.com/pashov/skills/commit/c577eb7799c349de0acb187ba00ca98e14e436fd) |
| **Adapted on** | 2026-08-31 |

## What is original here

- Orchestration rewritten for TEAL / PyTeal (no Pashov ASCII banner).
- No `AskUserQuestion` / model picker (this runtime is not Claude Code interactive).
- No `VERSION` curl against pashov (the worker has no internet).
- In-scope files are `**/*.teal` and PyTeal `**/*.py` (detected by import, not every `.py`), excluding tests.
- Generic lenses (economic security, first principles, gap hunters) rewritten for Algorand.

## Adapted from Trail of Bits — CC-BY-SA-4.0 files

| | |
|---|---|
| **Source** | [`algorand-vulnerability-scanner`](https://github.com/trailofbits/skills/tree/main/plugins/building-secure-contracts/skills/algorand-vulnerability-scanner) in [trailofbits/skills](https://github.com/trailofbits/skills) |
| **Licence** | **CC-BY-SA-4.0** |
| **Adapted at commit** | [`d1f1575`](https://github.com/trailofbits/skills/commit/d1f1575) |
| **Adapted on** | 2026-08-31 |

These files encode the 11 Algorand patterns (rekey, CloseRemainderTo,
AssetCloseTo, group size, clawback, clear-state, fees, asset ID, opt-in,
inner transactions, access controls) and are therefore CC-BY-SA-4.0:

- `references/hacking-agents/tob-algorand-patterns.md`
- `references/hacking-agents/rekey-agent.md`
- `references/hacking-agents/close-remainder-agent.md`
- `references/hacking-agents/group-size-agent.md`
- `references/hacking-agents/clawback-agent.md`
- `references/hacking-agents/clear-state-agent.md`
- `references/hacking-agents/fee-inner-agent.md`

### What CC-BY-SA-4.0 requires

**ShareAlike is copyleft.** A derivative of CC-BY-SA material must itself
be released under CC-BY-SA-4.0. The files listed above are such
derivatives. This does not spread to the rest of the skill or repository.

## Why MIT's notice is here

MIT requires the copyright and permission notice to travel with substantial
portions of the Software. This skill keeps the 12-agent pipeline, bundle
construction, dedup/gate protocol, and specialty-file layout from
`solidity-auditor`. The notice in [`LICENSE`](./LICENSE) is therefore
included even though the body has been rewritten for Algorand.
