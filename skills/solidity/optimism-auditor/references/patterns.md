# Optimism / OP Stack vulnerability patterns

Search the in-scope tree for each pattern. Confirm reachability and
funds impact before reporting. Quote the line.

## 1. Time and block-number units sized for L1

**Look for:** `block.number`, `block.timestamp`, delays in "blocks",
`blockhash`, TWAP windows, vesting cliffs, rate `per block`,
`MIN_DELAY`, governor `votingDelay` in blocks.

**Bug:** Constants that encode ~12s L1 blocks (e.g. `1 days / 12`,
`256` as "about an hour", Uniswap-v2-style 30-minute TWAP as 150
blocks) run ~6× faster at 2s. `blockhash(block.number - 256)` is ~8.5
minutes of L2 history, not ~51 minutes.

**Also:** mixing `block.number` (L2) with `L1Block.number()` (L1 origin)
in one formula.

## 2. Using L2 env as if it were L1 consensus

**Look for:** `block.coinbase`, `block.prevrandao`, `block.difficulty`,
`block.basefee` as randomness, auth, or "tip the proposer".

**Bug:**

- `coinbase` is the SequencerFeeVault; auth against it is a constant
  address check, not "current builder"
- `prevrandao` is L1 origin RANDAO, **constant across an epoch** (~6 L2
  blocks typical) — same-epoch grinding / reuse
- `basefee` is L2, not L1; L1 base fee is `L1Block.basefee()`

## 3. Fee refunds and gas accounting ignore L1 (and operator) fees

**Look for:** `tx.gasprice`, `gasleft()`, `block.basefee`, relayer
reimbursement, `GasPriceOracle` used only as `l1BaseFee` without
`getL1Fee`, custom copies of the legacy overhead/scalar formula.

**Bug:** User or relayer is paid/charged execution gas only. Post-Fjord
size estimation and Isthmus operator fee make homemade formulas stale.

## 4. Cross-domain sender confused with `msg.sender`

**Look for:** `relayMessage`, `finalizeBridge`, `finalizeETHWithdrawal`,
`xDomainMessageSender`, `onlyOtherBridge`, `messenger.call`,
`0x4200…0007`.

**Bug:** Target trusts `msg.sender` as the L1 user, or reads
`xDomainMessageSender()` without `require(msg.sender == messenger)`.
Replay: finalized mapping not updated, or success-path skipped on
outer `relayMessage` retry. `minGasLimit` too low → griefed relay,
funds stuck unless retry is actually possible.

## 5. Address aliasing skipped or inverted

**Look for:** `depositTransaction`, `0x1111…1111`, comparisons of
`msg.sender` to a known L1 contract on an L2 entry point, "L1 owner"
stored and later compared on L2 without alias, CREATE2 "same address
on L1 and L2" used as auth.

**Bug:** L1 contract deposits arrive from `l1 + 0x1111…1111`. Checks
against the unaliased L1 address fail closed (DoS) or, if the L2 twin
is trusted, fail open (impersonation — the reason aliasing exists).
EOA deposits are **not** aliased; mixing the two rules is common.

## 6. Standard bridge / mintable token auth

**Look for:** `OptimismMintableERC20`, `mint`, `burn`, `BRIDGE`,
`l1Token`, `l2Token`, `finalizeBridgeERC20`, custom factories.

**Bug:** Anyone can mint the L2 representation; `l1Token`/`l2Token`
pair mismatch; bridge finalize callable without messenger+L1 bridge
sender; decimals/name mismatch used in accounting; native ETH still
talking to `LegacyERC20ETH`.

## 7. Withdrawals treated as final on L2

**Look for:** `initiateWithdrawal`, `bridgeETHTo`, `proveWithdrawal`,
`finalizeWithdrawal`, credit user on L1-side off-chain when L2 tx
lands, accounting that burns L2 tokens and immediately releases an
L1 IOU in the same contract without the portal.

**Bug:** L2 success ≠ L1 finality. Challenge window. Reorg of **unsafe**
head. Double-credit if a retry/finalize can run twice.

## 8. Sequencer liveness and forced inclusion

**Look for:** deadlines in seconds that assume continuous L2 blocks,
oracles that must update every N L2 blocks, liquidation keepers that
only send L2 txs (no deposit path), `require(block.timestamp - t < X)`
that bricks if the sequencer is down beyond X.

**Bug:** During sequencer outage only L1 deposits include. If the only
un-brick path is an L2 tx, funds freeze. If a timeout **releases**
collateral to the other side when keepers cannot include, that's theft
via outage.

## 9. Unsafe head as settlement

**Look for:** CEX/off-chain settlement, oracles, NFT mints, "confirmed
after 1 block", `block.number` checkpoints without waiting for safe
or a sufficient L1 origin advance (`L1Block.number()` moving).

**Bug:** Unsafe blocks reorg. Using L1 origin number as a deeper
confirmation is better than raw L2 number, still not L1 finality.

## 10. Chain id, domain separators, and Superchain copies

**Look for:** `block.chainid`, EIP-712 domain, permit, signed messages
without chain id, replay of L2→L2 interop messages, hard-coded `10`
on a fork, OP token at `0x4200…0042` on a chain that is not OP Mainnet.

**Bug:** Signature replay across OP Stack chains (same code, different
id if forgotten). Governance token predeploy is not "the OP token"
everywhere. Interop/`CrossL2Inbox` identifiers must bind (chain, log,
index).

## 11. Deposit tx and first-frame `msg.sender`

**Look for:** constructors or initializers expected to be called from
an L1 factory via deposit, `tx.origin` gating, multicall at top level
of a deposit.

**Bug:** First frame of a contract-deposited tx has **aliased**
`msg.sender`/`tx.origin`. Inner calls are normal. Access control that
only holds for EOA L2 txs fails on the deposit path.

## 12. Reimplementing system contracts

**Look for:** local `L1Block`, `GasPriceOracle`, messenger, or WETH at
non-canonical addresses; `ecrecover` "L1 block hash" from calldata
without the predeploy.

**Bug:** Stale fee math, spoofable L1 hash, WETH not the canonical
`0x4200…0006` so bridges and routers desync.

## Generic Solidity (still required)

Reentrancy (including during `relayMessage` target execution),
`initialize`/`upgradeTo` on proxies, `approve`/`transferFrom` on
fee-on-transfer and ERC-777, oracle end-of-block manipulation
(**easier** with 2s blocks and a private mempool), signature replay,
incorrect `safeTransfer` return checks, insolvent bridges from
rounding.

When in doubt: if an L1 auditor would skip it because "the proposer
wouldn't", **do not skip it** — the sequencer is a different trust
model.
