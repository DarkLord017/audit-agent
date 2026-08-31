<!--
Adapted from Trail of Bits solana-vulnerability-scanner
(plugins/building-secure-contracts/skills/solana-vulnerability-scanner),
licensed CC-BY-SA-4.0. This file is therefore also CC-BY-SA-4.0.
Source: resources/VULNERABILITY_PATTERNS.md pattern
"Improper Instruction Introspection"
at commit 7be90d6e55e6b5e1607b519e97d0019b32b2656a.
See ../../ATTRIBUTION.md.
-->

# Improper Instruction Introspection

**Severity:** MEDIUM

Using absolute indexes in instruction introspection lets a later
instruction in the same transaction reuse an earlier instruction as its
"setup" check. Relative indexes bind the check to the immediately
related instruction.

## Detection

```rust
let instructions_sysvar = &accounts[0];
// WRONG: absolute index 0
let prev_ix = instructions::load_instruction_at_checked(0, instructions_sysvar)?;
// Attacker crafts tx where instruction 0 is benign; instruction 1
// (malicious) also loads instruction 0 for validation

pub fn withdraw(ctx: Context<Withdraw>) -> Result<()> {
    let prev_ix = instructions::load_instruction_at_checked(
        0, &ctx.accounts.instructions_sysvar,
    )?;
    // WRONG: not checking that prev_ix is actually related to this ix
}
```

**What to check:**

- Use relative indexes: `get_instruction_relative(-1, ...)` for the
  previous instruction
- Absolute indexes only when specifically intended
- Validate correlation: previous ix program id, accounts (same vault,
  same user) match the current instruction
- The same setup instruction must not authorize multiple later calls

## Mitigation

```rust
let current_index = instructions::load_current_index_checked(instructions_sysvar)?;
if current_index > 0 {
    let prev_ix = instructions::load_instruction_at_checked(
        (current_index - 1) as usize,
        instructions_sysvar,
    )?;
    // Validate prev_ix.program_id and prev_ix.accounts against this ix
}
// Better, if available:
// let prev_ix = instructions::get_instruction_relative(-1, instructions_sysvar)?;
```

Also require `prev_ix.program_id == *this_program` and that the vault
account in `prev_ix` equals `ctx.accounts.vault.key()`.

## References

building-secure-contracts/not-so-smart-contracts/solana/insecure_instruction_introspection
