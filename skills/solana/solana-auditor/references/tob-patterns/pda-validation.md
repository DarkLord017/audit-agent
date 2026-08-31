<!--
Adapted from Trail of Bits solana-vulnerability-scanner
(plugins/building-secure-contracts/skills/solana-vulnerability-scanner),
licensed CC-BY-SA-4.0. This file is therefore also CC-BY-SA-4.0.
Source: resources/VULNERABILITY_PATTERNS.md pattern "Improper PDA Validation"
at commit 7be90d6e55e6b5e1607b519e97d0019b32b2656a.
See ../../ATTRIBUTION.md.
-->

# Improper PDA Validation

**Severity:** CRITICAL

Program-derived addresses can have multiple valid bumps for the same
seeds. Using `create_program_address()` without verifying the canonical
bump allows PDA spoofing: an attacker creates a second account that
derives from the same seeds with a non-canonical bump.

## Detection

```rust
// VULNERABLE: user-provided bump, create_program_address without canonical check
pub fn withdraw(ctx: Context<Withdraw>, bump: u8) -> Result<()> {
    let vault_seeds = &[
        b"vault",
        ctx.accounts.user.key().as_ref(),
        &[bump],  // WRONG: attacker can provide a non-canonical bump
    ];
    let vault = Pubkey::create_program_address(vault_seeds, ctx.program_id)?;
    // This vault might not be the canonical PDA
    Ok(())
}
```

**What to check:**

- PDAs use `find_program_address()` to get the canonical bump
- Or `create_program_address()` result is compared to the expected PDA
- Bump is stored and reused (not supplied by the user on later ixs)
- Anchor: `seeds` and `bump` constraints

## Mitigation

Native: `Pubkey::find_program_address(&[b"vault", user.key.as_ref()], program_id)`
then `if vault_account.key != &vault_pda { return Err(...) }`. Use that
canonical bump in `invoke_signed`.

Anchor:

```rust
#[account(mut, seeds = [b"vault", user.key().as_ref()], bump)]
pub vault: Account<'info, VaultAccount>,
```

Store `vault.bump` at init from `ctx.bumps`.

## Tool detection

Trail of Bits lint: `improper-pda-validation`. Look for
`create_program_address` without a `find_program_address` comparison.

## References

building-secure-contracts/not-so-smart-contracts/solana/pda_validation
