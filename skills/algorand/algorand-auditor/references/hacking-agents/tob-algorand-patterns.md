<!--
Adapted from the algorand-vulnerability-scanner skill in trailofbits/skills,
which is licensed CC-BY-SA-4.0. This file is therefore also CC-BY-SA-4.0.
See ../../ATTRIBUTION.md.
-->

# Trail of Bits Algorand patterns (11)

These are the 11 Algorand-specific patterns from Trail of Bits'
[algorand-vulnerability-scanner](https://github.com/trailofbits/skills/tree/main/plugins/building-secure-contracts/skills/algorand-vulnerability-scanner)
and [Not So Smart Contracts — Algorand](https://github.com/crytic/building-secure-contracts/tree/master/not-so-smart-contracts/algorand).
Use them as a checklist. Your specialty file tells you which ones to
deepen; do not skip a pattern that is in your specialty just because it
also appears here.

Hunt in both PyTeal (`Txn.*`, `Gtxn[i].*`, `InnerTxnBuilder`) and raw TEAL
(`txn RekeyTo`, `gtxn 1 OnCompletion`, `itxn_field Fee`).

---

## 1. Rekeying — CRITICAL

Missing `RekeyTo` validation lets an attacker change account authorization
and bypass every later check.

- Every approving path must `Assert(Txn.rekey_to() == Global.zero_address())`
  (or an explicit intended address).
- Inner transactions (Teal v6+) must not take `rekey_to` from `Txn.accounts`.
- Group transactions: check RekeyTo on **every** relevant `Gtxn[i]`, not just `Txn`.
- Logic signatures: a missing check rekeys the **signed account**.

Tealer: `rekey-to`.

---

## 2. Unchecked transaction fee — HIGH

Smart signatures without a fee bound let the sender set an enormous fee
and drain the account paying it.

- Logic sigs: `Assert(Txn.fee() == Global.min_txn_fee())` or `== Int(0)` with pooling.
- `Txn.fee() <= some_large_value` is still unbounded in practice.
- Applications pooling fees: inner txns must not inherit a non-zero default.

---

## 3. CloseRemainderTo — CRITICAL

Missing `CloseRemainderTo` on a payment lets the sender empty the account
to an arbitrary address.

- Payments: `Assert(Txn.close_remainder_to() == Global.zero_address())`.
- Inner payments: do not set CloseRemainderTo unless that is the intended close.

Tealer: `can-close-account`.

---

## 4. AssetCloseTo — CRITICAL

Same shape as CloseRemainderTo, for ASAs: missing `AssetCloseTo` on an
axfer transfers the **entire** ASA balance.

- `Assert(Txn.asset_close_to() == Global.zero_address())` on every axfer path.
- Inner axfers: same rule.

Tealer: `can-close-asset`.

---

## 5. Group size — HIGH

Absolute `Gtxn[i]` indexes without `Global.group_size()` let an attacker
pad the atomic group and replay an app call.

- Pair every `Gtxn[i]` with `Assert(Global.group_size() == Int(N))` (or `<=`).
- "Missing transaction verification" is the same bug: no GroupSize / GroupIndex check at all.
- Group manipulation: attacker reorders, duplicates the app call, or inserts a ClearState.
- Atomic ordering: do not assume txn 0 is the payment if the sender can shuffle.

Tealer: `group-size-check`.

---

## 6. Time-based replay — MEDIUM

Periodic / lease-less logic lets the same `FirstValid`/`LastValid` window
be used more than once.

- Recurring payments need `Txn.lease()` set to a unique value per logical payment.
- `Global.latest_timestamp() >= next_payment_time` without a lease or counter is replayable.

---

## 7. Access controls (update / delete) — CRITICAL

`UpdateApplication` or `DeleteApplication` returning 1 with no sender
check lets anyone replace or destroy the app.

- Gate with `Txn.sender() == Global.creator_address()` (or a stored admin).
- Or disable: `Return(Int(0))` on those OnComplete values.
- Weak check: OnComplete branch exists but does not compare sender.

Tealer: `unprotected-updatable`, `unprotected-deletable`, `is-updatable`, `is-deletable`.

---

## 8. Asset ID verification — HIGH

Missing `Txn.xfer_asset() == expected_id` lets the attacker pay with a
worthless ASA.

- Expected id from global state or a constant, never from an unconstrained method arg.
- Check id **and** amount **and** sender/receiver.

---

## 9. Asset opt-in DoS — MEDIUM

Pushing ASAs to accounts that have not opted in fails the whole group.

- Prefer pull (`claim`) over looping inner axfers to a user list.
- A single not-opted-in receiver bricks batch distribution.

---

## 10. Inner transaction fee — MEDIUM

Unset inner `Fee` drains the application account under fee pooling.

- Every `InnerTxnBuilder.SetFields` must include `TxnField.fee: Int(0)`.
- Non-zero inner fees need explicit bookkeeping.

---

## 11. Clear-state / OnComplete — HIGH

`TxnType.ApplicationCall` is true for ClearState. The clear-state program
runs instead of approval, bypassing every Assert in approval.

- Next to every `Gtxn[i].type_enum() == TxnType.ApplicationCall`, require
  `Gtxn[i].on_completion() == OnComplete.NoOp` (or the specific allowed value).
- Clear-state programs should not assume they can prevent opt-out; they
  cannot. They must not leave global accounting wrong when a user force-exits.

---

## Also hunt (same ToB family)

- **Clawback:** ASA clawback address still set (or settable by a non-admin) seizes user balances.
- **Application state:** `App.globalPut` / `App.localPut` without sender or group checks.
- **Minimum balance:** inner payments that drop an account below min-balance fail; use as griefing.
- **Logic signature reuse:** a lsig that does not bind receiver / lease / first-valid is a blank cheque.
