# Writing a proof

A proof is a test that **fails, or succeeds, only because the bug is real**.
If the test would behave the same on correct code, it proves nothing.

There is no algod in this container. Do not try to submit transactions.
A proof here is a **pytest** that compiles the program (PyTeal → TEAL)
and demonstrates the claimed hole: missing field check in the compiled
TEAL, a predicate that returns 1 for an attacker txn, or Tealer on that
TEAL plus an assertion that names the harm.

## The shape

One test per finding. Name it after the finding. Fence language is
`python`.

```python
from pathlib import Path
import importlib.util

from pyteal import compileTeal, Mode, Seq, Assert, Txn, Global, Int, Approve

UNZIPPED = Path("/work/unzipped")  # or the unzipped fixture from conftest


def _load_approval():
    """Import their PyTeal module from unzipped/ without mutating it."""
    path = UNZIPPED / "approval.py"
    spec = importlib.util.spec_from_file_location("approval", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.approval_program()  # whatever they named it


def test_approval_missing_rekey_to_check(tmp_path):
    # 1. ARRANGE - compile their program, not a rewrite of it
    teal = compileTeal(_load_approval(), mode=Mode.Application, version=8)
    (tmp_path / "approval.teal").write_text(teal)

    # 2. ACT - the attacker field the finding claims is unchecked
    # Compiled TEAL must mention rekey on every approving path. A program
    # that never loads RekeyTo cannot reject a rekeying payment.
    has_rekey_check = (
        "RekeyTo" in teal or "rekey_to" in teal.lower()
    )

    # 3. ASSERT - the harm: takeover is possible because the check is absent
    assert not has_rekey_check, "finding claimed missing RekeyTo, but TEAL checks it"
```

If `poc/conftest.py` already defines `UNZIPPED`, import that (or use the
`unzipped` fixture) instead of hardcoding the path.

For raw `.teal` uploads, skip compile and read the file:

```python
def test_lsig_missing_close_remainder_to(unzipped):
    teal = (unzipped / "escrow.teal").read_text()
    assert "CloseRemainderTo" not in teal
```

Verified working in this container looks like:

```
poc/tests/test_rekey.py::test_approval_missing_rekey_to_check PASSED
```

## The three parts, always

**Arrange** — compile *their* program (or load their TEAL). Do not
reimplement the bug in a toy PyTeal snippet and "prove" the toy.

**Act** — do exactly what the finding claims: inspect the compiled TEAL
for the missing field, or evaluate a thin Python predicate that mirrors
their Asserts against an attacker txn dict (RekeyTo set, GroupSize=16,
OnComplete=ClearState).

**Assert** — assert the *harm*, not the mechanism. "TEAL never loads
RekeyTo, so a payment with RekeyTo=attacker is approved" is a proof.
"the file imported" is not.

When you can, run Tealer on the compiled file and quote the detector
next to the pytest (see [tealer.md](tealer.md)). Tealer agreeing is
support, not the proof.

## Two directions a proof can run

**The bug lets something happen that should not.** Write a test that
*passes* — the attacker condition is accepted. That passing test is
the proof.

**The bug blocks something that should work.** Write a test of the
legitimate path and show it is rejected (or compile fails closed).
Quote the pytest output.

Either way, quote the output. A claim of "the test passed" without the
output is not evidence.

## Honest failure

If you cannot build a proof, say why in one line and mark it UNVERIFIED:

- *"needs algod / sandbox to dryrun a group, not in this image"*
- *"PyTeal compile fails on a missing helper not in the tree"*
- *"Beaker app needs network compile, cannot run offline"*
- *"finding is in a client script, not a program"*

Do not:

- assert something trivially true and call it a proof
- mark VERIFIED because the code "obviously" has the bug
- rewrite the contract under review to make your test pass
- mark VERIFIED from Tealer alone

That last-but-one is the subtle failure. **Never modify anything in
`unzipped/`.** If your test only passes after you changed their code, you
have proved a bug in your code, not theirs.

## Minimal mocks are fine

If their `approval_program()` needs constants, set them in the test
file. If compile needs a tiny stub of a helper they import, write the
stub under `poc/` (not `unzipped/`). Keep it minimal — a stub that
does anything clever becomes the thing you are testing.

Write tests under `poc/tests/` if they shipped no pytest project, or
into their existing tests directory if they did. Never under `unzipped/`.
