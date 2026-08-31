<!--
Adapted from the cairo-vulnerability-scanner skill in trailofbits/skills,
which is licensed CC-BY-SA-4.0. This file is therefore also CC-BY-SA-4.0.
See ../../../ATTRIBUTION.md.
-->

# L1–L2 messaging

Three related ToB patterns. Full examples live in
[VULNERABILITY_PATTERNS.md](VULNERABILITY_PATTERNS.md).

## L1 to L2 address conversion (High)

Ethereum addresses are 160-bit; Starknet addresses are `felt252` with
`P < 2^256`. An L1 `uint256` recipient `>= P` wraps or becomes the zero
address on L2. Funds credit the zero address or an unintended account.

L1 must require `0 < l2Recipient < STARKNET_FIELD_PRIME`. L2 handlers must
reject the zero `ContractAddress`. See ToB
`l1_to_l2_address_conversion`.

## L1 to L2 message failure (High)

`sendMessageToL2` locks funds on L1. The sequencer may never consume the
message. Without `startL1ToL2MessageCancellation` / `cancelL1ToL2Message`
(and a delay), those funds are stuck. L2 handlers should be idempotent in
case a cancelled message is later consumed. See ToB
`l1_to_l2_message_failure`.

## Overconstrained L1 ↔ L2 interaction (Medium)

Different validation on each side traps funds: L1 whitelists depositors but
L2 will not honour the matching withdrawal, or L2 accepts a deposit that L1
will never release. Rules (whitelist, blacklist, pause, caps) must be
symmetric, and a full deposit→withdraw roundtrip must be tested. See ToB
`l1_l2_overconstrained`.

Handlers still need [l1-handler-from-address.md](l1-handler-from-address.md)
on top of these.
