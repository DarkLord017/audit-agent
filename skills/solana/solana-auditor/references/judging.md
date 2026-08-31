# Finding Validation

Every finding passes four sequential gates. Fail any gate → **rejected** or **demoted** to lead. Later gates are not evaluated for failed findings.

You are not defending the code. The job of these gates is to verify the attacker's claimed exploit actually fires end-to-end — anything that interrupts the attack between the attacker's call and the harm means the agent's claim does not execute, and only then does it fail to qualify as a finding.

## Gate 1 — Attack execution

Trace the agent's claimed attack path from caller to harm. Read every account constraint (`Signer`, `Account<'info, T>`, `seeds`/`bump`, `has_one`, `address =`), native check (`is_signer`, `owner ==`, `key ==`), and `require!` that sits on that path. Confirm that none of them interrupts the attack before the exploit step fires.
- A specific constraint / signer / owner / PDA check on the attack path interrupts the claimed exploit step before harm occurs (quote the exact line and trace it) → **REJECTED** (or **DEMOTE** if a related code smell remains)
- The supposed interruption is speculative ("probably wouldn't happen", "the caller would notice", "the upgrade authority would set X") → **clears**, continue

## Gate 2 — Reachability

Prove the vulnerable state exists in a live deployment.

- Structurally impossible (enforced invariant prevents it) → **REJECTED**
- Requires privileged actions outside normal operation → **DEMOTE**
- Achievable through normal usage or common token/account behaviors → **clears**, continue

## Gate 3 — Trigger

Prove an unprivileged actor executes the attack.

- Only trusted roles can trigger → **DEMOTE**
- Unprivileged actor triggers profitably → **clears**, continue

**Admin-action findings — reject unless an unprivileged amplifier is named.** This applies ONLY to actions performed by admin/upgrade-authority/PDA-authority, NOT to unprivileged attacker actions. If the harm requires the admin acting maliciously or against documented intent, **REJECT** — do not even emit as a LEAD (stricter than the DEMOTE above). The finding clears only when the body names a concrete unprivileged amplifier:

- **race** — admin sets X mid-flow; an unprivileged user exploits the window before the update propagates.
- **retroactive sweep** — an admin update rewrites a pending value already credited.
- **asymmetric formula** — admin output chains into a formula an unprivileged actor profits from.
- **access gap** — missing `is_signer`, tautological auth, `/// CHECK:` without a real check, or missing init guard (the access mechanism itself is the bug).

No amplifier named → **REJECTED**. Amplifier named → judge it on that unprivileged path.

## Gate 4 — Impact

Prove material harm to an identifiable victim.

- Self-harm only → **REJECTED**
- Dust-level, no compounding → **DEMOTE**
- Material loss to identifiable victim → **CONFIRMED**

## Confidence

Start at **100**, deduct: partial attack path **-20**, bounded non-compounding impact **-15**, requires specific (but achievable) state **-10**. Confidence ≥ 80 gets description + fix. Below 80 gets description only.

## Safe patterns (do not flag)

- Anchor `Account<'info, T>` / `Program<'info, T>` / `Signer<'info>` (verify the constraint is actually on the account being trusted).
- Anchor `seeds = [...], bump` (canonical bump) when the seeds match the stored identity.
- `load_instruction_at_checked` / `load_current_index_checked` on Solana ≥ 1.8.1 when the sysvar address is also constrained.
- Stored canonical bump reused in `invoke_signed` (not a user-supplied bump).
- Two-step authority transfer.
- Consistent protocol-favoring rounding unless compounding or zero-rounding.

## Lead promotion

Before finalizing leads, promote where warranted:

- **Cross-contract echo.** Same root cause confirmed as FINDING in one program → promote in every program where the identical pattern appears.
- **Multi-agent convergence.** 2+ agents flagged same area, lead was demoted (not rejected) → promote to FINDING at confidence 75.
- **Partial-path completion.** Only weakness is incomplete trace but path is reachable and unguarded → promote to FINDING at confidence 75, description only.

## Leads

High-signal trails for manual investigation. No confidence score, no fix — title, code smells, and what remains unverified.

## Do Not Report

Linter/compiler issues, compute-unit micro-opts, naming, rustdoc. Admin privileges by design. Missing events. Centralization without exploit path. Implausible preconditions (but fee-on-transfer, Token-2022 transfer hooks, and freeze authority ARE plausible for programs accepting arbitrary mints).
