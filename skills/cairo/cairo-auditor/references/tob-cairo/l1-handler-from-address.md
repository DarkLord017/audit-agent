<!--
Adapted from the cairo-vulnerability-scanner skill in trailofbits/skills,
which is licensed CC-BY-SA-4.0. This file is therefore also CC-BY-SA-4.0.
See ../../ATTRIBUTION.md.
-->

# Unchecked `from_address` in L1 handlers

`#[l1_handler]` functions are invoked by the Starknet OS when an L1 contract
calls `sendMessageToL2`. The first parameter after `self` is `from_address`:
the L1 sender. **Any** L1 contract can send a message. If the handler does
not check `from_address` against a stored, authorized L1 bridge, an attacker
deploys their own L1 contract and mints, credits, or unlocks at will.

**Severity:** Critical (infinite mint / unauthorized credit is the usual
impact).

## Detection

```cairo
#[l1_handler]
fn handle_deposit(
    ref self: ContractState,
    from_address: felt252,  // never compared
    user: ContractAddress,
    amount: u256,
) {
    let current = self.balances.read(user);
    self.balances.write(user, current + amount);
}
```

L1-side `onlyOwner` / `onlyAuthorized` does **not** help. The attacker does
not use your L1 contract; they use theirs.

Every `#[l1_handler]` must:

- compare `from_address` to a stored authorized L1 address
- reject the zero address
- treat a missing check as Critical even if "the L1 is trusted"

## Mitigation

```cairo
#[l1_handler]
fn handle_deposit(
    ref self: ContractState,
    from_address: felt252,
    user: ContractAddress,
    amount: u256,
) {
    assert(from_address == self.l1_bridge_address.read(), 'Unauthorized L1 sender');
    let zero: ContractAddress = 0.try_into().unwrap();
    assert(user != zero, 'Invalid user');
    self.balances.write(user, self.balances.read(user) + amount);
}
```

## Caracal

Detector name in ToB docs: `unchecked-l1-handler-from`. Not installed in
this image.

**ToB source:** `building-secure-contracts/not-so-smart-contracts/cairo/unchecked_l1_handler_from`
and `cairo-vulnerability-scanner` pattern "UNCHECKED from_address IN L1 HANDLER".
