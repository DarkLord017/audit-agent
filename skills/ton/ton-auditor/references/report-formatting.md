# Report Formatting

## Report Path

Save the report to `{project-name}-ton-audit-report-{timestamp}.md` in the current working directory, where `{project-name}` is the repo root basename and `{timestamp}` is `YYYYMMDD-HHMMSS` at scan time.

## Output Format

````
# 🔐 Security Review — <ContractName or repo name>

---

## Scope

|                                  |                                                        |
| -------------------------------- | ------------------------------------------------------ |
| **Mode**                         | ALL / default / filename                               |
| **Files reviewed**               | `File1.fc` · `File2.tact`<br>`File3.func` · `File4.fc` | <!-- list every file, 3 per line -->
| **Confidence threshold (1-100)** | N                                                      |

---

## Findings

[95] **1. <Title>**

`ContractName.functionName` · Confidence: 95

**Description**
<The vulnerable code pattern and why it is exploitable, in 1 short sentence>

**Fix**

```diff
- vulnerable line(s)
+ fixed line(s)
```
---

[82] **2. <Title>**

`ContractName.functionName` · Confidence: 82

**Description**
<The vulnerable code pattern and why it is exploitable, in 1 short sentence>

**Fix**

```diff
- vulnerable line(s)
+ fixed line(s)
```
---

< ... all above-threshold findings >

---

[75] **3. <Title>**

`ContractName.functionName` · Confidence: 75

**Description**
<The vulnerable code pattern and why it is exploitable, in 1 short sentence>

---

< ... all below-threshold findings (description only, no Fix block) >

---

Findings List

| # | Confidence | Title |
|---|---|---|
| 1 | [95] | <title> |
| 2 | [82] | <title> |
| 3 | [75] | <title> |

---

## Leads

_Vulnerability trails with concrete code smells where the full exploit path could not be completed in one analysis pass. These are not false positives — they are high-signal leads for manual review. Not scored._

- **<Title>** — `Contract.function` — Code smells: <missing sender check, integer-as-bool, unbounded forward amount, etc.> — <1-2 sentence description of the trail and what remains unverified>
- **<Title>** — `Contract.function` — Code smells: <...> — <1-2 sentence description>

---

> ⚠️ This review was performed by an AI assistant. AI analysis can never verify the complete absence of vulnerabilities and no guarantee of security is given. Team security reviews, bug bounty programs, and on-chain monitoring are strongly recommended.

````

**Rules:** Follow the template above exactly. Sort findings by confidence (highest first). Findings below the threshold get a description but no **Fix** block. Draft findings directly in report format — do not re-generate.

Use `Contract.receive(FooMsg)` / `Contract.op_transfer` as the function name for Tact `receive` blocks and FunC opcode branches. Cite `file.fc:42` or `file.tact:17` in the body when a line is known.
