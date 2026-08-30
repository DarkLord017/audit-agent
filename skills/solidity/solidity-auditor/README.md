> **Third-party skill — not authored by this project.**
>
> Created by the [Pashov Audit Group](https://github.com/pashov) and vendored
> here from [pashov/skills](https://github.com/pashov/skills/tree/main/solidity-auditor)
> at commit [`c577eb7`](https://github.com/pashov/skills/commit/c577eb7799c349de0acb187ba00ca98e14e436fd),
> under the MIT licence ([`LICENSE`](./LICENSE)). The content below is upstream's,
> unmodified. See [`ATTRIBUTION.md`](./ATTRIBUTION.md) for provenance and how to
> update it.

# Solidity Auditor

A security agent with a simple mission - findings in minutes, not weeks.

Built for:

- **Solidity devs** who want a security check before every commit
- **Security researchers** looking for fast wins before a manual review
- **Just about anyone** who wants an extra pair of eyes.

Not a substitute for a formal audit - but the check you should never skip.

## Demo

_Portrayed below: finding multiple high-confidence vulnerabilities in a codebase_

![Running solidity-auditor in terminal](https://raw.githubusercontent.com/pashov/skills/main/static/skill_pag.gif)

## Usage

```
Install https://github.com/pashov/skills/ and run solidity auditor on the codebase
```

```
run solidity auditor on *specified files*
```

```
update skill to latest version
```

## Tips

- **Target hot contracts.** Rather than scanning an entire repo, point the tool at the 2-5 contracts you're actively changing. Smaller scope means denser context for each agent and higher-signal findings.
- **Run more than once.** LLM output is non-deterministic — each run can surface different vulnerabilities. Two or three passes over the same code often catch things a single pass misses.
