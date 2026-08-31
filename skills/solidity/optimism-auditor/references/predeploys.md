# OP Stack predeploys and callable surface

Namespace: `0x4200000000000000000000000000000000000xxx` (proxied for the
first 2048 slots except `WETH` and `GovernanceToken`). Apps that
hard-code these addresses are OP Stack-specific even if comments say
"Ethereum".

Upgrade admin for most of these is `ProxyAdmin`
(`0x4200…0018`). Owner of that proxy can replace implementations —
treat as a trust assumption, not a user bug, unless the app copies a
predeploy and botches init.

## Addresses (Bedrock+)

| Name | Address | Call it for |
|---|---|---|
| LegacyMessagePasser | `0x4200…0000` | **Deprecated.** Do not withdraw through this. |
| DeployerWhitelist | `0x4200…0002` | **Deprecated.** CREATE is free. |
| WETH9 | `0x4200…0006` | Canonical WETH on OP Stack. |
| L2CrossDomainMessenger | `0x4200…0007` | `sendMessage`, `relayMessage`, `xDomainMessageSender` |
| GasPriceOracle | `0x4200…000F` | `getL1Fee(bytes)`, `l1BaseFee`, scalars |
| L2StandardBridge | `0x4200…0010` | ETH/ERC20 `bridgeETH*`, `bridgeERC20*`, finalize |
| SequencerFeeVault | `0x4200…0011` | `block.coinbase`; priority fees |
| OptimismMintableERC20Factory | `0x4200…0012` | L2 representations of L1 ERC20s |
| L1BlockNumber | `0x4200…0013` | **Legacy** wrapper; prefer `L1Block` |
| L2ERC721Bridge | `0x4200…0014` | NFT bridge |
| L1Block | `0x4200…0015` | L1 origin: `number`, `timestamp`, `basefee`, `hash`, `sequenceNumber`, blob/operator fee fields |
| L2ToL1MessagePasser | `0x4200…0016` | withdrawal commitments; `initiateWithdrawal`; ETH accumulates; `burn()` |
| OptimismMintableERC721Factory | `0x4200…0017` | L2 NFT representations |
| ProxyAdmin | `0x4200…0018` | upgrades |
| BaseFeeVault | `0x4200…0019` | L2 base fees (not burned) |
| L1FeeVault | `0x4200…001a` | L1 data fees |
| OperatorFeeVault | `0x4200…001B` | Isthmus operator fees |
| SchemaRegistry | `0x4200…0020` | EAS |
| EAS | `0x4200…0021` | EAS |
| GovernanceToken | `0x4200…0042` | OP token on OP Mainnet; **not** universal on every OP Stack chain |
| BeaconBlockRoot | `0x000F3df6D732807Ef1319fB7B8bB8522d0Beac02` | EIP-4788, L1 beacon roots (Ecotone) |
| LegacyERC20ETH | `0xDeadDeAd…0000` | **Dead** after Bedrock; stateful calls revert |

## Functions that show up in app code

### L2CrossDomainMessenger (`0x4200…0007`)

- `sendMessage(address target, bytes message, uint32 minGasLimit)` — L2→L1
  (or other domain). Does not mean the other side has executed.
- `relayMessage(...)` — executes an inbound message. Replay protection is
  the messenger's job; **your** target must still be idempotent if a
  retry is allowed after a failed relay.
- `xDomainMessageSender()` — **only valid during** a relayed call, and
  **only if** `msg.sender == messenger`. Reading it outside a relay, or
  trusting `msg.sender` as the L1 user, is the classic bridge bug.

Other messengers (custom, Hyperlane, LayerZero, Superchain interop
`L2ToL2CrossDomainMessenger`) are not this predeploy. Do not apply the
`0x4200…0007` address check to a different mailbox.

### L1Block (`0x4200…0015`)

View of the current L1 origin. Updated only by the **depositor account**
system address at epoch boundaries.

Useful: `number()`, `timestamp()`, `basefee()`, `hash()`,
`sequenceNumber()`, `baseFeeScalar()`, `blobBaseFee()`,
`blobBaseFeeScalar()`, operator-fee fields after Isthmus.

Not useful as: "current L1 head", "this transaction's L1 inclusion
block", or a VRF.

`L1BlockNumber.getL1BlockNumber()` is the legacy path to the same number.

### GasPriceOracle (`0x4200…000F`)

Post-Bedrock this is an estimation helper, not a privileged pusher.
`getL1Fee(bytes unsignedRlp)` is the L1 **data** fee for that payload.
Overhead/scalar were L1 `SystemConfig`; Ecotone switched to base/blob
scalars; Fjord changed compression. If the app reimplements the fee
formula, match the fork the chain is on or it will over/under charge.

### L2StandardBridge (`0x4200…0010`)

Standard lock-on-L1 / mint-on-L2 and burn-on-L2 / unlock-on-L1. Finalize
functions must only be callable via the messenger with the **L1 bridge**
as `xDomainMessageSender`. Local copies of this pattern that skip that
pair are critical.

`OptimismMintableERC20` / 721: only the bridge should mint/burn. Factory
deployments that leave `mint` public are critical.

### L2ToL1MessagePasser (`0x4200…0016`)

Low-level withdrawals. ETH sent here is not "withdrawn" until the L1
prove+finalize succeeds. `burn()` only removes L2 ETH supply against
already-accounted withdrawals — not a user refund.

### Fee vaults

`withdraw` / `donate` style functions send to an **immutable L1**
recipient after a threshold. Users cannot redirect `block.coinbase`
payments.

## L1 counterparts (when the zip includes both sides)

If L1 contracts are in scope: `OptimismPortal` (deposits, prove/finalize
withdrawal, deposit tx aliasing), `L1CrossDomainMessenger`,
`L1StandardBridge`, `SystemConfig`, `DisputeGameFactory` / fault-proof
games. Portal `finalizeWithdrawalTransaction` is not an L2 predeploy;
bugs there are L1-side, still in scope for this profile.
