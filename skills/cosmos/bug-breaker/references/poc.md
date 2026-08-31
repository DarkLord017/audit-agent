# Writing a proof

A proof is a test that **fails, or succeeds, only because the bug is real**.
If the test would behave the same on correct code, it proves nothing.

## The shape

One test per finding. Name it after the finding. Fence the complete source
as ` ```go ` or ` ```rust `.

### Cosmos SDK (Go)

```go
package keeper_test

import (
    "testing"

    "github.com/stretchr/testify/require"
)

func TestAttackerDrainsOtherUsersDeposit(t *testing.T) {
    // 1. ARRANGE - a victim with something to lose
    s := setupTest(t) // their suite, or a minimal keepers fixture
    victim := s.addrs[0]
    attacker := s.addrs[1]
    s.fund(victim, "1000000ustake")

    // 2. ACT - the attacker does the thing the finding claims
    _, err := s.msgServer.Withdraw(s.ctx, &types.MsgWithdraw{
        Sender: attacker.String(),
        Amount: sdk.NewInt64Coin("ustake", 1000000),
    })
    require.NoError(t, err)

    // 3. ASSERT - the harm, in numbers
    require.Equal(t, int64(1000000), s.balance(attacker, "ustake"),
        "attacker took the victim's deposit")
    require.Equal(t, int64(0), s.balance(s.moduleAddr, "ustake"),
        "module account drained")
}
```

### CosmWasm (Rust)

```rust
use cosmwasm_std::testing::{mock_dependencies, mock_env, mock_info};
use cosmwasm_std::{coins, Addr, Uint128};

#[test]
fn attacker_drains_other_users_deposit() {
    let mut deps = mock_dependencies();
    // 1. ARRANGE
    instantiate(deps.as_mut(), mock_env(), mock_info("admin", &[]), msg()).unwrap();
    execute(
        deps.as_mut(),
        mock_env(),
        mock_info("victim", &coins(1_000_000, "ustake")),
        ExecuteMsg::Deposit {},
    )
    .unwrap();

    // 2. ACT
    execute(
        deps.as_mut(),
        mock_env(),
        mock_info("attacker", &[]),
        ExecuteMsg::Withdraw {
            amount: Uint128::new(1_000_000),
        },
    )
    .unwrap();

    // 3. ASSERT - the harm
    let victim = query_balance(deps.as_ref(), Addr::unchecked("victim")).unwrap();
    assert_eq!(victim.u128(), 0, "victim lost their deposit");
}
```

Prefer `cosmwasm_std::testing` or `cw-multi-test` in-process. Do not invoke
`cargo wasm` — `/work` is a 1g tmpfs and a wasm build will fill it.

## The three parts, always

**Arrange** — set up a state where there is something real to lose. A bug
that only "works" on an empty module usually is not one.

**Act** — do exactly what the finding claims an attacker can do. The
signer / `info.sender` must be unmistakably not the authority.

**Assert** — assert the *harm*, not the mechanism. `attacker.balance ==
1_000_000` is a proof. `Withdraw did not error` is not — plenty of
harmless handlers succeed.

For consensus bugs (map iteration, non-determinism), assert the observable
disagreement: two orderings of the same inputs produce different store
hashes, events, or emitted packets.

## Two directions a proof can run

**The bug lets something happen that should not.** Write a test that
*passes* — the attacker succeeds. That passing test is the proof.

**The bug blocks something that should work.** Write a test doing the
legitimate thing and show it errors. Quote the error.

Either way, quote the output. A claim of "the test passed" without the
output is not evidence.

## Honest failure

If you cannot build a proof, say why in one line and mark it UNVERIFIED:

- *"their go.mod needs modules not in the image cache, GOPROXY=off"*
- *"Cargo.lock wants crates not vendored; cargo --offline failed"*
- *"needs a running wasmd node, cannot start one with no network"*
- *"needs two contracts to interact and the second is not in scope"*
- *"compile filled the 1g /work tmpfs"*

Do not:

- assert something trivially true and call it a proof
- mark VERIFIED because the code "obviously" has the bug
- rewrite the module under review to make your test pass

That last one is the subtle failure. **Never modify anything in
`unzipped/`.** If your test only passes after you changed their code, you
have proved a bug in your code, not theirs.

## Minimal mocks are fine

If the keeper needs a `BankKeeper` to construct, write a 30-line mock in
your test file. That is setup, not modification. Keep it minimal — a mock
that does anything clever becomes the thing you are testing. CosmWasm:
`mock_dependencies()` is enough for most execute-path bugs; reach for
`cw-multi-test` only when you need bank/wasm host behaviour.
