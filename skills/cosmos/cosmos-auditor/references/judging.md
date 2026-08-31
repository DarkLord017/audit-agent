# Finding Validation

Every finding passes four sequential gates. Fail any gate → **rejected** or **demoted** to lead. Later gates are not evaluated for failed findings.

You are not defending the code. The job of these gates is to verify the attacker's claimed exploit actually fires end-to-end — anything that interrupts the attack between the attacker's call and the harm means the agent's claim does not execute, and only then does it fail to qualify as a finding.

## Gate 1 — Attack execution

Trace the agent's claimed attack path from caller to harm. Read every guard, check, `ValidateBasic` / `Validate` / ante decorator, keeper invariant, and CosmWasm `if` that sits on that path. Confirm that none of them interrupts the attack before the exploit step fires.
- A specific guard on the attack path interrupts the claimed exploit step before harm occurs (quote the exact line and trace it) → **REJECTED** (or **DEMOTE** if a related code smell remains)
- The supposed interruption is speculative ("probably wouldn't happen", "governance would notice", "the authority would set X") → **clears**, continue
- CLI / query / gRPC-gateway-only code with no consensus-path caller → **REJECTED**

## Gate 2 — Reachability

Prove the vulnerable state exists in a live chain or instantiated contract.

- Structurally impossible (enforced invariant prevents it) → **REJECTED**
- Requires privileged actions outside normal operation (authority message, genesis-only) → **DEMOTE**
- Achievable through normal usage, IBC packets, CosmWasm execute, or common token/denom behaviors → **clears**, continue

## Gate 3 — Trigger

Prove an unprivileged actor executes the attack.

- Only trusted roles (module authority, governance, chain-admin) can trigger → **DEMOTE**
- Unprivileged actor triggers profitably (any IBC counterparty, any CosmWasm `info.sender`, any user Msg) → **clears**, continue

**Authority-action findings — reject unless an unprivileged amplifier is named.** This applies ONLY to actions performed by module authority / governance, NOT to unprivileged attacker actions. If the harm requires the authority acting maliciously or against documented intent, **REJECT** — do not even emit as a LEAD (stricter than the DEMOTE above). The finding clears only when the body names a concrete unprivileged amplifier:

- **race** — authority sets a param mid-flow; an unprivileged user exploits the window.
- **retroactive sweep** — a param update rewrites a pending value already credited.
- **asymmetric formula** — authority output chains into a formula an unprivileged actor profits from.
- **access gap** — missing signer check, tautological auth, missing init/instantiate guard (the access mechanism itself is the bug).
- **ibc-counterparty** — any chain can open a channel; the "trusted relayer" is not a privilege.

No amplifier named → **REJECTED**. Amplifier named → judge it on that unprivileged path.

## Gate 4 — Impact

Prove material harm to an identifiable victim.

- Self-harm only → **REJECTED**
- Dust-level, no compounding → **DEMOTE**
- Material loss to identifiable victim, chain halt, or consensus-breaking state divergence → **CONFIRMED**

## Confidence

Start at **100**, deduct: partial attack path **-20**, bounded non-compounding impact **-15**, requires specific (but achievable) state **-10**. Confidence ≥ 80 gets description + fix. Below 80 gets description only.

## Safe patterns (do not flag)

- Sorted map-key iteration (`sort.Strings(keys)` then range the slice)
- `math.Int` / `math.LegacyDec` / CosmWasm `Uint128` checked arithmetic
- `ctx.BlockTime()` / `ctx.BlockHeight()` instead of `time.Now()`
- `address.Module(...)` for module accounts
- CosmWasm `cosmwasm-std` ≥ patched versions for CWA-2024-002 (`pow`/`neg`)
- Permissioned wasm upload when the finding is "anyone can upload"

## Lead promotion

Before finalizing leads, promote where warranted:

- **Cross-module echo.** Same root cause confirmed as FINDING in one module → promote in every module/contract where the identical pattern appears.
- **Multi-agent convergence.** 2+ agents flagged same area, lead was demoted (not rejected) → promote to FINDING at confidence 75.
- **Partial-path completion.** Only weakness is incomplete trace but path is reachable and unguarded → promote to FINDING at confidence 75, description only.

## Leads

High-signal trails for manual investigation. No confidence score, no fix — title, code smells, and what remains unverified.

## Do Not Report

Linter/compiler issues, gas/compute micro-opts, naming, proto comments. Authority privileges by design. Missing events (unless event contents are consensus-critical and non-deterministic). Centralization without exploit path. Implausible preconditions.
