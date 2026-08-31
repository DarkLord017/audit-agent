---
name: algorand-auditor
description: Security audit of Algorand TEAL/PyTeal code while you develop. Trigger on "audit", "check this contract", "review for security". Modes - default (full repo) or a specific filename.
---

# Smart Contract Security Audit

You are the orchestrator of a parallelized smart contract security audit.

This runtime is not Claude Code interactive. Do **not** call `AskUserQuestion`.
Do **not** pick a model for subagents. Omit the `model` parameter on Agent
calls. Do **not** curl a remote VERSION file — there is no network.

## Mode Selection

**Exclude pattern:** skip directories `test/`, `tests/`, `mocks/`, `__pycache__/`,
`.venv/`, `venv/` and files matching `*_test.py`, `test_*.py`, `*Test*.py` or
`*Mock*.py`.

**In-scope files are not "every `.py`".** Include:

- all `*.teal` files (approval programs, clear-state programs, logic signatures)
- only those `*.py` files that are **PyTeal** (or Beaker, which compiles to
  PyTeal). Detect them with `grep`, not by extension.

A file that imports `algosdk` but not `pyteal` / `beaker` is a client script
and is **out of scope**.

- **Default** (no arguments): scan in-scope TEAL + PyTeal using the exclude
  pattern. Use Bash `find` (not Glob), then `grep` for PyTeal imports.
- **`$filename ...`**: scan the specified file(s) only.

**Flags:**

- `--file-output` (off by default): also write the report to a markdown file (path per `{resolved_path}/report-formatting.md`). Never write a report file unless explicitly passed.

### Discover command (default mode)

Run as one Bash snippet. Collect TEAL, then PyTeal `.py` via import grep:

```bash
find . -name '*.teal' \
  -not -path '*/test/*' -not -path '*/tests/*' \
  -not -path '*/mocks/*' -not -path '*/__pycache__/*' \
  -not -path '*/.venv/*' -not -path '*/venv/*'

find . -name '*.py' \
  -not -path '*/test/*' -not -path '*/tests/*' \
  -not -path '*/mocks/*' -not -path '*/__pycache__/*' \
  -not -path '*/.venv/*' -not -path '*/venv/*' \
  -not -name '*_test.py' -not -name 'test_*.py' \
  -print0 | xargs -0 grep -l -E 'from pyteal|import pyteal|from beaker|import beaker' 2>/dev/null || true
```

PyTeal import markers to accept: `from pyteal`, `import pyteal`,
`from pyteal import`, `import beaker`, `from beaker`. Do **not** treat
`from algosdk import` alone as in-scope.

## Orchestration

**Turn 1 — Discover.** In one message, make these parallel tool calls:

a. Bash `find` + `grep` for in-scope `.teal` and PyTeal `.py` files per mode selection
b. Glob for `**/references/hacking-agents/shared-rules.md` — extract the `references/` directory (two levels up) as `{resolved_path}`
c. ToolSearch `select:Agent`
d. Bash `mktemp -d ./.audit-XXXXXX` → store as `{bundle_dir}`

**Turn 2 — Prepare.** In one message, make parallel tool calls: (a) Read `{resolved_path}/report-formatting.md`, (b) Read `{resolved_path}/judging.md`.

Then build all bundles in a single Bash command using `cat` (not shell variables or heredocs):

1. `{bundle_dir}/source.md` — ALL in-scope `.teal` and PyTeal `.py` files, each with a `### path` header and fenced code block (`teal` or `python`).
2. Agent bundles = `source.md` + agent-specific files:

