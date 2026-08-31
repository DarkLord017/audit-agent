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
here for Cosmos SDK modules and CosmWasm contracts. Original: William
Woodruff, ["Brocards for vulnerability triage"](https://blog.yossarian.net/2026/04/11/Brocards-for-vulnerability-triage)
(2026), and the `vulnerability-triage-brocards` skill in
[trailofbits/skills](https://github.com/trailofbits/skills).

A finding that survives all seven goes to a PoC. One that fails any is
DISPUTED — name the brocard in your report.

---

## 1. No vulnerability without a threat model

The finding must say who the attacker is, what they can do, and what harm
results. "This keeper method is unusual" is not a finding.

**Test:** can you complete this sentence from the report alone?

> An attacker with **[capability]** can **[action]** to achieve **[impact]**.

If the impact is not loss of funds, loss of access, corrupted accounting,
or consensus failure (chain halt / state divergence), ask what it actually
costs anyone.

---

## 2. No exploit from the heavens

If the attacker must already hold the power the exploit would grant, there
is no exploit.

**This is the one that kills the most findings in Cosmos audits.**
"The module authority can drain the module account" is not a bug if that
authority can already `MsgUpdateParams`, migrate the CosmWasm contract, or
pass a governance proposal that does the same. Centralisation is a design
property. It becomes a finding only when the report shows the privilege
exceeds what the docs claim, or a *non*-privileged actor reaches it.

**Test:** strip the attacker's privileges to the minimum the exploit
needs. Can an ordinary user, an arbitrary IBC counterparty, or an
unprivileged CosmWasm `info.sender` do this? If it needs the x/gov
authority or the wasm admin, dismiss unless the report argues that role
is not meant to have that reach.

---

## 3. No vulnerability outside of usage

Theoretically reachable is not reachable.

**Test:** is the function on a consensus-critical path, and does any real
path get there? Check for:

- unexported keeper helpers with no Msg / ABCI / IBC caller
- CLI, query, gRPC-gateway, REST — **not consensus**, not a chain-halt bug
- code behind a flag never enabled, or a role never granted
- an interface that nothing implements
- test and mock packages — **out of scope**, and a common false positive
- CosmWasm `#[cfg(test)]` or `src/multitest` helpers

A panic in a query handler does not halt the chain. A map iteration in a
CLI command is not a consensus bug.

---

## 4. No vulnerability from standard behaviour

If the module correctly implements a specification, the finding belongs
to the spec, not the code.

**Test:** does the Cosmos SDK / ibc-go / CosmWasm spec require or permit
this? ICS-20 voucher mint on recv, governance being able to change params,
CosmWasm `info.sender` being the direct caller — these are the standard
behaving as written.

**But:** integrating a spec *without* handling those behaviours is a real
finding in the integrator. The bug is in the assumption, not the standard.
Fee-on-transfer via wasm hooks, IBC denom traces, and tokenfactory denoms
are all plausible for any module that accepts arbitrary denoms.

---

## 5. No vulnerability from documented behaviour

If the project documents the behaviour, including its risk, the finding is
against the docs.

**Test:** does the README, proto comment, or a comment say this? "Authority
is trusted", "permissioned wasm uploads", "not for use with IBC denoms" —
all dismiss findings that assume otherwise.

**But:** remember the docs are the *uploader's* claim. If the code does
not do what the docs say, the gap itself is the finding.

---

## 6. No cure worse than the disease

**Test:** would fixing this cost more than the bug? A rounding loss of one
uatom per call does not justify breaking the module. Note it and
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
| 1 | Unprotected MsgWithdraw | ACCEPT | — | any user drains other deposits |
| 2 | Authority can set fee to 100% | DISPUTED | 2 | authority already controls params |
| 3 | Panic in query handler | DISPUTED | 3 | query is not consensus-critical |
| 4 | Map iteration in BeginBlocker | ACCEPT | — | non-deterministic state root |

Only ACCEPT rows get a test written.
