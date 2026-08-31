<!--
Adapted from the ton-vulnerability-scanner skill in trailofbits/skills
(resources/VULNERABILITY_PATTERNS.md, pattern "INTEGER AS BOOLEAN"),
which is licensed CC-BY-SA-4.0. This file is therefore also CC-BY-SA-4.0.
See ../../ATTRIBUTION.md.
-->

# Integer as boolean (Trail of Bits)

FunC uses integers for booleans: **0 = false, -1 = true**. The bitwise NOT
operator `~` on any other value (especially `1`) produces a still-truthy
result and silently inverts control flow.

**Licence:** CC-BY-SA-4.0. Adapted from Trail of Bits
[`ton-vulnerability-scanner`](https://github.com/trailofbits/skills/tree/main/plugins/building-secure-contracts/skills/ton-vulnerability-scanner)
at commit [`7be90d6`](https://github.com/trailofbits/skills/commit/7be90d6e55e6b5e1607b519e97d0019b32b2656a).

## Why it works

- FunC `true` = `-1` (all bits set)
- FunC `false` = `0`
- `~0 = -1`, `~(-1) = 0`
- **`~1 = -2` (truthy!)**, `~2 = -3` (truthy!)

Tact `Bool` is a real boolean. This pattern is about **FunC** and FunC
called from Tact via `asm`.

## Detection

```func
;; VULNERABLE: positive integer as boolean
int is_active = 1;          ;; WRONG: should be -1

if (~ is_active) {
    ;; ~1 = -2, still truthy — this ALWAYS runs
}

int is_valid(int value) {
    if (value > 100) {
        return 1;           ;; WRONG: should return -1
    }
    return 0;
}

int flag = cs~load_uint(1); ;; 0 or 1, not 0 or -1
if (~ flag) { }             ;; broken for flag == 1

int is_owner = equal_slices(sender, owner); ;; already 0 or -1
if (is_owner == 1) { }      ;; NEVER matches
```

**Check:**

- [ ] Booleans are `0` or `-1`, never `1` / `2` / counts
- [ ] Functions that return booleans return `-1` for true
- [ ] `~`, `&`, `|` are not applied to status codes or amounts
- [ ] `load_uint(1)` is converted (`flag ? -1 : 0`) before boolean ops
- [ ] Comparisons use `== 0` / `!= 0` for non-boolean ints, not `if (status)`

## Mitigation

```func
const int TRUE = -1;
const int FALSE = 0;

int is_active = TRUE;
if (~ is_active) { }        ;; ~(-1) = 0, falsy — correct

int flag_bit = cs~load_uint(1);
int flag_bool = flag_bit ? TRUE : FALSE;

if (is_owner) { }           ;; equal_slices already returned -1/0
if (status_code != 0) { }   ;; status codes are not booleans
```

## Common mistakes

1. Storage / message bit loaded with `load_uint(1)` then negated.
2. `== 1` against a FunC comparison result (`-1`).
3. Returning a count (`items.length`) and using it as a boolean with `~`.

## References

building-secure-contracts/not-so-smart-contracts/ton/integer_as_boolean