| Bundle                | Appended files (relative to `{resolved_path}`)                                                                                                |
| --------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------- |
| `agent-1-bundle.md`   | `source.md` + `senior-auditor-sop.md` + `hacking-agents/rekey-agent.md` + `hacking-agents/tob-algorand-patterns.md` + `hacking-agents/shared-rules.md` |
| `agent-2-bundle.md`   | `source.md` + `senior-auditor-sop.md` + `hacking-agents/close-remainder-agent.md` + `hacking-agents/tob-algorand-patterns.md` + `hacking-agents/shared-rules.md` |
| `agent-3-bundle.md`   | `source.md` + `senior-auditor-sop.md` + `hacking-agents/group-size-agent.md` + `hacking-agents/tob-algorand-patterns.md` + `hacking-agents/shared-rules.md` |
| `agent-4-bundle.md`   | `source.md` + `senior-auditor-sop.md` + `hacking-agents/clawback-agent.md` + `hacking-agents/tob-algorand-patterns.md` + `hacking-agents/shared-rules.md` |
| `agent-5-bundle.md`   | `source.md` + `senior-auditor-sop.md` + `hacking-agents/clear-state-agent.md` + `hacking-agents/tob-algorand-patterns.md` + `hacking-agents/shared-rules.md` |
| `agent-6-bundle.md`   | `source.md` + `senior-auditor-sop.md` + `hacking-agents/access-control-agent.md` + `hacking-agents/tob-algorand-patterns.md` + `hacking-agents/shared-rules.md` |
| `agent-7-bundle.md`   | `source.md` + `senior-auditor-sop.md` + `hacking-agents/fee-inner-agent.md` + `hacking-agents/tob-algorand-patterns.md` + `hacking-agents/shared-rules.md` |
| `agent-8-bundle.md`   | `source.md` + `senior-auditor-sop.md` + `hacking-agents/economic-security-agent.md` + `hacking-agents/shared-rules.md`                         |
| `agent-9-bundle.md`   | `source.md` + `senior-auditor-sop.md` + `hacking-agents/first-principles-agent.md` + `hacking-agents/shared-rules.md`                          |
| `agent-10-bundle.md`  | `source.md` + `senior-auditor-sop.md` + `hacking-agents/numerical-gap-agent.md` + `hacking-agents/shared-rules.md`                             |
| `agent-11-bundle.md`  | `source.md` + `senior-auditor-sop.md` + `hacking-agents/trust-gap-agent.md` + `hacking-agents/shared-rules.md`                                 |
| `agent-12-bundle.md`  | `source.md` + `senior-auditor-sop.md` + `hacking-agents/flow-gap-agent.md` + `hacking-agents/shared-rules.md`                                  |

Each bundle = source.md + SOP + specialty (+ ToB patterns for agents 1–7) + shared-rules. Agents read the bundle; no Read/Grep needed for the initial scan. Targeted Read/Grep allowed for cross-file investigation.

Print line counts for every bundle and `source.md`. Do NOT inline source code into the Agent call prompt itself.

**Turn 3a — Spawn all 12 agents.** In one message, spawn all 12 agents as **parallel BACKGROUND Agent calls** (`run_in_background=true`). Omit the `model` parameter entirely — do NOT substitute any default. The orchestrator will receive a notification when each agent completes — do NOT poll or sleep. Single phase, no later spawns. Proceed to Turn 3b only after all 12 have notified completion.

Agents 1–9 use the **single-specialty prompt** (Turn 3a-i). Agents 10–12 use the **gap-hunter prompt** (Turn 3a-ii).

**Turn 3a-i — Single-specialty prompt template (agents 1–9, substitute real values):**

```
You are an attacker. Your specialty, mindset, source, and output rules
are in your bundle. Read it fully before producing findings.

Read first:
- {bundle_dir}/agent-N-bundle.md (XXXX lines) — source + SOP + specialty + shared rules.

The bundle contains all in-scope source. Do NOT re-read in-scope files
for the initial scan. Use Read/Grep only for cross-file searches or
out-of-scope context (test/, tests/, mocks/, client SDK scripts).

What a finding looks like:
- file, function (PyTeal def / TEAL label / ABI method)
- root cause — the one-sentence code-level defect
- minimal fix — the smallest change that eliminates the defect
- proof — concrete numbers, a group-txn trace, or quoted TEAL/PyTeal

Without concrete proof, it's a LEAD, not a finding. Leads are honest
about what you couldn't verify — they're not failures, they're
calibration. Emit them.

Don't skim. Don't trust your first read. Trust your discomfort.

Output format: see shared-rules.md inside your bundle.
```

**Turn 3a-ii — Gap-hunter prompt template (agents 10–12, substitute real values):**

```
You are an attacker. Your gap-hunter specialty, mindset, source, and
output rules are in your bundle. Read it fully before producing findings.

Read first:
- {bundle_dir}/agent-N-bundle.md (XXXX lines) — source + SOP + gap-hunter specialty + shared rules.

The bundle contains all in-scope source. Do NOT re-read in-scope files
for the initial scan. Use Read/Grep only for cross-file searches or
out-of-scope context (test/, tests/, mocks/, client SDK scripts).

What a finding looks like:
- file, function
- seam — which two or three lenses combine
- root cause — the one-sentence code-level defect that lives at the seam
- minimal fix — the smallest change that eliminates the defect
- proof — concrete numbers, a trace, or quoted code showing the seam

Without concrete proof of the seam, it's a LEAD, not a finding.
Leads are honest about what you couldn't verify — they're not failures,
they're calibration. Emit them.

Don't skim. Don't trust your first read. Trust your discomfort.

Output format: see shared-rules.md inside your bundle (gap-hunter-specific
output fields are in your specialty file).
```

