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
here for Cairo/Starknet contracts. Original: William Woodruff, ["Brocards
for vulnerability triage"](https://blog.yossarian.net/2026/04/11/Brocards-for-vulnerability-triage)
(2026), and the `vulnerability-triage-brocards` skill in
[trailofbits/skills](https://github.com/trailofbits/skills).

A finding that survives all seven goes to a PoC. One that fails any is
DISPUTED — name the brocard in your report.

---

## 1. No vulnerability without a threat model

The finding must say who the attacker is, what they can do, and what harm
results. "This function is unusual" is not a finding.

**Test:** can you complete this sentence from the report alone?

> An attacker with **[capability]** can **[action]** to achieve **[impact]**.

If the impact is not loss of funds, loss of access, or corrupted
accounting, ask what it actually costs anyone.

---

## 2. No exploit from the heavens

If the attacker must already hold the power the exploit would grant, there
is no exploit.

**This is the one that kills the most findings in smart contract audits.**
"The owner can drain the pool" is not a bug if the owner can already
`replace_class_syscall`, upgrade the proxy, or set the fee to 100%.
Centralisation is a design property. It becomes a finding only when the
report shows the privilege exceeds what the docs claim, or a
*non*-privileged actor reaches it.

On Starknet, "the sequencer can reorder / censor / set `block_timestamp`"
is the analogue of "the miner can …". Sequencer trust is a design property
of the chain, not a bug in this contract, unless the report shows the
contract assumed something the sequencer is not bound to (for example
using `get_block_timestamp` as a randomness beacon *and* claiming it is
unbiasable).

**Test:** strip the attacker's privileges to the minimum the exploit
needs. Can an ordinary account do this? If it needs `assert_only_owner`
or a governance role, dismiss unless the report argues that role is not
meant to have that reach. If it needs "be the sequencer", dismiss unless
the contract documented a stronger assumption.

---

## 3. No vulnerability outside of usage

Theoretically reachable is not reachable.

**Test:** is the function externally callable, and does any real path get
there? Check for:

- functions that are not in the contract ABI / not `#[external]` /
  `#[l1_handler]` / constructor, with no external caller
- code behind a flag never enabled, or a role never granted
- a component impl that nothing embeds
- test and mock contracts — **out of scope**, and a common false positive
- `#[cfg(test)]` modules

An `#[l1_handler]` **is** an entry point. "Users cannot call it from L2"
does not dismiss it; any L1 contract can, unless `from_address` is
checked. That is usually ACCEPT, not this brocard.

---

## 4. No vulnerability from standard behaviour

If the contract correctly implements a specification, the finding belongs
to the spec, not the code.

**Test:** does the relevant SNIP / OpenZeppelin component / account
abstraction spec require or permit this? SRC-5 interface ids, SRC-6
signature validation, SNIP-9 outside execution, ERC-20-like Cairo tokens
with no return value on `transfer` — these are the standard behaving as
written.

**But:** integrating a token *without* handling those behaviours is a real
finding in the integrator. The bug is in the assumption, not the standard.
Fee-on-transfer-style tokens are less common on Starknet; what *is*
common is treating `felt252` like a saturating int, or assuming
`u256` overflow panics after a `try_into` that already wrapped.

---

## 5. No vulnerability from documented behaviour

If the project documents the behaviour, including its risk, the finding is
against the docs.

**Test:** does the README, Cairo doc comment, or a comment say this?
"Owner is trusted", "upgrade is instant, no timelock", "L1 bridge is
immutable" — all dismiss findings that assume otherwise.

**But:** remember the docs are the *uploader's* claim. If the code does
not do what the docs say, the gap itself is the finding. A comment that
says `from_address` is checked when the handler never reads it is ACCEPT.

---

## 6. No cure worse than the disease

**Test:** would fixing this cost more than the bug? A rounding loss of one
unit per call does not justify breaking the accounting invariant. Note it
and downgrade rather than escalating. A `felt252` used as a display id
(not a balance) wrapping is usually this brocard, not an overflow finding.

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
| 1 | Unchecked L1 `from_address` mints | ACCEPT | — | any L1 contract credits attacker |
| 2 | Owner can `upgrade` with no delay | DISPUTED | 2 | owner already controls the class hash |
| 3 | Overflow in internal `_accrue` | DISPUTED | 3 | not in ABI, no external caller |

Only ACCEPT rows get a test written.
