# Attribution

The `bug-breaker` skill is written for this project, with one part adapted
from third-party work.

## Original to this project

- `SKILL.md`
- `references/tealer.md` — Tealer commands for this worker image
- `references/pyteal.md`
- `references/poc.md`

## Adapted from Trail of Bits — `references/triage.md`

| | |
|---|---|
| **Source** | [`vulnerability-triage-brocards`](https://github.com/trailofbits/skills/tree/main/plugins/vulnerability-triage-brocards) in [trailofbits/skills](https://github.com/trailofbits/skills) |
| **Original author** | William Woodruff, ["Brocards for vulnerability triage"](https://blog.yossarian.net/2026/04/11/Brocards-for-vulnerability-triage) (2026) |
| **Licence** | **CC-BY-SA-4.0** |
| **Adapted at commit** | [`d1f1575`](https://github.com/trailofbits/skills/commit/d1f1575) |
| **Adapted on** | 2026-08-31 |

`references/triage.md` keeps the seven brocards and their structure, and
rewrites the tests and examples for Algorand — RekeyTo / CloseRemainderTo,
creator vs unprivileged sender, UpdateApplication, logic signatures,
ClearState, unreachable ABI methods.

### What CC-BY-SA-4.0 requires

**ShareAlike is copyleft.** A derivative of CC-BY-SA material must itself
be released under CC-BY-SA-4.0. `references/triage.md` is such a
derivative, so **that file is licensed CC-BY-SA-4.0**, not under whatever
licence this repository otherwise uses.

This does not spread to the rest of the repository. The obligation covers
the adapted work, not everything that sits beside it or calls it. The other
files above are original and unaffected.

If you would rather not carry a CC-BY-SA file, delete
`references/triage.md` and remove the triage step from `SKILL.md`. The skill
still runs; it just proves findings without filtering them first, which
costs more budget per job.

## Related

The `algorand-auditor` skill in `../algorand-auditor/` is an original
adaptation of Pashov `solidity-auditor` under MIT, with ToB Algorand
patterns under CC-BY-SA-4.0 — see its own `ATTRIBUTION.md`.
