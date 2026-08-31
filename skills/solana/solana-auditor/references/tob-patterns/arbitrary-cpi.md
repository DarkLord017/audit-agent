<!--
Adapted from Trail of Bits solana-vulnerability-scanner
(plugins/building-secure-contracts/skills/solana-vulnerability-scanner),
licensed CC-BY-SA-4.0. This file is therefore also CC-BY-SA-4.0.
Source: resources/VULNERABILITY_PATTERNS.md pattern "Arbitrary CPI"
at commit 7be90d6e55e6b5e1607b519e97d0019b32b2656a.
See ../../ATTRIBUTION.md.
-->

# Arbitrary CPI (Cross-Program Invocation)

**Severity:** CRITICAL

Using `invoke()` or `invoke_signed()` with a user-controlled program id
lets an attacker call a malicious program instead of the intended one
(typically SPL Token or the System program). The CPI still carries this
program's signers — including PDA signatures from `invoke_signed`.

## Detection

```rust
// VULNERABLE: User-provided program ID without validation
pub fn transfer_tokens(ctx: Context<TransferTokens>, amount: u64) -> Result<()> {
    let token_program = &ctx.accounts.token_program;
    // WRONG: No check that token_program.key() == spl_token::ID
    invoke(
        &spl_token::instruction::transfer(...),
        &[
            ctx.accounts.from.to_account_info(),
            ctx.accounts.to.to_account_info(),
            token_program.to_account_info(),  // ATTACKER CONTROLLED
        ],
    )?;
    Ok(())
}

// VULNERABLE: Native Solana without validation
let token_program = next_account_info(accounts_iter)?;
invoke(&transfer_instruction, &[from_account, to_account, token_program])?;
```

**What to check:**

- Every CPI program id is validated before `invoke` / `invoke_signed`
- Validation: `program.key() == EXPECTED_PROGRAM_ID`
- Caller cannot pass an arbitrary program account
- Anchor: `Program<'info, T>` (or `address = ...`) on the program account

## Mitigation

Native: compare `token_program.key` to `spl_token::ID` (or the intended
id) and return `ProgramError::IncorrectProgramId` on mismatch.

Anchor: `pub token_program: Program<'info, Token>` — the type pins the id.

## Tool detection

Trail of Bits lint: `unchecked-cpi-program-id`. Look for `invoke()` with
no prior program-id check.

## References

building-secure-contracts/not-so-smart-contracts/solana/arbitrary_cpi
