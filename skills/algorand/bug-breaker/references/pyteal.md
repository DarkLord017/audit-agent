# PyTeal and pytest in this container

`python`, `pytest`, `pyteal`, and `algosdk` are installed and work.
**There is no network and no algod.** That changes what a proof can be.

## Compile their program, do not rewrite it

```python
from pyteal import compileTeal, Mode

teal = compileTeal(approval_program(), mode=Mode.Application, version=8)
Path("poc/approval.teal").write_text(teal)
```

Logic signatures use `mode=Mode.Signature`. Match their `pragma` /
`compileTeal(..., version=N)`. If version is unknown, try 8, then 6.

Write compiled TEAL under `poc/` (or pytest's `tmp_path`). **Never write
into `unzipped/`.**

## Use their project, not yours

If `unzipped/` contains a `pytest.ini` or `pyproject.toml`, **work
inside their project**. It carries `pythonpath`, extras, and fixtures
their compile needs. Put your tests in their tests directory.

Only if they shipped none do you use `poc/`, which is scaffolded with
`conftest.py` exposing `UNZIPPED` at `{source}/`.

There is no internet. `pip install` will fail. If their module imports a
package that is not `pyteal` / `algosdk` / `pytest` (Beaker, for
example), say so and mark UNVERIFIED — do not fake the import.

## Run only your test

Their suite may be broken, slow, or talk to algod. Scope every run:

```
pytest poc/tests/test_rekey.py -vv
# or, inside their project:
pytest tests/test_rekey.py -vv
```

Quote the pytest output in the report.

## Failures you will actually hit

| Symptom | Cause | Do this |
|---|---|---|
| `Could not resolve host` / pip | no network | never pip install; mark UNVERIFIED |
| `ModuleNotFoundError: beaker` | they use Beaker, not in the image | UNVERIFIED, say the missing dep |
| `TealInputError` / compile fail | version or invalid Expr | try version 6 and 8; then UNVERIFIED |
| `goal` / `algod` not found | you tried a live dryrun | do not; prove on compiled TEAL |
| Their whole suite fails | pre-existing breakage | `--` only your test file |

## Compiling is not proving

`compileTeal` succeeding means nothing about the finding. Only a pytest
that runs and demonstrates the claimed behaviour counts. See
[poc.md](poc.md).

`/work` is a **1g tmpfs**. Keep generated TEAL and pytest small. Do not
unpack extra toolchains.
