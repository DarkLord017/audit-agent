<!--
Adapted from the ton-vulnerability-scanner skill in trailofbits/skills
(resources/VULNERABILITY_PATTERNS.md, pattern "FAKE JETTON CONTRACT"),
which is licensed CC-BY-SA-4.0. This file is therefore also CC-BY-SA-4.0.
See ../../ATTRIBUTION.md.
-->

# Fake Jetton contract / missing sender check (Trail of Bits)

`transfer_notification` can be sent by **any** contract. Without validating
that the sender is the expected Jetton wallet, an attacker credits
themselves tokens that were never transferred.

**Licence:** CC-BY-SA-4.0. Adapted from Trail of Bits
[`ton-vulnerability-scanner`](https://github.com/trailofbits/skills/tree/main/plugins/building-secure-contracts/skills/ton-vulnerability-scanner)
at commit [`7be90d6`](https://github.com/trailofbits/skills/commit/7be90d6e55e6b5e1607b519e97d0019b32b2656a).

Opcode: `op::transfer_notification` = `0x7362d09c`.

## Real vs attack flow

- **Real:** User → user's Jetton wallet → receiver (`transfer_notification`)
- **Attack:** Attacker contract → receiver (same opcode, no Jetton moved)

## Detection

```func
() recv_internal(int my_balance, int msg_value, cell in_msg_full, slice in_msg_body) impure {
    slice cs = in_msg_full.begin_parse();
    int flags = cs~load_uint(4);
    slice sender_address = cs~load_msg_addr();
    int op = in_msg_body~load_uint(32);

    if (op == op::transfer_notification) {
        ;; WRONG: sender_address never compared to the stored wallet
        int jetton_amount = in_msg_body~load_coins();
        slice from_user = in_msg_body~load_msg_addr();
        credit_user(from_user, jetton_amount);
    }
}
```

Still vulnerable: checking `from_user` (body field the attacker writes) but
not `sender_address`. Still vulnerable: trusting `forward_payload` for
token id / pool id without a sender check.

Tact equivalent: `receive(TransferNotification)` without
`require(sender() == self.jettonWallet)`.

**Check:**

- [ ] Notify handler compares sender to a **stored** Jetton wallet address
- [ ] That address is set at init (or by owner) and is not attacker-writable
- [ ] `from_user` / `forward_payload` are not used as authentication
- [ ] Multi-Jetton dictionaries are keyed by something the sender cannot pick
      unless it matches the stored wallet for that key

## Mitigation

```func
global slice jetton_wallet_address;

if (op == op::transfer_notification) {
    throw_unless(error::wrong_jetton_wallet,
        equal_slices(sender_address, jetton_wallet_address));
    int jetton_amount = in_msg_body~load_coins();
    slice from_user = in_msg_body~load_msg_addr();
    credit_user(from_user, jetton_amount);
}
```

Owner-only `op::set_jetton_wallet` is the usual way to rotate the stored
wallet. Rotation while notifies are in flight is a separate trust-gap issue.

## References

building-secure-contracts/not-so-smart-contracts/ton/fake_jetton_contract
