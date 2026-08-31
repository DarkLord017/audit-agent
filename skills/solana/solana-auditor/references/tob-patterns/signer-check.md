<!--
Adapted from Trail of Bits solana-vulnerability-scanner
(plugins/building-secure-contracts/skills/solana-vulnerability-scanner),
licensed CC-BY-SA-4.0. This file is therefore also CC-BY-SA-4.0.
Source: resources/VULNERABILITY_PATTERNS.md pattern "Missing Signer Check"
at commit 7be90d6e55e6b5e1607b519e97d0019b32b2656a.
See ../../ATTRIBUTION.md.
-->

# Missing Signer Check

**Severity:** CRITICAL

Sensitive operations without `is_signer` validation allow anyone to
pass the authority's pubkey as a non-signing account and act as that
authority.

## Detection

```rust
// VULNERABLE: pubkey compared, signature never required
let authority = next_account_info(accounts_iter)?;
let vault_data: Vault = Vault::try_from_slice(&vault.data.borrow())?;
if vault_data.authority != *authority.key {
    return Err(ProgramError::InvalidAccountData);
}
// Process withdrawal — attacker did not sign

// VULNERABLE: Anchor without Signer type
#[derive(Accounts)]
pub struct Withdraw<'info> {
    #[account(mut)]
    pub vault: Account<'info, VaultAccount>,
    /// CHECK: Missing signer constraint
    pub authority: AccountInfo<'info>,
}
```

**What to check:**

- Every authority account is validated with `is_signer`
- Native: `account.is_signer == true`
- Anchor: `Signer<'info>` (automatic)
- Access-controlled instructions require a signer check, not only a
  pubkey equality check

## Mitigation

Native: `if !authority.is_signer { return Err(ProgramError::MissingRequiredSignature); }`
then compare keys.

Anchor:

```rust
#[account(mut, has_one = authority)]
pub vault: Account<'info, VaultAccount>,
pub authority: Signer<'info>,
```

## Tool detection

Trail of Bits lint: `missing-signer-check`. Look for authority checks
without `is_signer`.

## References

building-secure-contracts/not-so-smart-contracts/solana/signer_check
