# Shared Scan Rules

## Bundle contents

Your bundle is concatenated files: all in-scope source code, the SOP (HOW to think), your specialty agent (WHAT to look for), and these shared rules (output format, dedup tags, AND mandatory mental tool protocol). Agent 1's bundle also includes the state and advanced Cosmos catalogs.

Read the whole bundle once at the start. The bundle contains all in-scope source. Use Read/Grep only for cross-file searches or out-of-scope context (vendor/, testdata/, test/, mocks/) — do not re-read in-scope files for the initial scan.

When matching names, check Go exported and unexported forms (`MsgFoo` / `msgFoo`, `BeginBlocker` / `beginBlock`) and CosmWasm entry points (`execute`, `sudo`, `reply`, `instantiate`).

## Mental tool protocol — MANDATORY

The three tools in `senior-auditor-sop.md` are NOT optional. Each tool has a specific trigger. **When the trigger fires, you MUST emit the corresponding marker in your output stream BEFORE continuing.** No skipping. The markers live in your working text — they do NOT go into the FINDING/LEAD output blocks.

### Triggers → required markers

| Trigger (the condition) | Marker (required immediately, literal `[Tool: ...]` syntax) | Content |
|---|---|---|
| You open a new function, Msg handler, keeper method, or CosmWasm entry point | `[Feynman: <name>]` | Explain what it does in plain English — no Go/Cosmos jargon, no `sdk.Context`/`keeper`/`WasmMsg`/`SubMsg`. Use as many sentences as you need until the explanation is solid. If your wording slips back to jargon, you're papering over an assumption — keep going. Wherever your plain-English explanation gets fuzzy, mark that spot — that is where bugs hide. |
| You stop on a line whose purpose isn't immediately clear | `[Socratic: <file:line> — why?]` | A one-line question that drills past "because that's how it's written." If your first answer is a restatement of the code, ask again. Stop when the answer exposes the implicit belief the code rests on. |
| A code path reads as clean / a check looks sufficient / a guard looks correct | `[Inversion: <function>]` | Three concrete attacker moves that attempt to defeat the path. Specific addresses/values/states, not abstractions. |

### Rules

1. **Triggers are not optional.** If the condition fires, the marker follows. Always. No skipping.
2. **Use the literal `[Tool: ...]` syntax.** The orchestrator greps your output for these tags after the run.
3. **You may emit a marker without a trigger.** Extra Feynman / Inversion markers are fine. You may NOT skip a marker after its trigger fired.
4. **The protocol applies to reasoning depth, not output volume.** Heavy use of these tools is what produces the audit work. Skipping them = surface-level scanning, which is the failure mode of every junior auditor.

The orchestrator verifies marker counts after every run. Skipped markers downgrade the value of your findings and are recorded as workflow violations.

## Cross-module patterns

When you find a bug in one module or contract, **weaponize that pattern across every other in-scope file.** Search by function name AND by code pattern. Finding map iteration in `x/foo` BeginBlocker means you check every other module's BeginBlocker / EndBlocker. Missing a repeat instance is an audit failure.

After scanning: escalate every finding to its worst exploitable variant (chain halt may hide fund theft). Then revisit every function where you found something and attack the other branches.

## Do not report

Admin-only / authority-only functions doing authority things that the docs claim. Standard Cosmos tradeoffs (governance can change params, validators can censor). Self-harm-only bugs. "The authority can rug" without a concrete mechanism beyond the documented authority. CLI, query, and gRPC-gateway code that is not on the consensus path. Compiler/linter nits.

## Output

Return findings as structured blocks:

FINDINGs have concrete, unguarded, exploitable attack paths. LEADs have real code smells with partial paths — default to LEAD over dropping.

**Every FINDING must have a `proof:` field** — concrete values, traces, or state sequences from the actual code. No proof = LEAD, no exceptions.

**One vulnerability per item.** Same root cause = one item. Different fixes needed = separate items.

```
FINDING | contract: Name | function: func | bug_class: kebab-tag | group_key: Contract | function | bug-class
path: caller → function → state change → impact
proof: concrete values/trace demonstrating the bug
description: one sentence
fix: one-sentence suggestion

LEAD | contract: Name | function: func | bug_class: kebab-tag | group_key: Contract | function | bug-class
code_smells: what you found
description: one sentence explaining trail and what remains unverified
```

`contract:` is the Go module (`x/foo`) or CosmWasm crate/contract name. `function:` is the Msg handler, ABCI hook, or CosmWasm entry point. The `group_key` enables deduplication: `Name | functionName | bug_class`. Agents may add custom fields.
