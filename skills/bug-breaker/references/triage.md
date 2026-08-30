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
here for smart contracts. Original: William Woodruff, ["Brocards for
vulnerability triage"](https://blog.yossarian.net/2026/04/11/Brocards-for-vulnerability-triage)
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
`selfdestruct`, upgrade the proxy, or set the fee to 100%. Centralisation
is a design property. It becomes a finding only when the report shows the
privilege exceeds what the docs claim, or a *non*-privileged actor reaches it.

**Test:** strip the attacker's privileges to the minimum the exploit
needs. Can an ordinary user do this? If it needs `onlyOwner`, dismiss
unless the report argues the owner is not meant to have that reach.

---

## 3. No vulnerability outside of usage

Theoretically reachable is not reachable.

**Test:** is the function externally callable, and does any real path get
there? Check for:

- `internal`/`private` with no external caller
- code behind a flag never enabled, or a role never granted
- an abstract contract or interface that nothing implements
- test and mock contracts — **out of scope**, and a common false positive

Slither's `entry-points` printer answers most of this. See
[slither.md](slither.md).

---

## 4. No vulnerability from standard behaviour

If the contract correctly implements a specification, the finding belongs
to the spec, not the code.

**Test:** does ERC20/ERC721/ERC4626 require or permit this? Approval
race, no return value on `transfer`, rebasing balances — these are the
standard behaving as written.

**But:** integrating a token *without* handling those behaviours is a real
finding in the integrator. The bug is in the assumption, not the standard.
Fee-on-transfer, rebasing and blacklisting tokens are all plausible for
any contract accepting arbitrary ERC20s.

---

## 5. No vulnerability from documented behaviour

If the project documents the behaviour, including its risk, the finding is
against the docs.

**Test:** does the README, NatSpec, or a comment say this? "Owner is
trusted", "only whitelisted tokens", "not for use with rebasing tokens" —
all dismiss findings that assume otherwise.

**But:** remember the docs are the *uploader's* claim. If the code does
not do what the docs say, the gap itself is the finding.

---

## 6. No cure worse than the disease

**Test:** would fixing this cost more than the bug? A rounding loss of one
wei per call does not justify breaking composability. Note it and
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
| 1 | Unprotected withdraw | ACCEPT | — | any EOA drains other deposits |
| 2 | Owner can set fee to 100% | DISPUTED | 2 | owner already controls upgrades |
| 3 | Reentrancy in `_sweep` | DISPUTED | 3 | `internal`, no external caller |

Only ACCEPT rows get a test written.
