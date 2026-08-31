# Go tests in this container

`go` is installed and works. **There is no network.** Module downloads
die with `GOPROXY=off`.

## The flags you always need

```
GOPROXY=off GOSUMDB=off go test ./... -count=1 -timeout 120s
```

`GOPROXY=off` is already in the environment. Do not set it back. Do not
run `go get`, `go mod download`, or `go mod tidy` expecting the network
to fill gaps.

`$GOMODCACHE` is `/opt/go/pkg/mod` and already holds cosmos-sdk, ibc-go,
cometbft, and their graphs as of image build. If their `go.mod` wants a
module or version that is not there, the test will fail with
`missing go.sum entry` or `module lookup disabled`. That is UNVERIFIED —
do not fake it.

## Use their project, not yours

If `unzipped/` contains a `go.mod`, **build against their module**. It
carries the SDK version, replace directives and module path their code
needs. Nothing else will compile it. Write tests in `poc/go/` and
`replace` their module path to `../unzipped` (adjust the relative path).
**Never modify `unzipped/`** — not even to add a `*_test.go`.

Only if they shipped no `go.mod` do you use `poc/go/` as a stub
module. You will almost certainly still be UNVERIFIED without their
module path — say so.

## Failures you will actually hit

| Symptom | Cause | Do this |
|---|---|---|
| `GOPROXY=off` / `module lookup disabled` | missing cache entry | mark UNVERIFIED; never `go get` |
| `missing go.sum entry` | they did not vendor / lock | UNVERIFIED |
| `undefined: …` / type mismatch | SDK version skew vs image cache | try their `go.mod` version if it is cached; else UNVERIFIED |
| `panic: please specify a Cosmos SDK version` | test helper expects app wiring | write a narrower keeper-level test, or UNVERIFIED |
| Their whole suite fails | pre-existing breakage, not yours | `go test -run TestYourPoc` only |

## Run only your test

Their suite may be broken, slow, or noisy. Scope every run:

```
GOPROXY=off go test ./x/foo/keeper -run TestAttackerDrainsOtherUsersDeposit -count=1 -v
```

`-v` shows logs, which is what you need to show *why* it failed.

## Compiling is not proving

`go test -c` succeeding means nothing about the finding. Only a test that
runs and demonstrates the claimed behaviour counts. See
[poc.md](poc.md).

## Never modify unzipped/

Do not `go mod tidy` their tree. Do not edit keepers to make a test
compile. Do not add files under `unzipped/`. Tests live in `poc/go/`
with a `replace` against their module path. If the test still cannot
compile without writing inside `unzipped/`, stop and mark UNVERIFIED.
