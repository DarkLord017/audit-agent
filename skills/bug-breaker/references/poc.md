# Writing a proof

A proof is a test that **fails, or succeeds, only because the bug is real**.
If the test would behave the same on correct code, it proves nothing.

## The shape

One test per finding. Name it after the finding.

```solidity
pragma solidity ^0.8.20;

import "forge-std/Test.sol";
import "unzipped/Vault.sol";       // or their remapping

contract VaultDrainTest is Test {
    Vault v;

    function setUp() public {
        v = new Vault();
    }

    function test_attacker_drains_other_users_deposit() public {
        // 1. ARRANGE - a victim with something to lose
        address victim = makeAddr("victim");
        vm.deal(victim, 10 ether);
        vm.prank(victim);
        v.deposit{value: 10 ether}();

        // 2. ACT - the attacker does the thing the finding claims
        address attacker = makeAddr("attacker");
        vm.prank(attacker);
        v.withdraw(attacker, 10 ether);

        // 3. ASSERT - the harm, in numbers
        assertEq(attacker.balance, 10 ether, "attacker took the victim's deposit");
        assertEq(address(v).balance, 0, "vault drained");
    }
}
```

Verified working in this container:

```
[PASS] test_anyone_can_drain() (gas: 89950)
```

## The three parts, always

**Arrange** — set up a state where there is something real to lose. A bug
that only "works" on an empty contract usually is not one.

**Act** — do exactly what the finding claims an attacker can do. Use
`vm.prank` so the caller is unmistakably not the owner.

**Assert** — assert the *harm*, not the mechanism. `attacker.balance ==
10 ether` is a proof. `withdraw did not revert` is not — plenty of
harmless functions do not revert.

## Cheatcodes you will need

| Cheatcode | Use |
|---|---|
| `vm.prank(a)` | next call comes from `a` |
| `vm.startPrank(a)` / `vm.stopPrank()` | several calls from `a` |
| `vm.deal(a, n)` | give `a` some ether |
| `makeAddr("name")` | a labelled address, readable in traces |
| `vm.expectRevert(...)` | prove something *should* fail and does not |
| `vm.warp(t)` / `vm.roll(n)` | move time or blocks |
| `vm.expectEmit(...)` | assert on events |

## Two directions a proof can run

**The bug lets something happen that should not.** Write a test that
*passes* — the attacker succeeds. That passing test is the proof.

**The bug blocks something that should work.** Write a test doing the
legitimate thing and show it reverts. Use `-vvv` and quote the revert.

Either way, quote the output. A claim of "the test passed" without the
output is not evidence.

## Honest failure

If you cannot build a proof, say why in one line and mark it UNVERIFIED:

- *"their `lib/` is empty, the contract does not compile"*
- *"needs a live price oracle, cannot fork with no network"*
- *"needs two contracts to interact and the second is not in scope"*

Do not:

- assert something trivially true and call it a proof
- mark VERIFIED because the code "obviously" has the bug
- rewrite the contract under review to make your test pass

That last one is the subtle failure. **Never modify anything in
`unzipped/`.** If your test only passes after you changed their code, you
have proved a bug in your code, not theirs.

## Minimal mocks are fine

If the contract needs an ERC20 to construct, write a 15-line mock in your
test file. That is setup, not modification. Keep it minimal — a mock that
does anything clever becomes the thing you are testing.
