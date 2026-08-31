# Titanoboa and pytest in this container

`vyper`, `pytest` and Titanoboa (`import boa`) are installed and work.
**There is no network.** Do not fork a chain, do not `pip install`.

`/work` is a 1g tmpfs. Titanoboa is an in-process interpreter — keep PoCs
small. A debug build or a huge fixture dump will blow the disk.

## The command you always run

```
pytest tests/test_foo.py -vv
```

Titanoboa's pytest plugin loads automatically and rolls back EVM state
after each test. You do not pass extra flags for that.

## Use their project, not yours

If `unzipped/` contains a `pytest.ini` or `pyproject.toml`, **work inside
their project**. It carries the pythonpath, fixtures and plugins their
code needs. Put your tests in their test directory.

Only if they shipped no pytest project do you use `poc/`, which is
scaffolded with `conftest.py` exposing `UNZIPPED` (the `{source}/` tree).
Load contracts from there:

```python
from pathlib import Path
import boa

UNZIPPED = Path("/work/unzipped")  # or the conftest UNZIPPED
vault = boa.load(str(UNZIPPED / "Vault.vy"))
```

Constructor args go to `boa.load` after the path:
`boa.load(path, "Name", "SYM", 18)`.

## Failures you will actually hit

| Symptom | Cause | Do this |
|---|---|---|
| `Could not resolve host` / pip errors | trying to install | never `pip install`; mark UNVERIFIED if a dep is missing |
| `vyper.exceptions.VersionException` | pragma wants a compiler not in the image | say so and mark UNVERIFIED |
| `InterfaceViolation` / unknown interface | they import an interface file not in the tree | mark UNVERIFIED; do not invent the interface |
| `FileNotFoundError` on `boa.load` | wrong path | resolve the `.vy` under `unzipped/` with `find` / `grep` |
| Their whole suite fails | pre-existing breakage, not yours | pass the path of *your* test file only |

## Run only your test

Their suite may be broken, slow, or noisy. Scope every run:

```
pytest poc/tests/test_drain.py -vv
```

`-vv` shows assert diffs, which is what you need to show *why* it failed.

## Compiling is not proving

`vyper file.vy` succeeding means nothing about the finding. Only a test
that runs and demonstrates the claimed behaviour counts. See
[poc.md](poc.md).
