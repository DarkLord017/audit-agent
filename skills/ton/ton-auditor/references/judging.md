# Finding Validation

Every finding passes four sequential gates. Fail any gate → **rejected** or **demoted** to lead. Later gates are not evaluated for failed findings.

You are not defending the code. The job of these gates is to verify the attacker's claimed exploit actually fires end-to-end — anything that interrupts the attack between the attacker's message and the harm means the agent's claim does not execute, and only then does it fail to qualify as a finding.

## Gate 1 — Attack execution

Trace the agent's claimed attack path from inbound message to harm. Read every `throw_unless` / `throw_if` / Tact `require`, bounce flag, sender comparison, seqno check, and leftover-slice assertion that sits on that path. Confirm that none of them interrupts the attack before the exploit step fires.
- A specific throw / require / sender check on the attack path interrupts the claimed exploit step before harm occurs (quote the exact line and trace it) → **REJECTED** (or **DEMOTE** if a related code smell remains)
- The supposed interruption is speculative ("probably wouldn't happen", "the sender would notice", "the deployer would set X") → **clears**, continue

## Gate 2 — Reachability

Prove the vulnerable state exists in a live deployment.

- Structurally impossible (enforced invariant prevents it) → **REJECTED**
- Requires privileged actions outside normal operation → **DEMOTE**
- Achievable through normal usage or common Jetton / bounce / external-message behaviors → **clears**, continue

## Gate 3 — Trigger

Prove an unprivileged actor executes the attack.

- Only trusted roles can trigger → **DEMOTE**
- Unprivileged actor triggers profitably → **clears**, continue

**Admin-action findings — reject unless an unprivileged amplifier is named.** This applies ONLY to actions performed by admin/owner, NOT to unprivileged attacker actions. If the harm requires the admin acting maliciously or against documented intent, **REJECT** — do not even emit as a LEAD (stricter than the DEMOTE above). The finding clears only when the body names a concrete unprivileged amplifier:

- **race** — admin sets X mid-flow (e.g. Jetton wallet address); an unprivileged user exploits the window before the update propagates.
- **retroactive sweep** — an admin update rewrites a pending credit already recorded.
- **asymmetric formula** — admin output chains into a formula an unprivileged actor profits from.
- **access gap** — missing sender check, tautological auth, missing seqno on `recv_external`, or uninitialized owner (the access mechanism itself is the bug).

No amplifier named → **REJECTED**. Amplifier named → judge it on that unprivileged path.

## Gate 4 — Impact

Prove material harm to an identifiable victim.

- Self-harm only → **REJECTED**
- Dust-level, no compounding → **DEMOTE**
- Material loss to identifiable victim → **CONFIRMED**

## Confidence

Start at **100**, deduct: partial attack path **-20**, bounded non-compounding impact **-15**, requires specific (but achievable) state **-10**. Confidence ≥ 80 gets description + fix. Below 80 gets description only.

## Safe patterns (do not flag)

- `throw_unless(equal_slices(sender_address, stored_jetton_wallet))` on `transfer_notification` (but verify the stored wallet is actually set and cannot be spoofed).
- FunC boolean `-1` / `0` used with `~`, `&`, `|` (flag `1` used as true).
- Tact `require(sender() == self.jettonWallet)` (same as above).
- Seqno increment **before** `accept_message` on a well-formed `recv_external` (flag missing seqno, increment-after-accept, or replayable externals).
- Two-step admin transfer / delayed Jetton-wallet rotation.
- Consistent protocol-favoring rounding unless compounding or zero-rounding.
- Bounce handlers that only credit when the original outbound was a known op (flag handlers that mint on any bounce).

## Lead promotion

Before finalizing leads, promote where warranted:

- **Cross-contract echo.** Same root cause confirmed as FINDING in one contract → promote in every contract where the identical pattern appears.
- **Multi-agent convergence.** 2+ agents flagged same area, lead was demoted (not rejected) → promote to FINDING at confidence 75.
- **Partial-path completion.** Only weakness is incomplete trace but path is reachable and unguarded → promote to FINDING at confidence 75, description only.

## Leads

High-signal trails for manual investigation. No confidence score, no fix — title, code smells, and what remains unverified.

## Do Not Report

Compiler/linter issues, gas micro-opts, naming, comments. Admin privileges by design. Missing events. Centralization without exploit path. Implausible preconditions (but fake Jetton notify, bounced messages, and replayed `recv_external` ARE plausible on TON).
