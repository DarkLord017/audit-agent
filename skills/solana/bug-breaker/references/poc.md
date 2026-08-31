# Writing a proof

A proof is a test that **fails, or succeeds, only because the bug is real**.
If the test would behave the same on correct code, it proves nothing.

Prefer **LiteSVM** (in-process VM, no `solana-test-validator`). Fall back
to `solana-program-test` if the upload already uses it. Host-native unit
tests of `process_instruction` are fine when the bug is reachable without
SBF.

## The shape

One test per finding. Name it after the finding.

```rust
use litesvm::LiteSVM;
use solana_sdk::{
    pubkey::Pubkey,
    signature::{Keypair, Signer},
    transaction::Transaction,
};

#[test]
fn attacker_withdraws_without_signing() {
    // 1. ARRANGE — a victim with something to lose
    let mut svm = LiteSVM::new();
    let program_id = Pubkey::new_unique();
    // Load a prebuilt .so if the upload shipped one under target/deploy/.
    // Never compile by fetching crates. Never modify unzipped/.
    svm.add_program(program_id, include_bytes!("../../unzipped/target/deploy/vault.so"));

    let victim = Keypair::new();
    svm.airdrop(&victim.pubkey(), 10_000_000_000).unwrap();

    // 2. ACT — the attacker does the thing the finding claims
    let attacker = Keypair::new();
    svm.airdrop(&attacker.pubkey(), 1_000_000_000).unwrap();
    let ix = /* withdraw ix: vault's authority pubkey as a NON-signer */;
    let tx = Transaction::new_signed_with_payer(
        &[ix],
        Some(&attacker.pubkey()),
        &[&attacker],
        svm.latest_blockhash(),
    );
    svm.send_transaction(tx).unwrap();

    // 3. ASSERT — the harm, in numbers
    let attacker_lamports = svm.get_balance(&attacker.pubkey()).unwrap();
    assert!(
        attacker_lamports > 1_000_000_000,
        "attacker took the victim's vault lamports"
    );
}
```

Verified working in this container looks like:

```
test attacker_withdraws_without_signing ... ok
```

## The three parts, always

**Arrange** — set up a state where there is something real to lose. A bug
that only "works" on an empty program usually is not one.

**Act** — do exactly what the finding claims an attacker can do. The
attacker keypair must be unmistakably not the admin / upgrade authority.

**Assert** — assert the *harm*, not the mechanism. `attacker token
balance == victim's deposit` is a proof. `send_transaction did not
err` is not — plenty of harmless instructions succeed.

## Two directions a proof can run

**The bug lets something happen that should not.** Write a test that
*passes* — the attacker succeeds. That passing test is the proof.

**The bug blocks something that should work.** Write a test doing the
legitimate thing and show it errors. Quote the program error.

Either way, quote the output. A claim of "the test passed" without the
output is not evidence.

## Honest failure

If you cannot build a proof, say why in one line and mark it UNVERIFIED:

- *"crate X is not in the offline cache, cargo test --offline failed"*
- *"needs a compiled .so and cargo-build-sbf is not in this image"*
- *"needs two programs to interact and the second is not in scope"*
- *"/work is 1g tmpfs; the debug build OOM'd — marked UNVERIFIED"*

Do not:

- assert something trivially true and call it a proof
- mark VERIFIED because the code "obviously" has the bug
- rewrite the program under review to make your test pass

That last one is the subtle failure. **Never modify anything in
`unzipped/`.** If your test only passes after you changed their code, you
have proved a bug in your code, not theirs.

## Minimal mocks are fine

If the instruction needs a mint or a sysvar, construct them in the test
(LiteSVM ships System / SPL Token). That is setup, not modification.
Keep it minimal — a mock program that does anything clever becomes the
thing you are testing.
