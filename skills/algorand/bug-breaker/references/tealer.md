# Tealer in this container

Tealer (Crytic static analyzer for TEAL) is already installed. No
network, so never try to install or upgrade it.

Tealer reads **compiled TEAL**, not PyTeal. Compile first
([pyteal.md](pyteal.md)), write the `.teal` under `poc/`, then run
Tealer on that file.

## Commands that work here

The CLI is `tealer detect`, not a bare filename. Capture both streams:

```
tealer detect --contracts poc/approval.teal 2>&1
```

On a logic signature that is missing RekeyTo / CloseRemainderTo, this
reports detectors such as:

```
rekey-to              Rekeyable Logic Signatures
can-close-account     Missing CloseRemainderTo field Validation
can-close-asset       Missing AssetCloseTo Field Validation
missing-fee-check     Missing Fee Field Validation
group-size-check      Usage of absolute indexes without validating GroupSize
unprotected-updatable / unprotected-deletable
is-updatable / is-deletable
```

Printers (optional, for triage — they may write `.dot` files under cwd):

```
tealer print human-summary --contracts poc/approval.teal 2>&1
tealer print transaction-context --contracts poc/approval.teal 2>&1
```

If `tealer detect` errors on a filename-as-first-arg form, do not guess
a second CLI; retry with `--contracts` as above. If it still fails
(unsupported TEAL version, empty file), quote the error and continue
triage without it.

## How to use this in triage

Tealer agreeing with a finding raises confidence. Tealer **not**
flagging something is weak evidence of absence — it has no view of ABI
business logic, share-price inflation, or ClearState accounting, which
is where many real findings live. Several detectors apply only to
**stateless** programs (logic sigs); stateful apps will not show
`rekey-to` even when the approval path is missing the check. Do not
treat a clean Tealer run on an app as "RekeyTo is fine."

Never mark a finding VERIFIED because Tealer agrees. Tealer is a static
opinion; only a pytest that ran is proof.

## Do not

- run Tealer on `.py` files
- write output or patched TEAL into `unzipped/`
- fail the whole breaker because one program would not parse
