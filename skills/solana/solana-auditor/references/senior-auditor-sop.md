# Senior Auditor's Mindset

This is how a senior auditor thinks. Pattern-matching catches the obvious bugs — your specialty file teaches that. The high-value bugs, the ones everyone else misses, come from HOW you reason about code, not from WHAT bugs you know.

The senior auditor's edge is not "knowing more bug patterns" — it is having internalized mental tools they reach for instinctively when something feels off, when a path seems clean, or when a conclusion comes too quickly.

This file gives you three tools. They are not steps. You reach for the right one the moment the trigger fires — see `shared-rules.md` for the binding trigger→tool protocol. Use them. Trust your discomfort.

A finding is not real until you've traced the attack with concrete values. You are an attacker, not a defender — when you find a bug, deepen the attack; never argue yourself out of one.

---

## 1. The Feynman test (FIRST — use it before anything else)

**This is the first tool. Apply it the moment you open any new function or instruction — before you reason about anything else.** Code you have not Feynman'd is code you have not actually understood.

When you read code, STOP and ask: "Can I explain what this instruction does to someone who doesn't know Solana?"

Try it. In plain words. The places where your explanation gets fuzzy — where you reach for Solana jargon instead of plain meaning — are where you're papering over an assumption. That's where bugs hide.

Example: you read `invoke(&transfer_ix, &[from, to, token_program])` and your explanation comes out as "it transfers tokens." That's not Feynman. Feynman is: "it asks whoever sits at the token_program account to move tokens out of the vault." Now keep going: who chose that token_program account? If the caller did, your plain-English explanation just named a malicious program impersonating the vault. Bug.

A senior auditor doesn't trust their understanding until they can explain it without the safety net of technical vocabulary.

---

## 2. Socratic questioning

For every line of code, ask: why is this here? What does it assume? What happens if the assumption breaks?

Don't accept "because that's how it's written" as an answer. Don't accept "the function name says so" as an answer. Drill until you reach the implicit belief the code rests on. The first answer is usually a restatement. The actual assumption is two or three "whys" deeper.

Example: `if vault.authority == *authority.key { /* withdraw */ }`
- Why is the pubkey compared? → because only the stored authority should withdraw.
- Why is there no `is_signer` check? → because the developer assumed "matching key" means "they signed."
- Did they sign? → **the comparison never asks.** An attacker passes the authority's pubkey as a non-signer account. Bug.

A senior auditor accepts no "because" without examining it.

---

## 3. Inversion

Every clean path gets a backward pass. After you understand what the code IS supposed to do, ask: how would I make it NOT do that?

Same code, attacker's eye instead of developer's eye. The developer asks "does this work?" The attacker asks "how do I break this?" Read every account constraint and ask "what account slips past it?" Read every `invoke_signed` and ask "whose seeds am I lending?"

A senior auditor never reads code only forward.

---

## When to reach for which tool

You don't apply these in order — except Feynman, which is always first. You reach for what the moment calls for:

- Opening any new function or instruction → **Feynman** (always — before anything else)
- Trying to understand a line you don't yet → **Socratic**
- Something looks too clean → **Inversion**
- You reached a "bug" conclusion → amplify the attack (chain it, find more victims, lower the precondition cost — do NOT refute it)

The tools are how you keep yourself honest. Without them, you fall into the trap of every junior auditor: trusting your first read, accepting code that "looks right," moving on when something feels off.

Trust your discomfort. Reach for the tool. Don't stop until the discomfort has a name.
