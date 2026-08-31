# Attribution

The `ton-auditor` skill is an **original adaptation** for this project.
It is not a byte-identical vendor of upstream. Its orchestration, FINDING/LEAD
shape, judging gates, report formatting, and 12-agent specialty layout are
adapted from the Pashov Solidity auditor under MIT, which permits this.

| | |
|---|---|
| **Structural source** | [pashov/skills `solidity-auditor`](https://github.com/pashov/skills/tree/main/solidity-auditor) |
| **Author of that source** | Pashov Audit Group ([@pashov](https://github.com/pashov)) |
| **Licence of that source** | MIT — see [`LICENSE`](./LICENSE), reproduced so the copyright notice travels with this derivative |
| **Upstream commit referenced** | [`c577eb7`](https://github.com/pashov/skills/commit/c577eb7799c349de0acb187ba00ca98e14e436fd) |
| **Adapted on** | 2026-08-31 |

## What is original here

- All FunC / Tact guidance: `recv_internal` / `recv_external` / `receive()`, bounce, seqno replay, opcode parsing, `send_raw_message` flags, Tact `sender()` / `bounced()`.
- No Pashov ASCII banner.
- No `AskUserQuestion` / model picker (this runtime is not Claude Code interactive).
- No `VERSION` curl against pashov (the worker has no internet).
- In-scope files are `**/*.fc`, `**/*.func`, `**/*.tact`, excluding tests and wrappers.

## Adapted from Trail of Bits — `references/ton-patterns/`

Three pattern files are adapted from the Trail of Bits TON vulnerability scanner.
They are **CC-BY-SA-4.0** (ShareAlike). See the header comment in each file.

| | |
|---|---|
| **Source** | [`ton-vulnerability-scanner`](https://github.com/trailofbits/skills/tree/main/plugins/building-secure-contracts/skills/ton-vulnerability-scanner) in [trailofbits/skills](https://github.com/trailofbits/skills) |
| **Licence** | **CC-BY-SA-4.0** |
| **Adapted at commit** | [`7be90d6`](https://github.com/trailofbits/skills/commit/7be90d6e55e6b5e1607b519e97d0019b32b2656a) |
| **Adapted on** | 2026-08-31 |
| **Files** | `integer-as-boolean.md`, `fake-jetton.md`, `forward-ton-gas.md` |

`replay-bounce-opcode.md` is original to this project (replay is named in the
ToB scanner's example output, but the detection content here is not copied
from their pattern file).

### What CC-BY-SA-4.0 requires

**ShareAlike is copyleft.** A derivative of CC-BY-SA material must itself
be released under CC-BY-SA-4.0. The three ToB-derived pattern files are
such derivatives, so **those files are licensed CC-BY-SA-4.0**, not under
whatever licence this repository otherwise uses.

This does not spread to the rest of the skill. Orchestration, judging,
report formatting, and the 12 specialty agents are original adaptations
under the MIT notice above.

## Why MIT's notice is here

MIT requires the copyright and permission notice to travel with substantial
portions of the Software. This skill keeps the 12-agent pipeline, bundle
construction, dedup/gate protocol, and specialty-file layout from
`solidity-auditor`. The notice in [`LICENSE`](./LICENSE) is therefore
included even though the body has been rewritten for TON.
