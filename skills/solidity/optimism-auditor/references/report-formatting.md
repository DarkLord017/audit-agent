# Report format (Optimism auditor)

The whole reply is the report. The breaker and the JSON converter read
this text, not a file on disk.

Every finding **must** include a path relative to `unzipped/` and a line
number in the `Contract.function` · `path:line` line. Use `unknown` only
when the symbol is genuinely not in the tree.

````
# Security Review — Optimism / OP Stack

## Scope

| | |
| --- | --- |
| **Chain** | OP Mainnet / OP Stack fork / unclear (say which markers you found) |
| **Files reviewed** | `a.sol` · `b.sol` |
| **Overlay** | patterns that fired, or "no OP markers; generic EVM only" |

---

## Findings

[90] **1. <Title>**

`Contract.function` · `unzipped/<path>.sol:<line>` · Confidence: 90

**Description**
One or two sentences: the OP (or generic) assumption that is false, and
how an unprivileged actor extracts value.

**Chain fact**
Which overlay fact this uses (aliasing, 2s blocks, L1 fee, messenger, …)
or `generic-evm`.

**PoC hint**
What to mock on anvil (predeploy address, alias, `vm.warp` vs `vm.roll`).

**Fix**

```diff
- vulnerable
+ fixed
```

---

<more findings>

---

## Findings list

| # | Confidence | Title | Overlay |
|---|---|---|---|
| 1 | [90] | <title> | aliasing |
````

Confidence 1–100. ≥80 include a Fix diff. Below 80: description + chain
fact + path, no requirement for a diff.

Order: highest confidence first. Include generic EVM findings in the
same list; do not hide them in a footnote.
