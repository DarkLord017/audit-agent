<!--
Adapted from the cairo-vulnerability-scanner skill in trailofbits/skills,
which is licensed CC-BY-SA-4.0. This directory is therefore also CC-BY-SA-4.0.
See ../../ATTRIBUTION.md.
-->

# Trail of Bits Cairo patterns (extra references)

These files are **not** part of upstream `cairo-auditor`. They are extra
CC-BY-SA-4.0 references adapted from Trail of Bits'
[`cairo-vulnerability-scanner`](https://github.com/trailofbits/skills/tree/main/plugins/building-secure-contracts/skills/cairo-vulnerability-scanner).
Upstream `SKILL.md` is unchanged; specialists are not auto-bundled these
files. Read them when a finding touches felt252 arithmetic, L1 handlers,
storage layout, or L1–L2 messaging.

| File | Pattern |
|---|---|
| [VULNERABILITY_PATTERNS.md](VULNERABILITY_PATTERNS.md) | Upstream ToB pattern dump (header added only) |
| [felt252-overflow.md](felt252-overflow.md) | Unchecked `felt252` arithmetic |
| [l1-handler-from-address.md](l1-handler-from-address.md) | Unchecked `from_address` on `#[l1_handler]` |
| [storage-collision.md](storage-collision.md) | Storage slot / component collision |
| [l1-l2-messaging.md](l1-l2-messaging.md) | Address conversion, message failure, overconstrained bridges |
| [signature-replay.md](signature-replay.md) | Missing nonce / domain separator |

**Licence:** CC-BY-SA-4.0. See [`../../ATTRIBUTION.md`](../../ATTRIBUTION.md).
