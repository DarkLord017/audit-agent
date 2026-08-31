# Writing a proof

A proof is a test that **fails, or succeeds, only because the bug is real**.
If the test would behave the same on correct code, it proves nothing.

## The shape

One test per finding. Name it after the finding. Put it under `poc/tests/`
(or a copy of their package — never under `unzipped/`).

```move
#[test_only]
module poc::vault_drain_tests {
    use sui::test_scenario::{Self as ts};
    use sui::coin::{Self, Coin};
    use sui::sui::SUI;
    use sui::test_utils::assert_eq;

    const ADMIN: address = @0xAD;
    const VICTIM: address = @0xB0B;
    const ATTACKER: address = @0xA11CE;

    #[test]
    fun test_attacker_drains_other_users_deposit() {
        let mut scenario = ts::begin(ADMIN);
        // 1. ARRANGE - a victim with something to lose
        //    init the package, share the vault, victim deposits
        ts::next_tx(&mut scenario, VICTIM);
        // ... victim deposit ...

        // 2. ACT - the attacker does the thing the finding claims
        ts::next_tx(&mut scenario, ATTACKER);
        // ... attacker withdraws the victim's balance, no AdminCap ...

        // 3. ASSERT - the harm, in numbers
        let stolen = ts::take_from_sender<Coin<SUI>>(&scenario);
        assert_eq(coin::value(&stolen), 1_000_000_000);
        ts::return_to_sender(&scenario, stolen);
        ts::end(scenario);
    }
}
```

Verified working in this container looks like:

```
Running Move unit tests
[ PASS    ] poc::vault_drain_tests::test_attacker_drains_other_users_deposit
Test result: OK. Total tests: 1; passed: 1; failed: 0
```

## The three parts, always

**Arrange** — set up a state where there is something real to lose. A bug
that only "works" on an empty shared object usually is not one. Give the
victim a `Coin<SUI>` (or the protocol's coin) and put it in the vault.

**Act** — do exactly what the finding claims an attacker can do. Use
`test_scenario::next_tx(&mut scenario, ATTACKER)` so the sender is
unmistakably not the `AdminCap` holder. Do **not** pass the capability
into the attacking transaction unless the finding is that anyone can
obtain it.

**Assert** — assert the *harm*, not the mechanism. `coin::value(&stolen)
== 1_000_000_000` is a proof. "the call did not abort" is not — plenty of
harmless functions succeed.

## Modelling capabilities, shared objects, PTBs

| Situation | How to test it |
|---|---|
| Missing cap check on a shared object | Share the object in `ADMIN`'s tx, then call the `entry fun` as `ATTACKER` with no cap |
| Capability leak | Show `ATTACKER` ends the test holding `AdminCap` / `TreasuryCap` they were not given |
| PTB atomic composition | Stay inside **one** `next_tx` and issue several calls (split, borrow, repay). `next_tx` starts a new transaction; PTBs are the calls *between* them |
| Owned-object theft | `take_from_sender` / `take_from_address` after the attacking tx and check the type |

`sui::test_scenario` is in-process. There is no full node and no network.

## Two directions a proof can run

**The bug lets something happen that should not.** Write a test that
*passes* — the attacker succeeds. That passing test is the proof.

**The bug blocks something that should work.** Write a test doing the
legitimate thing and show it aborts. Use `--filter` on that test and
quote the abort code.

Either way, quote the output. A claim of "the test passed" without the
output is not evidence.

## Honest failure

If you cannot build a proof, say why in one line and mark it UNVERIFIED:

- *"their Move.toml pins git deps this image does not have, and rewriting
  a copy still fails to compile"*
- *"this is an Aptos package; the image has no Aptos CLI"*
- *"needs a live oracle / clock object the test harness cannot mock"*
- *"needs two packages to interact and the second is not in scope"*

Do not:

- assert something trivially true and call it a proof
- mark VERIFIED because the code "obviously" has the bug
- rewrite the contract under review to make your test pass

That last one is the subtle failure. **Never modify anything in
`unzipped/`.** If your test only passes after you changed their code, you
have proved a bug in your code, not theirs.

## Minimal mocks are fine

If the module needs a one-off witness or a dummy coin to construct, write
a 20-line `#[test_only]` mock in `poc/` (not in `unzipped/`). That is
setup, not modification. Keep it minimal — a mock that does anything
clever becomes the thing you are testing.
