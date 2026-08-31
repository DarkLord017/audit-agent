# Replay, bounce, and opcode parsing

Original TON guidance for this auditor (not a Trail of Bits pattern file).
Replay is named in the ToB scanner's example output; bounce handling and
opcode parsing are the other two TON-specific lenses this pipeline adds.

## Replay

External messages (`recv_external` / Tact `external()`) are authenticated by
signature, not by "only once." Without a nonce, the same signed body is
valid forever.

**Hunt:**

- No `seqno` (or `valid_until` + `timeout`) loaded from the external body.
- Seqno compared but **not stored incremented** before `accept_message`.
- `accept_message` then a throw — depending on the phase, the message may
  still be considered delivered; the next replay uses the same seqno if
  storage was not updated.
- Internal messages that should be unique (`query_id` on Jetton transfer)
  credited again when the same notify is sent twice (the Jetton wallet
  usually will not; a fake wallet will). Replay of fake notify is the
  fake-Jetton bug; replay of a *real* wallet notify is not generally
  possible unless the wallet itself is buggy — still check idempotency
  keyed by `(sender, query_id)`.

**Fix shape:** load seqno, `throw_unless(seqno == stored)`, increment,
`save_data`, then `accept_message`. Reject expired `valid_until`.

## Bounce

Every outbound message has a bounce bit. If the destination is not a
deployed contract (or throws), a bounce message returns.

**Hunt:**

- `recv_internal` does not inspect `flags & 1` (bounced) and parses the
  bounce body as a new opcode — often a credit.
- Tact contract with no `bounced(...)` handler; confirm whether unmatched
  bounces are ignored or fall into `receive`.
- Bounce handler credits `sender` (the destination that rejected) instead
  of reversing the original debit to the user.
- Bounce body layout: bounced messages carry `0xFFFFFFFF` then the original
  op and a prefix of the original body. Loading as if it were a fresh
  `transfer_notification` is a classic mix-up.
- Unbounceable send of user funds to a not-yet-deployed account — burned.
- Bounceable send of protocol TON to an attacker who throws on purpose to
  drive a profitable bounce path.

**Fix shape:** first line of `recv_internal` after parsing flags: if bounced,
only run the reverse-accounting handler; never the happy-path opcode
switch. Tact: explicit `bounced(Msg)` that undoes `receive(Msg)`.

## Opcode parsing

FunC dispatch is manual. One wrong `load_uint` width shifts every later
field. Tact generates this; FunC and `asm` do not.

**Hunt:**

- `load_uint(32)` for op, but some messages use 32-bit op + 64-bit
  `query_id` and some forget `query_id` so `load_coins()` eats the query id.
- Missing `throw_unless(slice_empty(), …)` (or Tact equivalent) so extra
  bits are ignored — or a second concatenated op is smuggled.
- `if (op == A) { } else if (op == B) { } else { }` with empty else:
  unknown ops succeed and may `save_data` of uninitialized locals.
- Overlapping constants (`op::transfer` vs a getter method_id).
- `recv_external` and `recv_internal` sharing a parser that assumes an
  internal header (flags + sender) on an external body, or the reverse.
- `load_msg_addr()` vs `load_uint(256)`: bounceable flag bits become part
  of the key, so the same account has two dict entries.

**Fix shape:** document the TL-B (or Tact `message`) once; parse exactly
that; reject leftover bits; reject unknown ops; never share parsers
across internal/external/bounce without a tagged union.

## Proof bar

A replay finding names the missing seqno line and the second
`recv_external` that would succeed. A bounce finding names the flag bit
and the storage delta on the bounce path. An opcode finding names the
`load_*` widths and the concrete body hex (or field list) that is
misread. Without that, LEAD.
