<!--
Adapted from Trail of Bits solana-vulnerability-scanner
(plugins/building-secure-contracts/skills/solana-vulnerability-scanner),
licensed CC-BY-SA-4.0. This file is therefore also CC-BY-SA-4.0.
Source: resources/VULNERABILITY_PATTERNS.md pattern "Sysvar Account Check"
at commit 7be90d6e55e6b5e1607b519e97d0019b32b2656a.
See ../../ATTRIBUTION.md.
-->

# Sysvar Account Check

**Severity:** HIGH (especially pre-Solana 1.8.1)

In Solana versions before 1.8.1, users can pass spoofed sysvar accounts
(Instructions, Clock, …) to bypass authentication. Unchecked
`load_instruction_at()` / `load_current_index()` do not validate that
the account is the real sysvar. Modern code should still pin sysvar
addresses or use `Clock::get()`.

## Detection

```rust
use solana_program::sysvar::instructions;

let instructions_sysvar = next_account_info(accounts_iter)?;
// WRONG: load_instruction_at does not validate the sysvar account
let current_ix = instructions::load_instruction_at(0, instructions_sysvar)?;
// Attacker provides a fake Instructions sysvar

let current_index = instructions::load_current_index(instructions_sysvar)?;
```

**What to check:**

- Prefer Solana 1.8.1+
- Use checked functions: `load_instruction_at_checked()`,
  `load_current_index_checked()`
- Do not use: `load_instruction_at()`, `load_current_index()`
- Sysvar accounts validated against known ids (`sysvar::instructions::ID`,
  `sysvar::clock::ID`) or read via `Sysvar::get()`

## Mitigation

Use `load_instruction_at_checked(index, instructions_sysvar)`.

Or manually: `if instructions_sysvar.key != &sysvar::instructions::ID { return Err(...) }`.

Anchor: `#[account(address = solana_program::sysvar::instructions::ID)]`.

Prefer `Clock::get()?` over a passed Clock account when you only need
the clock.

## Tool detection

Trail of Bits lint: `unchecked-sysvar-account`. Look for
`load_instruction_at()` instead of `load_instruction_at_checked()`.

## References

building-secure-contracts/not-so-smart-contracts/solana/sysvar_get
