<!--
Adapted from the ton-vulnerability-scanner skill in trailofbits/skills
(resources/VULNERABILITY_PATTERNS.md, pattern "FORWARD TON WITHOUT GAS CHECK"),
which is licensed CC-BY-SA-4.0. This file is therefore also CC-BY-SA-4.0.
See ../../ATTRIBUTION.md.
-->

# Forward TON without gas check (Trail of Bits)

Allowing users to specify `forward_ton_amount` (or any outbound coins) without
checking that inbound `msg_value` covers it lets them drain the contract's
TON: they pay a small fee and the contract forwards a large amount from
its own balance.

**Licence:** CC-BY-SA-4.0. Adapted from Trail of Bits
[`ton-vulnerability-scanner`](https://github.com/trailofbits/skills/tree/main/plugins/building-secure-contracts/skills/ton-vulnerability-scanner)
at commit [`7be90d6`](https://github.com/trailofbits/skills/commit/7be90d6e55e6b5e1607b519e97d0019b32b2656a).

## Detection

```func
if (op == op::transfer) {
    slice to_address = in_msg_body~load_msg_addr();
    int amount = in_msg_body~load_coins();
    int forward_ton_amount = in_msg_body~load_coins();  ;; USER CONTROLLED

    ;; WRONG: no msg_value >= fee + forward_ton_amount
    var msg = begin_cell()
        .store_uint(0x18, 6)
        .store_slice(to_address)
        .store_coins(forward_ton_amount)
        .store_uint(0, 1 + 4 + 4 + 64 + 32 + 1 + 1)
        .end_cell();
    send_raw_message(msg, 1);   ;; flag 1: fees from contract
}
```

Also vulnerable: `store_coins(forward_amount + reward)` where `reward` is
protocol funds and `forward_amount` is user-chosen.

**Check:**

- [ ] User cannot specify arbitrary forward TON, **or**
- [ ] `msg_value >= tx_fee + forward_ton_amount` (and any other outbound)
- [ ] Prefer a fixed / capped forward constant
- [ ] Flag 128 (carry all balance) is not combined with a user destination
- [ ] Flag 1 is not used with an unchecked user amount

## Mitigation

```func
const int FORWARD_TON_AMOUNT = 50000000; ;; 0.05 TON fixed
const int TX_FEE = 10000000;
const int MAX_FORWARD_TON = 100000000;

;; Preferred: ignore user forward, send a constant.
;; If user-specified:
throw_unless(error::forward_amount_too_high,
    forward_ton_amount <= MAX_FORWARD_TON);
throw_unless(error::insufficient_gas,
    msg_value >= TX_FEE + forward_ton_amount);

send_raw_message(msg, 64);  ;; remaining inbound value, not contract stack
```

## Send flags (short)

| Flag | Meaning | With user-chosen coins |
|---|---|---|
| 0 | fees from the message value | usually OK if `store_coins` is the inbound remainder |
| 1 | fees from contract balance | validate `msg_value` |
| 64 | remaining inbound value | safer default |
| 128 | entire remaining balance | owner-close only |

## References

building-secure-contracts/not-so-smart-contracts/ton/forward_value_without_check
