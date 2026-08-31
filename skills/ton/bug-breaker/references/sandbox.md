# FunC, Tact, and @ton/sandbox in this container

`func-js` (also on PATH as `func`), `tact`, `jest`, and `@ton/sandbox` are
installed. **There is no network.** That changes how you compile and how
you resolve npm packages.

`/work` is a 1g tmpfs. `@ton/sandbox` is in-process — keep PoCs small. Do
not try to talk to mainnet or testnet.

## Environment

| Variable | Value |
|---|---|
| `TON_SANDBOX_DIR` | `/opt/ton-sandbox` (vendored `node_modules`) |
| `NODE_PATH` | `/opt/ton-sandbox/node_modules` |
| `FUNC_STDLIB` | `/opt/func-stdlib/stdlib.fc` |
| PATH | includes `/opt/ton-sandbox/node_modules/.bin` |

`NODE_PATH` is how Jest and `compileFunc` resolve `@ton/*` without
`npm install`. If a test still cannot find a module, symlink:

```
ln -s /opt/ton-sandbox/node_modules poc/node_modules
```

Never `npm install`. It will fail DNS.

## The commands you actually run

FunC (WASM compiler; `func` is a symlink to `func-js`):

```
func-js "$FUNC_STDLIB" unzipped/contracts/wallet.fc --boc /tmp/wallet.boc
```

Tact:

```
tact --config unzipped/tact.config.json
```

If there is no `tact.config.json`, compile the file only when the image
compiler accepts a single input; otherwise mark UNVERIFIED.

Sandbox tests (Jest + ts-jest, already in `$TON_SANDBOX_DIR`):

```
cd poc && jest tests/fakeNotify.spec.ts --offline=false
```

Jest has no package-offline mode; **npm** is what must stay offline.
`NODE_PATH` is enough. From their Blueprint tree:

```
cd unzipped && blueprint test -- tests/fakeNotify.spec.ts
```

`blueprint test` is a Jest wrapper. If it tries to fetch plugins, stop and
run `jest` directly with `NODE_PATH`.

## Use their project, not yours

If `unzipped/` contains `package.json`, `tact.config.json`, or
`blueprint.config.ts`, **work inside their project**. It carries compile
targets, wrappers and Jest config their code needs. Put your tests in
their `tests/` directory (adding files is allowed; editing `.fc` / `.tact`
is not).

Point `NODE_PATH` at the vendored modules. If their `package.json` names a
dependency that is not under `/opt/ton-sandbox/node_modules`, you cannot
fetch it — mark those findings **UNVERIFIED**.

Only if they shipped none of those markers do you use `poc/`, which is
scaffolded with `tests/`, `tsconfig.json`, `jest.config.js`, and a
`node_modules` symlink to the vendored tree. Compile their sources from
`/work/unzipped/` via the resolver in [poc.md](poc.md).

## Failures you will actually hit

| Symptom | Cause | Do this |
|---|---|---|
| `Could not resolve host` / npm errors | trying to install | never `npm install`; mark UNVERIFIED if a dep is missing |
| `source not found` / `#include` | stdlib or local import | map `stdlib.fc` to `$FUNC_STDLIB`; other missing includes → UNVERIFIED |
| `tact` version / config error | pragma wants a compiler not in the image | say so and mark UNVERIFIED |
| `Cannot find module '@ton/sandbox'` | NODE_PATH not applied | export `NODE_PATH=/opt/ton-sandbox/node_modules` or symlink `node_modules` in `poc/` |
| Their whole suite fails | pre-existing breakage, not yours | pass the path of *your* test file only |

## Run only your test

Their suite may be broken, slow, or noisy. Scope every run:

```
jest poc/tests/fakeNotify.spec.ts
```

Quote the assertion failure or the passing test name. Traces from
`@ton/sandbox` (`print: true` on `Blockchain.create` only if you need them)
are how you show *why* it failed.

## Compiling is not proving

`func-js` / `tact` succeeding means nothing about the finding. Only a test
that runs and demonstrates the claimed behaviour counts. See
[poc.md](poc.md).
