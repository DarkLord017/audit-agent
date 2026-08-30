# Foundry in this container

`forge`, `cast` and `anvil` are installed and work. **There is no network.**
That changes two things about every command you run.

## The two flags you always need

```
forge test --offline --use $SOLC_BIN -vv
```

- `forge` is not a compiler. It fetches `solc` on first use, and that
  download dies here with a DNS error. `--use` points it at the compiler
  already in the image.
- `--offline` stops it reaching for a version list at all.

`$SOLC_BIN` is set in the environment. If it is missing:

```
/opt/solc/.solc-select/artifacts/solc-0.8.28/solc-0.8.28
```

These are **command-line flags**, so they override the project's config
without editing any of the uploader's files. Do not edit their
`foundry.toml` to add them.

## Use their project, not yours

If `unzipped/` contains a `foundry.toml`, **work inside their project**.
It carries the remappings, `lib/`, solc version and optimizer settings
their code needs. Nothing else will compile it. Put your tests in their
test directory.

Only if they shipped no `foundry.toml` do you use `poc/`, which is
scaffolded with `forge-std` linked and their contracts reachable as
`unzipped/Whatever.sol`.

## Failures you will actually hit

| Symptom | Cause | Do this |
|---|---|---|
| `Could not resolve host` | missing `--offline`/`--use`, or `forge install` | add the flags; never `forge install` |
| `Source not found` / unresolved import | their remappings not applied | run inside their project, or add `--remappings` |
| `Compiler version mismatch` | pragma wants a version not in the image | `--use $SOLC_BIN` anyway; if the pragma forbids it, say so and mark UNVERIFIED |
| `lib/` empty | they did not vendor dependencies | cannot compile, mark UNVERIFIED, do not fake it |
| Their whole suite fails | pre-existing breakage, not yours | `--match-path` your own test only |

## Run only your test

Their suite may be broken, slow, or noisy. Scope every run:

```
forge test --offline --use $SOLC_BIN --match-path 'test/MyPoc.t.sol' -vvv
```

`-vvv` shows traces, which is what you need to show *why* it failed.

## A note on their config

Their `foundry.toml` may set `ffi = true`, which lets their tests run shell
commands. That is not a threat to this container -- it holds no secret and
has no route out. Just be aware their tests can touch files, so do not
treat anything on disk as authoritative. What you report is what you
observed in the run output.

## Compiling is not proving

`forge build` succeeding means nothing about the finding. Only a test that
runs and demonstrates the claimed behaviour counts. See
[poc.md](poc.md).
