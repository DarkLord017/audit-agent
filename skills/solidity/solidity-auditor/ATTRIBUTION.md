# Attribution

The `solidity-auditor` skill in this directory is **third-party work**. It is
not authored by this project.

| | |
|---|---|
| **Author** | Pashov Audit Group ([@pashov](https://github.com/pashov)) |
| **Upstream** | https://github.com/pashov/skills/tree/main/solidity-auditor |
| **License** | MIT — see [`LICENSE`](./LICENSE), reproduced verbatim from upstream |
| **Skill version** | 3 (see [`VERSION`](./VERSION)) |
| **Vendored at commit** | [`c577eb7`](https://github.com/pashov/skills/commit/c577eb7799c349de0acb187ba00ca98e14e436fd) |
| **Vendored on** | 2026-08-30 |

## Why it is vendored rather than fetched

The worker container has no route to the internet (see
`backend/instancer/docker_backend.py`), so the skill has to be baked into the
image at build time by `backend/docker/worker/Dockerfile`. It is registered as
the `solidity` profile in `backend/worker_runner/profiles.py`, which records the
same upstream URL in its `source` field.

## Local modifications

The skill content is **unmodified** from upstream and is byte-identical to the
pinned commit, with two additions that do not affect skill behaviour:

- `LICENSE` — copied from the upstream repository root. MIT requires the
  copyright and permission notice to travel with the code, and upstream keeps
  its licence at the repo root rather than in the skill directory.
- `ATTRIBUTION.md` — this file.
- `README.md` — an attribution banner prepended to the top. The body is
  otherwise upstream's. The demo GIF link was repointed at the upstream raw URL,
  because `static/` lives at the upstream repository root and is not vendored
  here.

To verify the skill content against upstream:

```sh
git clone --depth 1 https://github.com/pashov/skills.git /tmp/pashov-skills
diff -rq /tmp/pashov-skills/solidity-auditor skills/solidity-auditor \
  | grep -vE 'LICENSE|ATTRIBUTION.md|README.md'
# no output = skill content matches upstream
```

## Updating

`SKILL.md` self-checks `VERSION` against upstream at runtime, but the worker has
no network access, so that check silently no-ops. Re-vendor deliberately: copy
the upstream directory over this one, then update the version, commit and date
in the table above.
