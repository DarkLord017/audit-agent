# Report Formatting

## Report Path

Save the report to `{project-name}-solana-audit-report-{timestamp}.md` in the current working directory, where `{project-name}` is the repo root basename and `{timestamp}` is `YYYYMMDD-HHMMSS` at scan time.

## Output Format

````
# 🔐 Security Review — <ProgramName or repo name>

---

## Scope

|                                  |                                                        |
| -------------------------------- | ------------------------------------------------------ |
| **Mode**                         | ALL / default / filename                               |
| **Files reviewed**               | `lib.rs` · `withdraw.rs`<br>`state.rs` · `cpi.rs`      | <!-- list every file, 3 per line -->
| **Confidence threshold (1-100)** | N                                                      |

---

## Findings

[95] **1. <Title>**

`ProgramName.instruction_name` · Confidence: 95

**Description**
<The vulnerable code pattern and why it is exploitable, in 1 short sentence>

**Fix**

```diff
- vulnerable line(s)
+ fixed line(s)
```
---

[82] **2. <Title>**

`ProgramName.instruction_name` · Confidence: 82

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

`ProgramName.instruction_name` · Confidence: 75

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

- **<Title>** — `Program.instruction` — Code smells: <missing signer, unvalidated CPI, non-canonical bump, etc.> — <1-2 sentence description of the trail and what remains unverified>
- **<Title>** — `Program.instruction` — Code smells: <...> — <1-2 sentence description>

---

> ⚠️ This review was performed by an AI assistant. AI analysis can never verify the complete absence of vulnerabilities and no guarantee of security is given. Team security reviews, bug bounty programs, and on-chain monitoring are strongly recommended.

````

**Rules:** Follow the template above exactly. Sort findings by confidence (highest first). Findings below the threshold get a description but no **Fix** block. Draft findings directly in report format — do not re-generate. Keep `ProgramName.instruction_name` in the same `Name.function` shape the breaker parses.
