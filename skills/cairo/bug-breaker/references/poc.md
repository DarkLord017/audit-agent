# Writing a proof

A proof is a test that **fails, or succeeds, only because the bug is real**.
If the test would behave the same on correct code, it proves nothing.

## The shape

One test per finding. Name it after the finding. Put it in `tests/` of
whichever project you are using (theirs, or `poc/`).

```cairo
use snforge_std::{
    declare, ContractClassTrait, DeclareResultTrait,
    start_cheat_caller_address, stop_cheat_caller_address,
};
use starknet::ContractAddress;

fn attacker() -> ContractAddress {
    0xBEEF.try_into().unwrap()
}

fn victim() -> ContractAddress {
    0x1111.try_into().unwrap()
}

#[test]
fn test_attacker_drains_other_users_deposit() {
    let class = declare("Vault").unwrap().contract_class();
    let (vault, _) = class.deploy(@array![]).unwrap();

    // 1. ARRANGE - a victim with something to lose
    start_cheat_caller_address(vault, victim());
    // Vault::deposit(vault, 1000_u256);  // dispatcher call
    stop_cheat_caller_address(vault);

    // 2. ACT - the attacker does the thing the finding claims
    start_cheat_caller_address(vault, attacker());
    // Vault::withdraw(vault, 1000_u256);
    stop_cheat_caller_address(vault);

    // 3. ASSERT - the harm, in numbers
    // assert(Vault::balance_of(vault, attacker()) == 1000, 'attacker took deposit');
    // assert(Vault::balance_of(vault, victim()) == 0, 'victim drained');
}
```

Replace the commented dispatcher calls with the actual interface from the
contract under review. Verified working in this kind of container looks
like:

```
[PASS] tests::test_drain::test_attacker_drains_other_users_deposit
```

## The three parts, always

**Arrange** — set up a state where there is something real to lose. A bug
that only "works" on an empty contract usually is not one.

**Act** — do exactly what the finding claims an attacker can do. Use
`start_cheat_caller_address` so the caller is unmistakably not the owner.

**Assert** — assert the *harm*, not the mechanism.
`balance_of(attacker) == 1000` is a proof. `withdraw did not panic` is
not — plenty of harmless functions do not panic.

## Cheatcodes you will need

| Cheatcode | Use |
|---|---|
| `start_cheat_caller_address(c, a)` / `stop_cheat_caller_address(c)` | next calls to `c` come from `a` (`vm.prank`) |
| `start_cheat_caller_address_global(a)` | all contracts see `a` as caller |
| `start_cheat_block_timestamp(c, t)` | move time (`vm.warp`) |
| `start_cheat_block_number(c, n)` | move block number |
| `spy_events()` | assert on events |
| `#[should_panic(expected: 'reason')]` | prove something *should* fail |

`#[l1_handler]` functions are not called with an ordinary dispatcher.
snforge can execute them via the L1 handler entry point / `execute` helpers
in current snforge_std — if you cannot reach an L1 handler in this
version, mark the finding UNVERIFIED and say so. Do not pretend an L2
external function is the handler.

## Two directions a proof can run

**The bug lets something happen that should not.** Write a test that
*passes* — the attacker succeeds. That passing test is the proof.

**The bug blocks something that should work.** Write a test doing the
legitimate thing and show it panics. Quote the panic payload.

Either way, quote the output. A claim of "the test passed" without the
output is not evidence.

## Honest failure

If you cannot build a proof, say why in one line and mark it UNVERIFIED:

- *"their Scarb.lock deps are not in the image cache, the contract does not compile"*
- *"needs a live Starknet RPC / fork, and there is no network"*
- *"needs two contracts to interact and the second is not in scope"*
- *"`#[l1_handler]` cannot be invoked from this snforge version"*

Do not:

- assert something trivially true and call it a proof
- mark VERIFIED because the code "obviously" has the bug
- rewrite the contract under review to make your test pass

That last one is the subtle failure. **Never modify anything in
`unzipped/`.** If your test only passes after you changed their code, you
have proved a bug in your code, not theirs.

## Minimal mocks are fine

If the contract needs an ERC-20-like token to construct, write a short
mock in your test package (`poc/src/mock_token.cairo`). That is setup, not
modification. Keep it minimal — a mock that does anything clever becomes
the thing you are testing.

Copying a `.cairo` file from `unzipped/` into `poc/src/` (when they shipped
no `Scarb.toml`) is also setup. Do not write back into `unzipped/`.
