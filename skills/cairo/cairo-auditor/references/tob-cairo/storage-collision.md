<!--
Adapted from the cairo-vulnerability-scanner skill in trailofbits/skills
(pattern: "Storage Collision — conflicting storage variable hashes"),
which is licensed CC-BY-SA-4.0. This file is therefore also CC-BY-SA-4.0.
See ../../../ATTRIBUTION.md.
-->

# Storage collision

Cairo storage slots are derived from names (and, for maps, keys), not from
declaration order the way Solidity `append-only` layouts are taught. Two
variables that hash to the same slot, two components that reuse a
`#[substorage(v0)]` layout, or an upgrade that reinterprets an existing slot
as a different type, will silently alias. Writes to one clobber the other.

**Severity:** Critical when the colliding slots are balances, authorities, or
allowances.

## What collides

**Component substorages.** `#[substorage(v0)]` places a component at a fixed
base. Two components of the same type, or two components that both start
their layout at `v0` without a distinct namespace, share slots.

```cairo
#[storage]
struct Storage {
    #[substorage(v0)]
    ownable: ownable_component::Storage,
    #[substorage(v0)]  // same base as ownable — collision
    erc20: erc20_component::Storage,
}
```

OpenZeppelin components document which `vN` they occupy. Mixing versions, or
embedding the same component twice at `v0`, is the usual bug.

**Name-hash aliasing.** Storage variable addresses are `selector!("name")`
(or the equivalent snip). Unusually, two distinct names in flattened modules
can be chosen so they collide; more often a refactor *renames* a variable
while an upgrade keeps the old slot's bytes, or a new variable is introduced
with a name that an old, removed variable used.

**Upgrade layout.** `replace_class_syscall` keeps storage. The new class must
read every live slot with the same type and meaning. Reordering fields,
changing a `felt252` to a `u256`, or inserting a field in the middle of a
component layout reinterprets leftover data as admin keys or balances.

**Map key encoding.** `Map<ContractAddress, u256>` and a raw `felt252` key
that happens to be that address's felt representation occupy the same slot
family. Mixing `LegacyMap` and `Map` on the "same" logical mapping across an
upgrade is a collision.

## Detection

- Every `#[substorage(vN)]` in the contract and in dependencies: unique `N`
  per component instance, matching the library's documented offset.
- Upgrade entrypoints (`upgrade`, `replace_class_syscall`): diff old vs new
  storage structs field-by-field.
- After a rename or "unused" storage deletion, confirm nothing still writes
  the old selector.
- Two `Map`s that take attacker-controlled keys into a shared value type
  with overlapping key encoding.

## Mitigation

- One component instance per `vN`. Follow the library's storage layout
  notes when adding a second token, a second ownable, or a new mixin.
- Upgrades are append-only: new fields at new names / new `vN`, never
  reuse or retile a live slot.
- Do not delete a storage variable in a class that still has state at that
  selector; freeze it (`_deprecated_foo`) if you must stop using it.

**ToB source:** `cairo-vulnerability-scanner` pattern summary
"Storage Collision — Conflicting storage variable hashes".
