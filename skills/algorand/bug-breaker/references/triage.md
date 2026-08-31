<!--
Adapted from the vulnerability-triage-brocards skill in trailofbits/skills,
which is licensed CC-BY-SA-4.0. This file is therefore also CC-BY-SA-4.0.
Original: William Woodruff, "Brocards for vulnerability triage" (2026).
See ../ATTRIBUTION.md.
-->

# Triage: killing findings before you spend a test on them

Seven falsifiable tests. Apply them in order to each finding. Stop at the
first DISMISS.

These are the vulnerability-triage brocards from Trail of Bits, adapted
here for Algorand (TEAL / PyTeal). Original: William Woodruff, ["Brocards
for vulnerability triage"](https://blog.yossarian.net/2026/04/11/Brocards-for-vulnerability-triage)
(2026), and the `vulnerability-triage-brocards` skill in
[trailofbits/skills](https://github.com/trailofbits/skills).

A finding that survives all seven goes to a PoC. One that fails any is
DISPUTED — name the brocard in your report.

---

## 1. No vulnerability without a threat model

The finding must say who the attacker is, what they can do, and what harm
results. "This ABI method is unusual" is not a finding.

**Test:** can you complete this sentence from the report alone?

> An attacker with **[capability]** can **[action]** to achieve **[impact]**.

If the impact is not loss of ALGO/ASA, loss of account auth (rekey), or
corrupted app state, ask what it actually costs anyone.

---

## 2. No exploit from the heavens

If the attacker must already hold the power the exploit would grant, there
is no exploit.

**This is the one that kills the most findings in smart contract audits.**
"The creator can drain the app account" is not a bug if the creator can
already `UpdateApplication`, `DeleteApplication`, or is the ASA clawback
address. Centralisation is a design property. It becomes a finding only
when the report shows the privilege exceeds what the docs claim, or a
*non*-privileged actor reaches it.

**Test:** strip the attacker's privileges to the minimum the exploit
needs. Can an ordinary sender / lsig user do this? If it needs
`Txn.sender() == Global.creator_address()`, dismiss unless the report
argues the creator is not meant to have that reach (e.g. UpdateApplication
is documented as disabled but returns 1).

---

## 3. No vulnerability outside of usage

Theoretically reachable is not reachable.

**Test:** is the path an approval NoOp, an OnComplete the program actually
allows, or a logic sig that will be signed? Check for:

- PyTeal `@Subroutine` / internal `def` with no ABI / OnComplete caller
- code behind an OnComplete arm that `Return(Int(0))`
- a clear-state program "bug" that only hurts the user who opts out
  (self-harm) unless it corrupts *global* accounting
- test and mock contracts — **out of scope**, and a common false positive
  (`**/test/**`, `**/tests/**`, `test_*.py`)

Tealer's `human-summary` / `transaction-context` printers help. See
[tealer.md](tealer.md).

---

## 4. No vulnerability from standard behaviour

If the program correctly implements Algorand's rules, the finding belongs
to the protocol, not the code.

**Test:** is this just how Algorand works? Users can always ClearState
their local state. Accounts need min-balance. ASA transfers require
opt-in. Inner txns spend from the application account. These are the
platform behaving as written.

**But:** an app that *assumes* ClearState cannot happen, or that pushes
ASAs without handling opt-in failure, is a real finding in the app. The
bug is in the assumption, not the protocol. Extra group slots, unset
RekeyTo, and ClearState-as-ApplicationCall ARE plausible attacker moves.

---

## 5. No vulnerability from documented behaviour

If the project documents the behaviour, including its risk, the finding is
against the docs.

**Test:** does the README or a comment say this? "Creator is trusted",
"clawback remains with the issuer", "this lsig is single-use via lease"
— all dismiss findings that assume otherwise.

**But:** remember the docs are the *uploader's* claim. If the code does
not do what the docs say (UpdateApplication open while README says
immutable), the gap itself is the finding.

---

## 6. No cure worse than the disease

**Test:** would fixing this cost more than the bug? A rounding loss of one
microAlgo per claim does not justify breaking the ABI. Note it and
downgrade rather than escalating.

---

## 7. The report is neither necessary nor sufficient

A confidence score of 95 from the previous stage is an opinion, not
evidence. Strip the number and the confident tone. Does the technical
description alone justify a test?

**Test:** would you still believe this if it were scored 40? If yes, the
score was never doing the work. If no, the score was doing all of it —
dismiss, or demand the mechanism.

---

## Recording it

One row per finding. Keep it short — this is the cheap stage.

| # | Finding | Verdict | Brocard | Reasoning |
|---|---|---|---|---|
| 1 | Missing RekeyTo on lsig | ACCEPT | — | any payment rekeys the escrow |
| 2 | Creator can UpdateApplication | DISPUTED | 2 | creator already controls the app |
| 3 | ClearState does not debit local | DISPUTED | 3 | local-only, user opts themselves out |
| 4 | No inner-txn logs | DISPUTED | 4 | Algorand has no required event ABI |

Only ACCEPT rows get a test written.
