# Writing a proof

A proof is a test that **fails, or succeeds, only because the bug is real**.
If the test would behave the same on correct code, it proves nothing.

## The shape

One test per finding. Name it after the finding. Prefer TypeScript
`@ton/sandbox` tests. Fence the complete source as ` ```typescript ` in
the report (or ` ```func ` only if the demonstration is a compiled FunC
snippet you actually ran).

```typescript
import { Blockchain, SandboxContract, TreasuryContract } from "@ton/sandbox";
import { Cell, beginCell, toNano, Address } from "@ton/core";
import { compileFunc } from "@ton-community/func-js";
import * as fs from "fs";
import * as path from "path";

const UNZIPPED = "/work/unzipped";
const STDLIB = process.env.FUNC_STDLIB || "/opt/func-stdlib/stdlib.fc";

function sources(p: string): string {
  if (p === "stdlib.fc" || p.endsWith("stdlib.fc")) {
    return fs.readFileSync(STDLIB, "utf8");
  }
  const cands = [
    path.join(UNZIPPED, p),
    path.join(UNZIPPED, "contracts", p),
    path.join(UNZIPPED, "contracts/imports", path.basename(p)),
  ];
  for (const c of cands) {
    if (fs.existsSync(c)) return fs.readFileSync(c, "utf8");
  }
  throw new Error("source not found: " + p);
}

describe("attacker credits via fake notify", () => {
  let blockchain: Blockchain;
  let attacker: SandboxContract<TreasuryContract>;

  beforeEach(async () => {
    blockchain = await Blockchain.create();
    attacker = await blockchain.treasury("attacker");
  });

  it("credits the attacker without a real Jetton transfer", async () => {
    const compiled = await compileFunc({
      targets: ["staking.fc"],
      sources,
    });
    if (compiled.status !== "ok") throw new Error(compiled.message);
    const code = Cell.fromBoc(Buffer.from(compiled.codeBoc, "base64"))[0];

    // 1. ARRANGE — a victim contract holding TON, expecting a real wallet
    const contract = blockchain.openContract(/* wrap code+data */);
    await contract.sendDeploy(attacker.getSender(), toNano("1"));

    // 2. ACT — attacker sends transfer_notification themselves
    const OP_NOTIFY = 0x7362d09c;
    await blockchain.sendMessage(/* internal from attacker, body:
      op, query_id, amount, from_user */);

    // 3. ASSERT — the harm, in numbers
    // expect(credited).toEqual(toNano("1000"));
  });
});
```

If the upload is Tact, compile with `@tact-lang/compiler` or `tact` and
open the generated wrappers. If they shipped Blueprint wrappers, **use
those from `unzipped/wrappers/` as imports** — do not copy them into
`unzipped/`. Tests live in `poc/tests/` or their `tests/`.

Verified working in this container looks like:

```
PASS poc/tests/fakeNotify.spec.ts
  attacker credits via fake notify
    ✓ credits the attacker without a real Jetton transfer (32 ms)
```

## The three parts, always

**Arrange** — set up a state where there is something real to lose. A bug
that only "works" on an empty contract usually is not one. Give the vault
TON via `treasury` + `sendDeploy`.

**Act** — do exactly what the finding claims an attacker can do. Send from
`blockchain.treasury("attacker")`, not from the owner treasury. For fake
notify, the sender of the internal message is the attacker contract, not
the stored Jetton wallet.

**Assert** — assert the *harm*, not the mechanism. Attacker credited
`toNano("1000")` is a proof. `exitCode === 0` is not — plenty of harmless
messages succeed.

Use `@ton/test-utils` `toHaveTransaction` when you need success/failure
and `exitCode`, then still assert balances.

## Two directions a proof can run

**The bug lets something happen that should not.** Write a test that
*passes* — the attacker succeeds. That passing test is the proof.

**The bug blocks something that should work.** Write a test doing the
legitimate thing and show it throws / `success: false`. Quote the
`exitCode`.

Either way, quote the output. A claim of "the test passed" without the
output is not evidence.

## Honest failure

If you cannot build a proof, say why in one line and mark it UNVERIFIED:

- *"their `#include` is not in the tree and not in `$FUNC_STDLIB`"*
- *"needs a live mainnet Jetton, cannot fetch with no network"*
- *"needs two contracts to interact and the second is not in scope"*
- *"tact.config.json wants a compiler not in this image"*
- *"package.json depends on a package not vendored in `$TON_SANDBOX_DIR`"*

Do not:

- assert something trivially true and call it a proof
- mark VERIFIED because the code "obviously" has the bug
- rewrite the contract under review to make your test pass

That last one is the subtle failure. **Never modify anything in
`unzipped/`.** If your test only passes after you changed their code, you
have proved a bug in your code, not theirs.

## Minimal mocks are fine

If the contract expects a Jetton wallet, you do not need a full TEP-74
implementation to prove a missing sender check — sending
`transfer_notification` from `treasury("attacker")` *is* the fake wallet.
Keep mocks in `poc/`, not in `unzipped/`. A mock that does anything
clever becomes the thing you are testing.
