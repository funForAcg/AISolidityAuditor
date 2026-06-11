# Real-project demo guide

This guide demonstrates AISolidityAuditor on public Solidity repositories, not only toy examples. For the Glamsterdam grant scope, use `mode: glamsterdam-readiness` so CI produces both Slither triage artifacts and separate readiness outputs.

## Published demo artifacts

| Repository | Commit | Action run | Artifacts |
|------------|--------|------------|-----------|
| [transmissions11/solmate](https://github.com/transmissions11/solmate) | `89365b880c4f3c786bdd453d4b8e8fe410344a69` | [#27331627981](https://github.com/PXLabs-code/AISolidityAuditor/actions/runs/27331627981) | [demo artifacts](demo-artifacts/transmissions11-solmate/89365b880c4f3c786bdd453d4b8e8fe410344a69/README.md) |

Reproduce or refresh a demo locally:

```bash
python scripts/run_real_project_demo.py --demo transmissions11-solmate
```

Run the pinned GitHub Actions demo workflow:

```bash
gh workflow run real-project-demo.yml -f demo=transmissions11-solmate
```

## End-to-end Action chain demo

The artifact-generation workflow above does not exercise SARIF upload or PR comments. The dedicated workflow [.github/workflows/action-e2e-demo.yml](../.github/workflows/action-e2e-demo.yml) proves the **full Action chain** by invoking the composite action (`uses: ./`) against pinned solmate:

1. Composite action runs Slither + Glamsterdam readiness heuristics.
2. SARIF is uploaded to GitHub code scanning (`github/codeql-action/upload-sarif`, category `action-e2e-solmate`).
3. Slither and readiness artifacts are uploaded as Actions artifacts.
4. The Markdown triage report is posted as a PR comment (on `pull_request` events).

It triggers on pull requests touching the workflow, `action.yml`, or this document, and can also be run manually:

```bash
gh workflow run action-e2e-demo.yml
```

### Recorded end-to-end runs

Each row links to evidence that the full chain (Action, SARIF code-scanning upload, artifacts, PR comment) executed against pinned solmate.

| Date | Trigger | Action run | Code scanning | PR comment |
|------|---------|------------|---------------|------------|
| 2026-06-11 | [PR #1](https://github.com/PXLabs-code/AISolidityAuditor/pull/1) (`pull_request`) | [#27333809196](https://github.com/PXLabs-code/AISolidityAuditor/actions/runs/27333809196) | [117 results, category `action-e2e-solmate`](https://github.com/PXLabs-code/AISolidityAuditor/security/code-scanning?query=tool%3AAISolidityAuditor) | [triage report comment](https://github.com/PXLabs-code/AISolidityAuditor/pull/1#issuecomment-4678610108) |

The 2026-06-11 run uploaded the `aisolidityauditor-results` (Slither triage + SARIF) and `aisolidityauditor-glamsterdam-readiness` artifacts, published 117 SARIF results to code scanning under the `AISolidityAuditor` tool name, and posted the Markdown triage report as a PR comment — covering every leg of the Action chain described above.

## Candidate repositories

Use small, well-known, open-source Solidity repositories where CI runtime is reasonable:

| Repository | Why it is useful |
|------------|------------------|
| `OpenZeppelin/openzeppelin-contracts` | Mature library with broad Solidity patterns and mostly clean expected output |
| `transmissions11/solmate` | Compact contracts with common ERC patterns |
| `Uniswap/v4-core` | Real protocol code with Foundry layout and modern Solidity usage |

## GitHub Action demo

Add this workflow to a fork of the target repository. The action is consumed directly from this repository today; a dedicated `AISolidityAuditor-action` repository with a `v1` tag is a planned release within the grant scope.

```yaml
name: Glamsterdam Solidity Readiness Triage

on:
  pull_request:
  push:

permissions:
  contents: read
  security-events: write
  pull-requests: write

jobs:
  audit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: PXLabs-code/AISolidityAuditor@master
        with:
          mode: glamsterdam-readiness
          upload_sarif: "true"
          comment_on_pr: "true"
          include_informational: "false"
```

Optional AI explanations can be enabled by adding `ai_provider` and the matching API key secret. Readiness heuristics do not depend on AI.

## What to capture

For each repository, capture:

- The Action run summary, including the Glamsterdam readiness finding count.
- Uploaded Slither triage artifacts: `audit-report.md`, `findings.json`, `slither.json`, and `audit-results.sarif`.
- Uploaded readiness artifacts: `glamsterdam-readiness-report.md` and `glamsterdam-findings.json`.
- GitHub code-scanning SARIF results, including Glamsterdam-related tags such as `glamsterdam`, `gas-repricing`, `evm-compatibility`, `eth-transfer-logs`, and `contract-size`.
- Optional PR comment.
- Any project setup changes required for Slither to compile the repository.

Confirm that `audit-report.md` and `findings.json` contain Slither evidence only. Readiness heuristics should appear only in the Glamsterdam readiness artifacts and in SARIF entries tagged as readiness heuristics.

## Reporting format

For each real-project run, add a short note with:

- Repository and commit SHA.
- Project path audited.
- Slither version.
- Solidity compiler version.
- Number of Slither findings by severity.
- Number of Glamsterdam readiness findings.
- SARIF tag coverage for Glamsterdam readiness rules.
- AI provider status, if used.
- Known limitations or build assumptions.
