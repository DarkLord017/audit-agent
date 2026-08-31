# Solana lints in this container

Trail of Bits [solana-lints](https://github.com/trailofbits/solana-lints)
(dylint) is **not installed**. There is no network, so never try:

```
cargo install cargo-dylint dylint-link    # WRONG — will fail DNS
cargo dylint --git https://github.com/trailofbits/solana-lints
```

Skip the static cross-check in one line if nothing below works.

## What you may try

If `cargo clippy` is on PATH (it may not be — this image uses a minimal
rustup profile):

```
cargo clippy --offline --manifest-path unzipped/Cargo.toml -- -W clippy::all 2>&1 | tail -80
```

Clippy agreeing with a finding raises confidence. Clippy **not** flagging
something is weak evidence of absence — it has no view of PDA identity,
CPI program ids, or economic flows, which is where most real findings
live.

Never mark a finding VERIFIED because a linter agrees. A linter is a
static opinion; only a passing test is proof.

## ToB lint names (for reading, not running)

If you recognise these from the auditor's pattern files, you can *name*
them in the report as "would have matched," but that is not a cross-check:

- `unchecked-cpi-program-id`
- `improper-pda-validation`
- `missing-ownership-check`
- `missing-signer-check`
- `unchecked-sysvar-account`
