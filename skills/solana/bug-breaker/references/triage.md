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
here for Solana programs. Original: William Woodruff, ["Brocards for
vulnerability triage"](https://blog.yossarian.net/2026/04/11/Brocards-for-vulnerability-triage)
(2026), and the `vulnerability-triage-brocards` skill in
[trailofbits/skills](https://github.com/trailofbits/skills).

A finding that survives all seven goes to a PoC. One that fails any is
DISPUTED — name the brocard in your report.

---

## 1. No vulnerability without a threat model

The finding must say who the attacker is, what they can do, and what harm
results. "This instruction is unusual" is not a finding.

**Test:** can you complete this sentence from the report alone?

> An attacker with **[capability]** can **[action]** to achieve **[impact]**.

If the impact is not loss of funds, loss of access, or corrupted
accounting, ask what it actually costs anyone.

---

## 2. No exploit from the heavens

If the attacker must already hold the power the exploit would grant, there
is no exploit.

**This is the one that kills the most findings in Solana audits.**
"The upgrade authority can drain the vault" is not a bug if that key can
already `bpf_loader_upgradeable::set_upgrade_authority` or close the
program. "The stored `admin` PDA authority can set the fee to 100%" is
not a bug if the docs say that key is trusted. Centralisation is a design
property. It becomes a finding only when the report shows the privilege
exceeds what the docs claim, or a *non*-privileged actor reaches it
(missing `is_signer`, spoofable PDA, unconstrained `UncheckedAccount`).

**Test:** strip the attacker's privileges to the minimum the exploit
needs. Can an ordinary wallet do this? If it needs the upgrade authority
or the documented admin, dismiss unless the report argues that role is
not meant to have that reach.

---

## 3. No vulnerability outside of usage

Theoretically reachable is not reachable.

**Test:** is the instruction an entry point, and does any real path get
there? Check for:

- `pub(crate)` / private helpers with no instruction dispatcher arm
- code behind a feature flag never enabled, or a role never granted
- Anchor `#[access_control]` / `constraint` that always fails on the
  claimed path
- test, mock, and `target/` sources — **out of scope**, and a common
  false positive

If the only caller is `#[cfg(test)]`, dismiss.

---

## 4. No vulnerability from standard behaviour

If the program correctly implements a specification, the finding belongs
to the spec, not the code.

**Test:** does SPL Token / Token-2022 / associated-token / the System
program require or permit this? Approval-then-transfer races, Token-2022
transfer fees when the mint has that extension advertised, rent-exempt
minimums — these are the platform behaving as written.

**But:** integrating a mint *without* handling those behaviours is a real
finding in the integrator. The bug is in the assumption, not the token
program. Transfer fees, transfer hooks, freeze, and non-standard decimals
are all plausible for any program accepting arbitrary mints.

---

## 5. No vulnerability from documented behaviour

If the project documents the behaviour, including its risk, the finding is
against the docs.

**Test:** does the README, crate docs, or a comment say this? "Admin is
trusted", "only the canonical vault PDA", "not for use with Token-2022"
— all dismiss findings that assume otherwise.

**But:** remember the docs are the *uploader's* claim. If the code does
not do what the docs say (seeds don't match the documented PDA, admin
is not actually a `Signer`), the gap itself is the finding.

---

## 6. No cure worse than the disease

**Test:** would fixing this cost more than the bug? A rounding loss of one
token unit per call does not justify breaking the share-price formula.
Note it and downgrade rather than escalating.

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
| 1 | Withdraw without is_signer | ACCEPT | — | any EOA passes the authority pubkey unsigned |
| 2 | Upgrade authority can set fee 100% | DISPUTED | 2 | that key already upgrades the program |
| 3 | Helper deserialize lacks owner check | DISPUTED | 3 | `pub(crate)`, only called after Account::try_from |

Only ACCEPT rows get a test written.
