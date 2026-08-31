# Finding Validation

Every finding passes four sequential gates. Fail any gate → **rejected** or **demoted** to lead. Later gates are not evaluated for failed findings.

You are not defending the code. The job of these gates is to verify the attacker's claimed exploit actually fires end-to-end — anything that interrupts the attack between the attacker's call and the harm means the agent's claim does not execute, and only then does it fail to qualify as a finding.

## Gate 1 — Attack execution

Trace the agent's claimed attack path from caller to harm. Read every `Assert`, `Txn.on_completion()` branch, group-size check, inner-txn field, and sender comparison that sits on that path. Confirm that none of them interrupts the attack before the exploit step fires.
- A specific Assert / OnComplete / group-size check on the attack path interrupts the claimed exploit step before harm occurs (quote the exact line and trace it) → **REJECTED** (or **DEMOTE** if a related code smell remains)
- The supposed interruption is speculative ("probably wouldn't happen", "the caller would notice", "the creator would set X") → **clears**, continue

## Gate 2 — Reachability

Prove the vulnerable state exists in a live deployment.

- Structurally impossible (enforced invariant prevents it) → **REJECTED**
- Requires privileged actions outside normal operation → **DEMOTE**
- Achievable through normal usage, extra group transactions, ClearState, or common ASA behaviours (not opted-in, clawback set, default frozen) → **clears**, continue

## Gate 3 — Trigger

Prove an unprivileged actor executes the attack.

- Only trusted roles can trigger → **DEMOTE**
- Unprivileged actor triggers profitably → **clears**, continue

**Admin-action findings — reject unless an unprivileged amplifier is named.** This applies ONLY to actions performed by creator/admin, NOT to unprivileged attacker actions. If the harm requires the creator acting maliciously or against documented intent, **REJECT** — do not even emit as a LEAD (stricter than the DEMOTE above). The finding clears only when the body names a concrete unprivileged amplifier:

- **race** — admin sets X mid-flow; an unprivileged user exploits the window before the update propagates.
- **retroactive sweep** — an admin update rewrites a pending value already credited.
- **asymmetric formula** — admin output chains into a formula an unprivileged actor profits from.
- **access gap** — missing `Txn.sender() == Global.creator_address()`, tautological auth, or `UpdateApplication` / `DeleteApplication` returning 1 (the access mechanism itself is the bug).

No amplifier named → **REJECTED**. Amplifier named → judge it on that unprivileged path.

## Gate 4 — Impact

Prove material harm to an identifiable victim.

- Self-harm only → **REJECTED**
- Dust-level, no compounding → **DEMOTE**
- Material loss to identifiable victim (account drained, rekeyed, ASA seized, app deleted, state cleared under other users) → **CONFIRMED**

## Confidence

Start at **100**, deduct: partial attack path **-20**, bounded non-compounding impact **-15**, requires specific (but achievable) state **-10**. Confidence ≥ 80 gets description + fix. Below 80 gets description only.

## Safe patterns (do not flag)

- `Assert(Txn.rekey_to() == Global.zero_address())` on every approving path (but verify it is on ALL paths, including inner txns and every Gtxn index).
- `Assert(Txn.close_remainder_to() == Global.zero_address())` / `Assert(Txn.asset_close_to() == Global.zero_address())` on payment / axfer paths.
- `Assert(Global.group_size() == Int(N))` paired with absolute `Gtxn[i]` indexes.
- ABI `@router.method` relative indexing (Teal v6+) when group size is still bounded.
- `TxnField.fee: Int(0)` on every inner transaction.
- `UpdateApplication` / `DeleteApplication` gated by `Txn.sender() == Global.creator_address()`, or explicitly `Return(Int(0))`.
- `Gtxn[i].on_completion() == OnComplete.NoOp` next to every `ApplicationCall` type check.

## Lead promotion

Before finalizing leads, promote where warranted:

- **Cross-contract echo.** Same root cause confirmed as FINDING in one contract → promote in every contract where the identical pattern appears.
- **Multi-agent convergence.** 2+ agents flagged same area, lead was demoted (not rejected) → promote to FINDING at confidence 75.
- **Partial-path completion.** Only weakness is incomplete trace but path is reachable and unguarded → promote to FINDING at confidence 75, description only.

## Leads

High-signal trails for manual investigation. No confidence score, no fix — title, code smells, and what remains unverified.

## Do Not Report

Compiler/assembler issues, opcode micro-opts, naming, comments. Creator privileges by design. Missing logs. Centralization without exploit path. The protocol min-balance of 0.1 ALGO as a design property unless it is used as a DoS or drain. Implausible preconditions (but extra group slots, ClearState instead of NoOp, unset RekeyTo, and not-opted-in ASA accounts ARE plausible).
