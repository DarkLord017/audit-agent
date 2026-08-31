# Caracal in this container

Caracal is Trail of Bits' Sierra-level static analyzer for Cairo
(https://github.com/crytic/caracal). It is **not installed** in this
worker image.

The last prebuilt release (v0.2.3) targets Cairo **≤ 2.5.0**. This image
ships Scarb 2.20 / Cairo 2.20. Building Caracal from source needs a Rust
toolchain and would still not parse current Sierra. Shipping a stale
binary that crashes on every upload is worse than skipping it.

Never try to `cargo install --git https://github.com/crytic/caracal` —
there is no network and no `cargo`.

## If `caracal` is on PATH anyway

Treat it like Slither: a fast second opinion, not a proof. It often
writes useful lines to **stderr**, so capture both streams:

```
caracal detect src/ 2>&1 | tail -80
```

Detectors named in ToB's cairo scanner:

| Detector | Pattern |
|---|---|
| `unchecked-felt252-arithmetic` | felt252 used as a quantity |
| `unchecked-l1-handler-from` | `#[l1_handler]` without `from_address` check |
| `missing-nonce-validation` | signatures without a nonce |

Caracal agreeing with a finding raises confidence. Caracal **not**
flagging something is weak evidence of absence. Never mark VERIFIED
because Caracal agrees. Only a passing snforge test is proof.

## In this image

Write **Static cross-check: Caracal not in image** in the report and move
on. Triage and snforge still apply.