**Turn 3b — Wait for all 12 agents to complete.** Once every one of the 12 spawned agents has notified completion, proceed to Turn 4. Do NOT proceed to dedup until every agent has finished — let them run to natural completion. Do NOT poll or sleep; act only on completion notifications.

**Turn 4 — Deduplicate, validate & output.** Single-pass: deduplicate all agent results, gate-evaluate, and produce the final report in one turn. Do NOT print an intermediate dedup list — go straight to the report.

1. **Dedup.** Parse every FINDING and LEAD from the 12 agents. Group by `group_key` (Contract | function | bug-class). Exact-match first; merge synonymous bug_class within same (Contract, function). Keep best per group, number sequentially, annotate `[agents: N]`.

   **MANDATORY — Wide-description (group_key).** Merged group with distinct mechanisms (different `fix:`, code-level cause, or attack path) MUST list every mechanism. No dropping. Same function can have multiple coexisting bugs at the same group_key — all MUST appear.

   **MANDATORY — Function-level second pass (after group_key dedup).** Run at (Contract, function), ignoring bug_class. Agents often label coexisting bugs with different bug_class tags but reference multiple mechanisms in the body. For every (Contract, function) with multiple final findings: scan body (description, path, proof, fix) of every constituent for distinct mechanisms across bug_class boundaries. Every mechanism in any constituent body MUST appear in ≥1 final finding.

   **MANDATORY — Function isolation (HARD).** NEVER merge across different `function:` fields. Dedup only within (Contract, function). Different function = different bug. Second pass above stays WITHIN (Contract, function), never across. Treat a TEAL label / ABI method / `on_completion` branch as the function name.

   **MANDATORY — Fix preservation (HARD GATE).** Before writing merged `fix:` on a multi-finding (Contract, function):
   1. Collect every raw `fix:` from agents flagging the tuple.
   2. Group by ADD-lines (`+` lines, or equivalent Assert/assignment).
   3. Distinct if ADD-lines differ in: called function/expression (e.g., `Assert(Txn.rekey_to() == Global.zero_address())` vs `Assert(Global.group_size() == Int(2))`), check direction (validate/restrict/ban), or checked parameter.
   4. ≥2 distinct → present as Option A, B, … — one block per distinct fix, verbatim from agent text (no paraphrase).
   5. Label intuitively: validate / restrict / allow-and-handle / ban-path.

   **Output format when 2+ distinct fixes exist:**

   ```
   **Fix (Option A — <label>)**:

   ```diff
   <verbatim diff from raw agent N1's fix>
   ```

   **Fix (Option B — <label>)**:

   ```diff
   <verbatim diff from raw agent N2's fix>
   ```
   ```

   **Inline check before printing**: count distinct fixes from raw for this (Contract, function). ≥2 distinct but merged shows 1 → violation, add alternatives.

   **MANDATORY — Completeness (HARD GATE).** Before print: list every unique (Contract, function, bug-class) in any raw FINDING/LEAD across the 12 agents. Every unique (Contract, function) MUST have ≥1 item in final. Zero = silent drop, fix it. Multiple bug-class within same (Contract, function) MAY collapse to one item (wide-description), but the (Contract, function) MUST survive. Print inline before report: `Completeness: N unique (Contract, function) in raw, N covered in final.`

   Composite chains: if A's output feeds B's precondition AND combined impact > either alone, add `Chain: [A] + [B]` at conf = min(A, B). Most audits: 0–2.

2. **Gate.** Run each deduped finding through the four gates in `judging.md` (no skip, no reorder, no revisit after verdict).

   **Single-pass:** every relevant code path ONCE in fixed order (creation / `application_id == 0` → NoOp ABI methods → OptIn → CloseOut → UpdateApplication → DeleteApplication → ClearState → inner txns). One-line verdict: `BLOCKS` / `ALLOWS` / `IRRELEVANT` / `UNCERTAIN`. `UNCERTAIN = ALLOWS`. Commit, no re-examination.

3. **Lead promotion / rejection.**
   - LEAD → FINDING (conf 75) if: full exploit chain in source, OR `[agents: 2+]` demoted (not rejected) same issue.
   - `[agents: 2+]` does NOT override a code path that interrupts attack before harm — demote to LEAD if execution uncertain.
   - No deployer-intent reasoning — what code allows, not how deployer might use it.

4. **Format/print** per `report-formatting.md`. Exclude rejected. If `--file-output`: also write to file. Do NOT re-read source to "verify the most critical claim" — agents did that, dedup filtered. Re-verification costs ~5min, rarely changes verdicts. Skip.

5. **Auto-clean.** After print (and `--file-output` write): `rm -rf {bundle_dir}`. Bundle dir = transient build state, not an artifact. Don't skip. For debugging: copy bundle elsewhere before re-running.
