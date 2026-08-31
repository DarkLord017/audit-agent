<!--
Adapted from the cairo-vulnerability-scanner skill in trailofbits/skills,
which is licensed CC-BY-SA-4.0. This file is therefore also CC-BY-SA-4.0.
See ../../ATTRIBUTION.md.
-->

# Signature replay

A signature that does not bind a **nonce**, **chain id**, and **this
contract** can be replayed: twice on the same contract, or on a fork /
testnet / sibling deployment.

**Severity:** High.

## Detection

```cairo
fn execute_with_signature(
    ref self: ContractState,
    to: ContractAddress,
    amount: u128,
    signature: Array<felt252>,
) {
    let message_hash = pedersen_hash(to.into(), amount.into());
    let signer = recover_signer(message_hash, signature);
    self.transfer_internal(signer, to, amount); // no nonce
}
```

Check that:

- a per-signer (or per-account) nonce is stored and incremented **before**
  the side effect
- the hashed payload includes nonce, chain id (`get_tx_info().chain_id`),
  and `get_contract_address()`
- session / account abstraction paths (SNIP-9, outside execution) have
  their own replay domain, not a raw hash of calldata

OpenZeppelin Account / SRC-6 already does nonce + domain separation.
Reimplementing `is_valid_signature` without that is the usual bug.

## Caracal

Detector name in ToB docs: `missing-nonce-validation`. Not installed in
this image.

**ToB source:** `building-secure-contracts/not-so-smart-contracts/cairo/signature_replay`
and `cairo-vulnerability-scanner` pattern "SIGNATURE REPLAY PROTECTION".
