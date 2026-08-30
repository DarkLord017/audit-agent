# Slither in this container

Slither **0.11.6**, already installed. No network, so never try to install
or upgrade it.

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

On a contract with an unprotected `withdraw`, this reports:

```
Detector: arbitrary-send-eth
V.withdraw(address,uint256) (V.sol#5) sends eth to arbitrary user
```

Compilation failure on a partial upload is normal and is **not** a reason
to stop. Fall back to per-file runs:

```
slither unzipped/src/Vault.sol 2>&1 | tail -40
```

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

Real output:

```
| Function | State variables written | Conditions on msg.sender               |
| deposit  | ['bal']                 | []                                     |
| withdraw | []                      | []                                     |
| setOwner | ['owner']               | ['require(bool)(msg.sender == owner)'] |
```

`setOwner` is guarded. `withdraw` is not. That is a lead, not a finding.

### Others worth knowing

| Printer | Answers |
|---|---|
| `human-summary` | overall shape, complexity, ERC conformance |
| `function-summary` | visibility, modifiers, state read/written per function |
| `entry-points` | what is externally callable |
| `modifiers` | which modifiers apply where |
| `require` | every require/assert condition |
| `contract-summary` | inheritance and function list |

Full list: `slither --list-printers 2>&1`.

## How to use this in triage

Slither agreeing with a finding raises confidence. Slither **not** flagging
something is weak evidence of absence -- it has no view of business logic,
economics, or cross-contract flows, which is where most real findings live.

Never mark a finding VERIFIED because Slither agrees. Slither is a static
opinion; only a passing test is proof.
