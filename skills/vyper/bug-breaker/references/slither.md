# Slither in this container

Slither is already installed and **supports Vyper**. `vyper` is on PATH,
which crytic-compile needs. No network, so never try to install or upgrade
either.

## The one thing that catches everyone

**Slither writes its results to stderr, not stdout.** Without `2>&1` you
get an empty result and conclude, wrongly, that it found nothing.

```
slither unzipped/ 2>&1 | tail -60          # right
slither unzipped/ | tail -60               # WRONG - shows nothing
```

## Detectors

The default run. Start here.

```
slither unzipped/ 2>&1 | tail -80
```

On a Vyper vault with an unprotected `withdraw`, this reports something
in the shape of:

```
Detector: arbitrary-send-eth
V.withdraw(address,uint256) (V.vy#5) sends eth to arbitrary user
```

Compilation failure on a partial upload is normal and is **not** a reason
to stop. Fall back to per-file runs:

```
slither unzipped/src/Vault.vy 2>&1 | tail -40
```

If Slither cannot find a compilation unit (no `brownie-config.yaml` /
Foundry / hardhat, just loose `.vy` files), pass the file path directly.
A crytic-compile error on one file does not excuse skipping the others.

Some detectors are Solidity-flavoured (`delegatecall`, `unchecked`,
solc-version). Ignore those that do not apply. Keep anything about
reentrancy, arbitrary send, `msg.sender` auth, and dangerous `raw_call`.

## Printers

Printers answer structural questions faster than reading every file.
Select with `--print`.

### `vars-and-auth` — the best one for access control

Shows, per function, which state variables it writes and what conditions
it puts on `msg.sender`. An empty condition column next to a written state
variable is exactly the shape of a missing-access-control bug.

```
slither unzipped/ --print vars-and-auth 2>&1 | sed -n '/INFO:Printers/,$p'
```

On a `.vy` contract this is the same table. `set_owner` guarded by
`assert msg.sender == self.owner`. `withdraw` with an empty condition
column is a lead, not a finding.

### Others worth knowing

| Printer | Answers |
|---|---|
| `human-summary` | overall shape, complexity |
| `function-summary` | visibility, state read/written per function |
| `entry-points` | what is `@external` / callable |
| `require` | every `assert` / `raise` condition |
| `contract-summary` | function list |

Full list: `slither --list-printers 2>&1`.

Vyper has no modifiers in the Solidity sense — `@nonreentrant` shows up
as a lock, not a modifier printer row. Do not treat an empty modifiers
printer as "no auth."

## How to use this in triage

Slither agreeing with a finding raises confidence. Slither **not** flagging
something is weak evidence of absence -- it has no view of business logic,
economics, or cross-contract flows, which is where most real findings live.

Never mark a finding VERIFIED because Slither agrees. Slither is a static
opinion; only a passing test is proof.
