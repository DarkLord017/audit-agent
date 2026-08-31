# Attribution

The `move-auditor` skill in this directory is **third-party work**. It is
not authored by this project.

| | |
|---|---|
| **Author** | [sanbir](https://github.com/sanbir) |
| **Upstream** | https://github.com/sanbir/move-auditor-skills/tree/main/move-auditor |
| **License** | MIT — see [`LICENSE`](./LICENSE), reproduced verbatim from upstream |
| **Skill version** | 4 (see [`VERSION`](./VERSION)) |
| **Vendored at commit** | [`6a3b40a`](https://github.com/sanbir/move-auditor-skills/commit/6a3b40a7c792277ba137d723b748bbf9fc4abe55) |
| **Vendored on** | 2026-08-31 |

## Why it is vendored rather than fetched

The worker container has no route to the internet, so the skill has to be
baked into the image at build time. It is registered as the `move` profile
in `backend/worker_runner/ecosystems/move.py`, which records the same
upstream URL in its `source` field.

Trail of Bits has no Move / Sui vulnerability scanner. The upstream Sui
object-model specialties (shared objects, capabilities, PTBs, `sui-protocol-agent`)
are kept as-is. This directory is not rewritten for Aptos.

## Local modifications

The skill content is **unmodified** from upstream and is byte-identical to
the pinned commit, with two additions that do not affect skill behaviour:

- `LICENSE` — copied from the upstream repository root. MIT requires the
  copyright and permission notice to travel with the code, and upstream
  keeps its licence at the repo root rather than in the skill directory.
- `ATTRIBUTION.md` — this file.

`README.md` is upstream's, including the demo GIF path `../static/skill_pag.gif`.
`static/` lives at the upstream repository root and is not vendored here.
The GIF at the pinned commit is
https://raw.githubusercontent.com/sanbir/move-auditor-skills/6a3b40a7c792277ba137d723b748bbf9fc4abe55/static/skill_pag.gif

`SKILL.md` self-checks `VERSION` against upstream at runtime, but the
worker has no network access, so that check silently no-ops.

To verify the skill content against upstream:

```sh
git clone https://github.com/sanbir/move-auditor-skills.git /tmp/move-auditor-skills
git -C /tmp/move-auditor-skills checkout 6a3b40a7c792277ba137d723b748bbf9fc4abe55
diff -rq /tmp/move-auditor-skills/move-auditor skills/move/move-auditor \
  | grep -vE 'LICENSE|ATTRIBUTION.md'
# no output = skill content matches upstream
```

## Updating

Re-vendor deliberately: copy the upstream `move-auditor/` directory over
this one, restore `LICENSE` from the upstream repository root, then update
the version, commit and date in the table above.
