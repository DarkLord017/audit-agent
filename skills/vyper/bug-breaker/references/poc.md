# Writing a proof

A proof is a test that **fails, or succeeds, only because the bug is real**.
If the test would behave the same on correct code, it proves nothing.

## The shape

One test per finding. Name it after the finding.

```python
import boa
from pathlib import Path

# Scaffolded poc/conftest.py defines UNZIPPED; /work/unzipped is the same tree.
UNZIPPED = Path("/work/unzipped")


def test_attacker_drains_other_users_deposit():
    vault = boa.load(str(UNZIPPED / "Vault.vy"))

    # 1. ARRANGE - a victim with something to lose
    victim = boa.env.generate_address("victim")
    boa.env.set_balance(victim, 10 * 10**18)
    with boa.env.prank(victim):
        vault.deposit(value=10 * 10**18)

    # 2. ACT - the attacker does the thing the finding claims
    attacker = boa.env.generate_address("attacker")
    with boa.env.prank(attacker):
        vault.withdraw(attacker, 10 * 10**18)

    # 3. ASSERT - the harm, in numbers
    assert boa.env.get_balance(attacker) == 10 * 10**18
    assert boa.env.get_balance(vault.address) == 0
```

If `poc/conftest.py` already defines `UNZIPPED`, import that (or use the
`unzipped` fixture) instead of hardcoding the path.

Verified working in this container looks like:

```
poc/tests/test_drain.py::test_attacker_drains_other_users_deposit PASSED
```

## The three parts, always

**Arrange** — set up a state where there is something real to lose. A bug
that only "works" on an empty contract usually is not one.

**Act** — do exactly what the finding claims an attacker can do. Use
`boa.env.prank` so the caller is unmistakably not the owner.

**Assert** — assert the *harm*, not the mechanism. `get_balance(attacker)
== 10 ether` is a proof. `withdraw did not revert` is not — plenty of
harmless functions do not revert.

## Cheatcodes you will need

| Call | Use |
|---|---|
| `boa.env.prank(a)` | context manager: calls come from `a` |
| `boa.env.generate_address("name")` | a labelled address, readable in traces |
| `boa.env.set_balance(a, n)` | give `a` some ether |
| `boa.env.get_balance(a)` | read ether balance |
| `boa.reverts()` / `boa.reverts("msg")` | prove something *should* fail and does not |
| `boa.env.time_travel(seconds=n)` | move time |

`@nonreentrant` bugs need a callback contract. Load a tiny attacker `.vy`
from your test file (write it under `poc/`, **not** under `unzipped/`)
that `raw_call`s back into the vault mid-withdraw.

## Two directions a proof can run

**The bug lets something happen that should not.** Write a test that
*passes* — the attacker succeeds. That passing test is the proof.

**The bug blocks something that should work.** Write a test doing the
legitimate thing and show it reverts. Use `-vv` and quote the revert
(`with boa.reverts():` inverted — the legitimate call *does* raise).

Either way, quote the output. A claim of "the test passed" without the
output is not evidence.

## Honest failure

If you cannot build a proof, say why in one line and mark it UNVERIFIED:

- *"their imports an interface that is not in the tree, `boa.load` fails"*
- *"needs a live price oracle, cannot fork with no network"*
- *"needs two contracts to interact and the second is not in scope"*
- *"pragma wants a Vyper version not in this image"*

Do not:

- assert something trivially true and call it a proof
- mark VERIFIED because the code "obviously" has the bug
- rewrite the contract under review to make your test pass

That last one is the subtle failure. **Never modify anything in
`unzipped/`.** If your test only passes after you changed their code, you
have proved a bug in your code, not theirs.

## Minimal mocks are fine

If the contract needs an ERC20 to construct, write a 15-line Vyper mock
in `poc/` (not in `unzipped/`) and `boa.load` it. That is setup, not
modification. Keep it minimal — a mock that does anything clever becomes
the thing you are testing.
