"""TON FunC/Tact audit profile: ton-auditor then @ton/sandbox bug-breaker."""

import os

from backend.worker_runner.profiles import (
    AuditProfile,
    Role,
    Toolchain,
    registry,
)

TON_SANDBOX = os.getenv("TON_SANDBOX_DIR", "/opt/ton-sandbox")
FUNC_STDLIB = os.getenv("FUNC_STDLIB", "/opt/func-stdlib/stdlib.fc")

TON_TOOLS = Toolchain(
    key="ton",
    image=os.getenv("WORKER_IMAGE_TON", "evmbench/worker-ton:latest"),
    project_markers=(
        "package.json",
        "tact.config.json",
        "blueprint.config.ts",
    ),
    scaffold_dirs=("tests",),
    scaffold_links=(("node_modules", TON_SANDBOX + "/node_modules"),),
    scaffold_files=(
        (
            "package.json",
            """\
{
  "name": "ton-poc",
  "private": true,
  "scripts": {
    "test": "jest"
  }
}
""",
        ),
        (
            "tsconfig.json",
            """\
{
  "compilerOptions": {
    "target": "ES2020",
    "module": "commonjs",
    "esModuleInterop": true,
    "strict": true,
    "skipLibCheck": true,
    "types": ["jest", "node"]
  }
}
""",
        ),
        (
            "jest.config.js",
            """\
/** @type {import('jest').Config} */
module.exports = {
  preset: 'ts-jest',
  testEnvironment: 'node',
  testPathIgnorePatterns: ['/node_modules/'],
  roots: ['<rootDir>/tests'],
};
""",
        ),
    ),
    briefing=f"""\
## Compiling and testing

If the upload has its own `package.json`, `tact.config.json`, or
`blueprint.config.ts`, **use it**. It carries their compile targets,
wrappers and Jest config, and nothing else will load their contracts the
way they expect. Work inside their project and add your tests to its
`tests/` directory. Do not edit their `.fc`, `.func`, or `.tact` files.

There is no network. Compilers and `@ton/sandbox` are already in this
image. Resolve modules from the vendored tree — never `npm install`:

```
export NODE_PATH={TON_SANDBOX}/node_modules
jest tests/fakeNotify.spec.ts
```

If their tree has no `node_modules`, either rely on `NODE_PATH` or
`ln -s {TON_SANDBOX}/node_modules node_modules` **inside `poc/`** (or
their project root if you are working there). A missing dependency that
is not in the vendored cache means **UNVERIFIED**.

FunC stdlib is `$FUNC_STDLIB` (`{FUNC_STDLIB}`). Map `#include "stdlib.fc"`
to that file. `func` on PATH is `func-js` (WASM), which is what Blueprint
uses.

If the upload has no Blueprint/Tact/npm project, use `{{poc}}/`, where
`node_modules` is linked and tests go in `tests/*.spec.ts`. Compile sources
from `{{source}}/` with `compileFunc` / `tact` as in the breaker skill.

`/work` is a 1g tmpfs. `@ton/sandbox` is in-process — keep PoCs small and
do not try to reach mainnet.

## Tools on PATH

- `func` / `func-js` -- FunC compiler (WASM)
- `tact` -- Tact compiler
- `jest` -- test runner (`ts-jest` is vendored)
- `blueprint` -- TON Blueprint CLI (`blueprint test` wraps Jest)

There is no internet access. `npm install` and `git clone` will fail.
Anything not already installed is not available, so do not try to fetch
dependencies.
""",
)

AUDITOR = Role(
    key="auditor",
    label="Auditor",
    skill="ton-auditor",
    command="/ton-auditor",
    description="Reads the FunC/Tact contracts and reports suspected vulnerabilities.",
    source="https://github.com/trailofbits/skills/tree/main/plugins/building-secure-contracts/skills/ton-vulnerability-scanner",
)

BREAKER = Role(
    key="breaker",
    label="Bug breaker",
    skill="bug-breaker",
    command="/bug-breaker",
    description="Tries to prove each claimed bug with an @ton/sandbox test.",
    max_turns=300,
)

registry.register(
    AuditProfile(
        key="ton",
        label="TON FunC/Tact smart contracts",
        roles=(AUDITOR, BREAKER),
        toolchain=TON_TOOLS,
        include_globs=("**/*.fc", "**/*.func", "**/*.tact"),
        exclude_globs=(
            "**/test/**",
            "**/tests/**",
            "**/wrappers/**",
            "**/node_modules/**",
        ),
        description="Loss-of-funds vulnerabilities in TON contracts, with proofs.",
    )
)
