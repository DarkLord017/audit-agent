# Attribution

The `cairo-auditor` skill in this directory is **third-party work**. It is
not authored by this project.

| | |
|---|---|
| **Author** | Keep Starknet Strange ([@keep-starknet-strange](https://github.com/keep-starknet-strange)) |
| **Upstream** | https://github.com/keep-starknet-strange/starknet-skills/tree/main/cairo-auditor |
| **License** | MIT — see [`LICENSE`](./LICENSE), reproduced verbatim from upstream |
| **Skill version** | 0.2.0 (see [`VERSION`](./VERSION)) |
| **Vendored at commit** | [`7765ad5`](https://github.com/keep-starknet-strange/starknet-skills/commit/7765ad58ddb0aebf6c578ddc23c821b4e11e15f2) |
| **Vendored on** | 2026-08-31 |

## Why it is vendored rather than fetched

The worker container has no route to the internet, so the skill has to be
baked into the image at build time. It is registered as the `cairo` profile
in `backend/worker_runner/ecosystems/cairo.py`, which records the same
upstream URL in its `source` field.

## Local modifications

The skill body is **unmodified** from upstream and is byte-identical to the
pinned commit, with additions that do not rewrite `SKILL.md` or any other
upstream file:

- `LICENSE` — copied from the upstream repository root. MIT requires the
  copyright and permission notice to travel with the code, and upstream keeps
  its licence at the repo root rather than in the skill directory.
- `ATTRIBUTION.md` — this file.
- `references/tob-cairo/` — extra Trail of Bits Cairo pattern references
  (CC-BY-SA-4.0). See that directory's README. They are not part of
  upstream and are not inlined into specialist bundles by `SKILL.md`.

Upstream `SKILL.md` looks for `scripts/quality/audit_local_repo.py` and
`datasets/` relative to the skill's repo root. Those live outside
`cairo-auditor/` upstream and are not vendored here; the preflight step
no-ops, which is expected.

`SKILL.md` also curls the remote `VERSION` at runtime. The worker has no
network, so that check silently no-ops.

To verify the skill content against upstream:

```sh
git clone --depth 1 https://github.com/keep-starknet-strange/starknet-skills.git /tmp/starknet-skills
diff -rq /tmp/starknet-skills/cairo-auditor skills/cairo/cairo-auditor \
  | grep -vE 'LICENSE|ATTRIBUTION.md|references/tob-cairo'
# no output = skill content matches upstream
```

## Updating

Re-vendor deliberately: copy the upstream `cairo-auditor/` directory over
this one (keeping `LICENSE`, `ATTRIBUTION.md`, and `references/tob-cairo/`),
then update the version, commit and date in the table above.

## Extra Trail of Bits files — `references/tob-cairo/`

| | |
|---|---|
| **Source** | [`cairo-vulnerability-scanner`](https://github.com/trailofbits/skills/tree/main/plugins/building-secure-contracts/skills/cairo-vulnerability-scanner) in [trailofbits/skills](https://github.com/trailofbits/skills) |
| **Licence** | **CC-BY-SA-4.0** |
| **Adapted at commit** | [`d1f1575`](https://github.com/trailofbits/skills/commit/d1f1575cff97816e5cc08af66cd2506099c681d3) |
| **Adapted on** | 2026-08-31 |

ShareAlike is copyleft. Those files are CC-BY-SA-4.0; that obligation does
not spread to the MIT-licensed upstream skill body beside them.
