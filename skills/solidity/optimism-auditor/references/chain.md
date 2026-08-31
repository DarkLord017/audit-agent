# OP Stack chain facts (auditor overlay)

OP Mainnet chain id **10**. OP Sepolia **11155420**. Other OP Stack chains
reuse the same execution rules with different ids, EIP-1559 constants, and
sometimes a different block time. Confirm in-repo config before treating
a number as OP Mainnet.

This is not a spec. When the repo pins an OP Stack release or fork name
(Bedrock, Ecotone, Fjord, Granite, Holocene, Isthmus), prefer that fork's
fee and `L1Block` fields.

## Block time and clocks

| Clock | What it is | Typical OP Mainnet |
|---|---|---|
| `block.timestamp` | L2 timestamp | +2s per L2 block (configurable `l2_block_time`) |
| `block.number` | **L2** block number | +1 per ~2s, **not** L1 |
| `L1Block.number()` | L1 origin block | updates once per L1 epoch (~12s), same value for several L2 blocks |
| `L1Block.timestamp()` | L1 origin timestamp | same stickiness |
| `L1Block.sequenceNumber()` | L2 blocks since epoch start | 0 at epoch boundary |

Ethereum L1 is ~12s. A delay of `N` **blocks** on OP is ~`N*2` seconds, not
`N*12`. Vesting, TWAP windows, rate limits, "wait 256 blocks", and
`blockhash` lookbacks that were sized for L1 fire ~6× faster.

`BLOCKHASH` only covers L2 hashes, last 256 L2 blocks (~8.5 minutes at 2s),
not L1 hashes. L1 hash is `L1Block.hash()`, and it is the **origin**, not
"this L2 block's L1".

Sequencer may stretch epochs when L1 is skipped or the batcher lags, so
L2 time vs L1 origin can drift within `max_sequencer_drift`. Do not treat
`block.timestamp` as tightly coupled to L1 time.

## Fees and gas

Users pay **more than** `gas * tx.gasprice`.

1. **L2 execution** — EIP-1559 base fee + priority fee. Base fee is **not**
   burned; it goes to `BaseFeeVault`. Priority fee goes to
   `SequencerFeeVault` (`block.coinbase`).
2. **L1 data fee** — pays for posting the tx to L1 DA. Estimated via
   `GasPriceOracle.getL1Fee(unsignedRlpTx)` (and Fjord+ size estimation).
   Not included in `tx.gasprice` / `GASPRICE`.
3. **Operator fee** (Isthmus+) — additional charged attribute; vault at
   `OperatorFeeVault`.

`GASPRICE` / `tx.gasprice` / refunds based on `gasleft()` **undercount**
real user cost. Relayers that require `msg.value >= gasprice * limit` can
be griefed or can underpay themselves.

EIP-1559 elasticity and denominator are **per-chain config**, not
Ethereum's 8/2. Do not hard-code L1 fee-market behaviour.

## Opcodes and tx fields that differ

| Opcode / field | Solidity | OP Stack behaviour vs L1 |
|---|---|---|
| `COINBASE` | `block.coinbase` | Sequencer fee wallet (`SequencerFeeVault`). Almost never rotates. |
| `PREVRANDAO` / `DIFFICULTY` | `block.prevrandao` | L1 RANDAO at current **L1 origin**, reused for many L2 blocks. |
| `ORIGIN` / `CALLER` | `tx.origin` / `msg.sender` | Aliased on L1→L2 **deposit txs from L1 contracts**. |
| `NUMBER` / `TIMESTAMP` | `block.number` / `block.timestamp` | L2 values. |
| `CHAINID` | `block.chainid` | 10 on OP Mainnet, not 1. |
| `BASEFEE` | `block.basefee` | L2 base fee. |
| Deposit tx type | — | Type `0x7e` exists only on L2 derivation; not a normal L2 mempool tx. |

### Address aliasing

L1 contract deposits (code at sender, except a valid EIP-7702 delegation):

```
aliased = uint160(l1Contract) + 0x1111000000000000000000000000000000001111
```

(overflow wraps at 160 bits). EOAs and 7702-delegated EOAs are **not**
aliased. Ephemeral create+selfdestruct senders **are** aliased.

If a contract on L2 checks `msg.sender == knownL1` for a deposit tx, it
will miss the aliased sender. Reverse: if it treats an aliased address as
an L2 user, it attributes the wrong party.

`CrossDomainMessenger` accounts for aliasing internally. Raw
`OptimismPortal.depositTransaction` does not save you.

## Mempool, ordering, MEV

There is **no public mempool**. The sequencer sees the queue and executes
by **priority fee** (highest first), and can insert or reorder within the
soft-confirmation window. Assume:

- No fair ordering, no L1-style searcher competition in a public pool
- `tx.origin` sandwich / same-block backrun is sequencer-shaped, not
  builder-shaped
- Censorship of L2-submitted txs is possible until L1 **forced inclusion**
  (deposit) lands — design timeouts accordingly
- `block.coinbase` transfer tips do not bribe an L1 builder

## Heads and withdrawals

L2 has **unsafe / safe / finalized** heads. Unsafe can reorg. Contracts
that treat the latest block as irreversible (CEX deposits, oracle
writes, NFT mints as final) are wrong until they wait for a safe or
finalized policy — and even then, **withdrawals to L1** are a separate
prove+finalize path with a fault-proof challenge window (on the order of
days, not minutes).

Do not equate "tx succeeded on L2" with "funds are on L1".

## Config the code may assume wrongly

| Knob | L1 intuition | OP reality |
|---|---|---|
| Block time | 12s | Often 2s |
| 256-block window | ~51 min | ~8.5 min |
| `block.coinbase` auth | rotating proposer | fee vault |
| Blob / 4788 | L1 beacon roots | `BeaconBlockRoot` predeploy serves **L1** beacon roots |
| ETH representation | native | native post-Bedrock; `LegacyERC20ETH` is dead |
| Custom gas token | ETH | some OP Stack forks; fee and `msg.value` semantics change |

SystemConfig on L1 owns fee scalars; `L1Block` is the L2 view, updated
by the **depositor account** system address, not by users.
