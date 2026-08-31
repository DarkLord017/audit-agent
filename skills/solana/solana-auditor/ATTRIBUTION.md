# Attribution

The `solana-auditor` skill is an **original adaptation** for this project.
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

- All Solana/Anchor-specific guidance: `invoke` / `invoke_signed`, PDAs and bumps, `AccountInfo` owner/signer, sysvars, instruction introspection, SPL token CPI, `#[derive(Accounts)]` constraints.
- No Pashov ASCII banner.
- No `AskUserQuestion` / model picker (this runtime is not Claude Code interactive).
- No `VERSION` curl against pashov (the worker has no internet).
- In-scope files are `**/*.rs` (Solana/Anchor programs), excluding `**/target/**`, tests, and mocks.

## Trail of Bits pattern files — CC-BY-SA-4.0

Files under [`references/tob-patterns/`](./references/tob-patterns/) are adapted from the Trail of Bits Solana vulnerability scanner. **Those files are licensed CC-BY-SA-4.0.** That obligation does not spread to this `SKILL.md`, the Pashov-shaped orchestration, or the transferable hacking-agent lenses.

| | |
|---|---|
| **Source** | [`solana-vulnerability-scanner`](https://github.com/trailofbits/skills/tree/main/plugins/building-secure-contracts/skills/solana-vulnerability-scanner) in [trailofbits/skills](https://github.com/trailofbits/skills) |
| **Licence** | **CC-BY-SA-4.0** |
| **Fetched at commit** | [`7be90d6`](https://github.com/trailofbits/skills/commit/7be90d6e55e6b5e1607b519e97d0019b32b2656a) |
| **Fetched on** | 2026-08-31 |
| **Source material** | `SKILL.md` and `resources/VULNERABILITY_PATTERNS.md` — used as pattern references, **not** vendored as this skill's `SKILL.md` |

The six ToB patterns (arbitrary CPI, PDA/bump, missing owner, missing signer, sysvar spoofing, instruction introspection) are folded into the 12-agent specialties. The `tob-patterns/` files keep the detection/mitigation examples under ShareAlike.

### What CC-BY-SA-4.0 requires

**ShareAlike is copyleft.** A derivative of CC-BY-SA material must itself be released under CC-BY-SA-4.0. Every file in `references/tob-patterns/` is such a derivative. The rest of this skill (orchestration, SOP, judging, transferable lenses) is original or MIT-derived and unaffected.

## Why MIT's notice is here

MIT requires the copyright and permission notice to travel with substantial
portions of the Software. This skill keeps the 12-agent pipeline, bundle
construction, dedup/gate protocol, and specialty-file layout from
`solidity-auditor`. The notice in [`LICENSE`](./LICENSE) is therefore
included even though the body has been rewritten for Solana.
