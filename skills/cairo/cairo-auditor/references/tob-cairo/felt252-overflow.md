<!--
Adapted from the cairo-vulnerability-scanner skill in trailofbits/skills,
which is licensed CC-BY-SA-4.0. This file is therefore also CC-BY-SA-4.0.
See ../../../ATTRIBUTION.md.
-->

# felt252 arithmetic overflow / underflow

`felt252` is a field element in `[0, P)` where `P` is the Starknet prime
(`2^251 + 17*2^192 + 1`). Addition, subtraction and multiplication wrap in
the field. They do **not** revert. Using `felt252` for balances, amounts,
shares or rewards is a classic Cairo footgun.

**Severity:** High (often Critical when it mints or drains).

## Detection

```cairo
#[external(v0)]
fn transfer(ref self: ContractState, to: ContractAddress, amount: felt252) {
    let sender = get_caller_address();
    let mut sender_balance = self.balances.read(sender);
    // wraps to ~P on underflow; wraps toward 0 on overflow
    sender_balance = sender_balance - amount;
    self.balances.write(sender, sender_balance);
    self.balances.write(to, self.balances.read(to) + amount);
}
```

Look for:

- `felt252` storage used as a quantity (`balance`, `amount`, `total`, `supply`, `shares`, `reward`, `fee`)
- `+`, `-`, `*` on those values with no range assert
- Mixed `felt252` / `u256` conversions that drop the overflow check

`u8`/`u16`/`u32`/`u64`/`u128`/`u256` panic on overflow in Cairo 1/2. Prefer
those for anything that represents a quantity.

## Mitigation

Use a bounded integer and assert sufficiency **before** subtracting:

```cairo
fn transfer(ref self: ContractState, to: ContractAddress, amount: u128) {
    let sender = get_caller_address();
    let sender_balance = self.balances.read(sender);
    assert(sender_balance >= amount, 'insufficient');
    self.balances.write(sender, sender_balance - amount);
    self.balances.write(to, self.balances.read(to) + amount);
}
```

If `felt252` is unavoidable, check both directions:

```cairo
assert(sender_balance >= amount, 'underflow');
let new_recipient = recipient_balance + amount;
assert(new_recipient >= recipient_balance, 'overflow');
```

## Caracal

Detector name in ToB docs: `unchecked-felt252-arithmetic`. Caracal is **not**
in this worker image (Cairo 2.5-era binary; see bug-breaker `caracal.md`).

**ToB source:** `building-secure-contracts/not-so-smart-contracts/cairo/arithmetic_overflow`
and `cairo-vulnerability-scanner` pattern "Unchecked Arithmetic" /
"FELT252 ARITHMETIC OVERFLOW/UNDERFLOW".
