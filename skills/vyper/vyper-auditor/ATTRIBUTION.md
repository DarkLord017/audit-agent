# Attribution

The `vyper-auditor` skill is an **original adaptation** for this project.
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

- All Vyper-specific guidance: `@external` / `@internal` / `@payable`, storage (`self.`), `raw_call` / `extcall`, `@nonreentrant`, `__init__` / `@deploy`, `__default__`, `unsafe_*`, `convert()`, interfaces, blueprints.
- No Pashov ASCII banner.
- No `AskUserQuestion` / model picker (this runtime is not Claude Code interactive).
- No `VERSION` curl against pashov (the worker has no internet).
- In-scope files are `**/*.vy`, excluding tests and mocks.

## Why MIT's notice is here

MIT requires the copyright and permission notice to travel with substantial
portions of the Software. This skill keeps the 12-agent pipeline, bundle
construction, dedup/gate protocol, and specialty-file layout from
`solidity-auditor`. The notice in [`LICENSE`](./LICENSE) is therefore
included even though the body has been rewritten for Vyper.
