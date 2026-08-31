<!--
Adapted from Trail of Bits solana-vulnerability-scanner
(plugins/building-secure-contracts/skills/solana-vulnerability-scanner),
licensed CC-BY-SA-4.0. This file is therefore also CC-BY-SA-4.0.
Source: resources/VULNERABILITY_PATTERNS.md pattern "Missing Ownership Check"
at commit 7be90d6e55e6b5e1607b519e97d0019b32b2656a.
See ../../ATTRIBUTION.md.
-->

# Missing Ownership Check

**Severity:** HIGH

Accounts deserialized without an owner check can be spoofed. The user
passes an account they own, packed with forged data (fake balances,
fake authorities).

## Detection

```rust
// VULNERABLE: deserialize without owner check
let vault_account = next_account_info(accounts_iter)?;
let vault: Vault = Vault::try_from_slice(&vault_account.data.borrow())?;
// vault could be a fake account owned by the attacker

// VULNERABLE: Anchor without owner constraint
#[derive(Accounts)]
pub struct Withdraw<'info> {
    /// CHECK: This is unsafe - no owner validation
    pub vault: AccountInfo<'info>,
}
```

**What to check:**

- Every account is owner-validated before deserialization
- Native: `account.owner == expected_program_id`
- Anchor: `Account<'info, T>` (automatic owner check)
- System accounts: `owner == system_program::ID`
- Token accounts: `owner == spl_token::ID` (or Token-2022 id)

## Mitigation

Native: `if vault_account.owner != program_id { return Err(ProgramError::IncorrectProgramId); }`
then deserialize.

Anchor: `pub vault: Account<'info, VaultAccount>` — owner is this
program. For SPL token accounts, `Account<'info, TokenAccount>`.

## Tool detection

Trail of Bits lint: `missing-ownership-check`. Look for deserialization
without owner validation.

## References

building-secure-contracts/not-so-smart-contracts/solana/ownership_check
