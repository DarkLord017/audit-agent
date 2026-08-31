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
here for TON FunC/Tact contracts. Original: William Woodruff, ["Brocards for
vulnerability triage"](https://blog.yossarian.net/2026/04/11/Brocards-for-vulnerability-triage)
(2026), and the `vulnerability-triage-brocards` skill in
[trailofbits/skills](https://github.com/trailofbits/skills).

A finding that survives all seven goes to a PoC. One that fails any is
DISPUTED — name the brocard in your report.

---

## 1. No vulnerability without a threat model

The finding must say who the attacker is, what they can do, and what harm
results. "This opcode is unusual" is not a finding.

**Test:** can you complete this sentence from the report alone?

> An attacker with **[capability]** can **[action]** to achieve **[impact]**.

If the impact is not loss of TON/Jettons, loss of access, or corrupted
accounting, ask what it actually costs anyone.

---

## 2. No exploit from the heavens

If the attacker must already hold the power the exploit would grant, there
is no exploit.

**This is the one that kills the most findings in smart contract audits.**
"The owner can drain the vault" is not a bug if the owner can already
`set_jetton_wallet` to their own contract, upgrade the code, or set the
fee to 100%. Centralisation is a design property. It becomes a finding
only when the report shows the privilege exceeds what the docs claim, or
a *non*-privileged actor reaches it.

**Test:** strip the attacker's privileges to the minimum the exploit
needs. Can an ordinary user (any internal-message sender) do this? If it
needs `equal_slices(sender, owner)` / `sender() == self.owner`, dismiss
unless the report argues the owner is not meant to have that reach.

---

## 3. No vulnerability outside of usage

Theoretically reachable is not reachable.

**Test:** is the handler an inbound message path, and does any real path
get there? Check for:

- FunC helpers that are never called from `recv_internal` / `recv_external`
- Tact functions that are not `receive` / `external` / `bounced` / `get`
- code behind a flag never enabled, or a role never granted
- an opcode constant that nothing in the in-scope tree sends
- test contracts and TypeScript wrappers — **out of scope**, and a common
  false positive (`**/test/**`, `**/tests/**`, `**/wrappers/**`)

`recv_internal` is always an entry point. Individual `if (op == …)`
branches are entry points only if some sender can build that body.

---

## 4. No vulnerability from standard behaviour

If the contract correctly implements a specification, the finding belongs
to the spec, not the code.

**Test:** does the Jetton TEP-74, NFT TEP-62, or TON message model require
or permit this? Bounce of value to an uninit account, `fwd_fee` deducted
from `msg_value`, Jetton wallets (not minters) sending
`transfer_notification` — these are the standard behaving as written.

**But:** integrating a Jetton *without* checking the wallet sender is a
real finding in the integrator. The bug is in the assumption, not TEP-74.
Fake notify, integer-as-bool, and unbounded forward amounts are all
plausible for any FunC contract that handles tokens or TON.

FunC `-1`/`0` booleans are spec. Using `1` as true is not.

---

## 5. No vulnerability from documented behaviour

If the project documents the behaviour, including its risk, the finding is
against the docs.

**Test:** does the README, comment, or Tact doc comment say this? "Owner is
trusted", "only the listed Jetton", "not bounce-safe" — all dismiss
findings that assume otherwise.

**But:** remember the docs are the *uploader's* claim. If the code does
not do what the docs say, the gap itself is the finding.

---

## 6. No cure worse than the disease

**Test:** would fixing this cost more than the bug? A rounding loss of one
nanoton per call does not justify breaking the message layout. Note it
and downgrade rather than escalating.

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
| 1 | Fake Jetton notify credits attacker | ACCEPT | — | any sender, no wallet check |
| 2 | Owner can set Jetton wallet | DISPUTED | 2 | owner already controls the vault |
| 3 | Helper `credit_user` has no sender check | DISPUTED | 3 | not an entry point; callers check |
| 4 | `~1` boolean in a getter | DISPUTED | 6 | view-only, no fund loss |

Only ACCEPT rows get a test written.
