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
here for Sui Move packages. Original: William Woodruff, ["Brocards for
vulnerability triage"](https://blog.yossarian.net/2026/04/11/Brocards-for-vulnerability-triage)
(2026), and the `vulnerability-triage-brocards` skill in
[trailofbits/skills](https://github.com/trailofbits/skills).

A finding that survives all seven goes to a PoC. One that fails any is
DISPUTED — name the brocard in your report.

---

## 1. No vulnerability without a threat model

The finding must say who the attacker is, what they can do, and what harm
results. "This `entry fun` is unusual" is not a finding.

**Test:** can you complete this sentence from the report alone?

> An attacker with **[capability]** can **[action]** to achieve **[impact]**.

If the impact is not loss of funds, loss of access, or corrupted
accounting, ask what it actually costs anyone.

---

## 2. No exploit from the heavens

If the attacker must already hold the power the exploit would grant, there
is no exploit.

**This is the one that kills the most findings in Sui audits.**
"The `AdminCap` holder can drain the pool" is not a bug if that capability
is the intended authority: it already lets them take fees, pause, or
upgrade. Centralisation is a design property. It becomes a finding only
when the report shows the privilege exceeds what the docs claim, or a
*non*-privileged actor reaches it.

**Test:** strip the attacker's privileges to the minimum the exploit
needs. Can an ordinary address do this — someone who does not own the
`AdminCap`, `TreasuryCap`, or `UpgradeCap`? If the path requires
`assert!(tx_context::sender(ctx) == admin)` or a typed capability witness
the attacker cannot obtain, dismiss unless the report argues that role is
not meant to have that reach.

Typical DISMISS:

- holder of `AdminCap` sets the fee to 100%
- holder of `UpgradeCap` replaces the package
- owner of a uniquely-owned object transfers it (that is ownership)

Typical ACCEPT:

- a shared-object `entry fun` mutates balances with **no** capability
  check, so any address can call it
- `TreasuryCap` is `share_object`'d, or `public_transfer`'d to a fixed
  address anyone can then use
- a capability with `store` is wrapped into a shared object and a public
  function hands it out

---

## 3. No vulnerability outside of usage

Theoretically reachable is not reachable.

**Test:** is the function an `entry` or `public` entry point, and does any
real path get there? Check for:

- private `fun` / `public(package)` with no `entry` or `public` caller
- a hot-potato type nothing outside the module can construct
- code behind a witness that is never instantiated
- `#[test_only]` modules and `tests/` — **out of scope**, and a common
  false positive

Sui's attacker is an address that builds a programmable transaction
block. They can call every `entry` and `public` function they can supply
arguments for. They cannot call a private function, and they cannot
forge a capability they do not hold.

---

## 4. No vulnerability from standard behaviour

If the package correctly implements a specification, the finding belongs
to the spec, not the code.

**Test:** is this just the Sui object model behaving as written?

- objects with `key` cannot be copied or dropped; `store` allows wrapping
  and `public_transfer`
- `coin::split` / `coin::join` and `sui::balance` arithmetic
- shared vs owned vs frozen is a design choice unless the docs claim
  otherwise
- **PTBs are the execution model.** Combining several calls in one
  transaction (split coin, call, repay, merge) is not a bug. It becomes
  one only when the protocol's invariant assumes those steps cannot be
  atomic — the missing invariant is the finding, not the existence of
  PTBs.

**But:** composing with a coin *without* handling `balance::split` into
dust, or assuming a wrapped object cannot be unpacked, is a real finding
in the integrator. The bug is in the assumption, not the standard.

---

## 5. No vulnerability from documented behaviour

If the project documents the behaviour, including its risk, the finding is
against the docs.

**Test:** does the README, module comment, or a doc comment say this?
"AdminCap is trusted", "shared clock must be passed by the caller",
"not for use with wrapped coins" — all dismiss findings that assume
otherwise.

**But:** remember the docs are the *uploader's* claim. If the code does
not do what the docs say, the gap itself is the finding.

---

## 6. No cure worse than the disease

**Test:** would fixing this cost more than the bug? A rounding loss of one
MIST per swap does not justify breaking composability. Note it and
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
| 1 | Shared vault withdraw has no cap check | ACCEPT | — | any address drains other deposits |
| 2 | AdminCap holder can set fee to 100% | DISPUTED | 2 | AdminCap is the intended authority |
| 3 | Private `fun steal` can mint | DISPUTED | 3 | no entry/public caller |
| 4 | Attacker PTB flash-repays in one tx | DISPUTED | 4 | PTB atomicity is the runtime, not a bug, unless an invariant requires two txs |

Only ACCEPT rows get a test written.
