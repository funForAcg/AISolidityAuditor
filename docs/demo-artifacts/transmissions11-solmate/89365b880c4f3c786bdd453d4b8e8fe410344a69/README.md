# Real-project demo: transmissions11/solmate

## Repository

- **Repo**: `https://github.com/transmissions11/solmate`
- **Commit SHA**: `89365b880c4f3c786bdd453d4b8e8fe410344a69`
- **Project path (Slither)**: `.`
- **Project path (readiness heuristics)**: `src`

## Action run

- **Workflow run**: https://github.com/PXLabs-code/AISolidityAuditor/actions/runs/27331627981
- **Mode**: `glamsterdam-readiness`
- **Generated at**: 2026-06-11T07:40:41.686782+00:00

## Results

- **Slither findings (reported)**: 5
- **Glamsterdam readiness findings**: 106
- **Glamsterdam SARIF rules**: 5

## Slither summary (informational excluded)

| Severity | Count |
|----------|------:|
| High | 1 |
| Medium | 1 |
| Low | 3 |
| **Total reported** | **5** |

## Readiness summary (`src/`)

| Detector | Count |
|----------|------:|
| `glamsterdam-gas-sensitive-loop` | 31 |
| `glamsterdam-low-level-evm` | 43 |
| `glamsterdam-eth-transfer-assumption` | 12 |
| `glamsterdam-block-context` | 17 |
| `glamsterdam-contract-size-watch` | 3 |

## Artifacts

- `audit-report.md` — Slither triage only
- `findings.json` — Slither findings only
- `slither.json` — raw Slither JSON
- `audit-results.sarif` — merged SARIF with tool/source metadata
- `glamsterdam-readiness-report.md` — readiness heuristics only
- `glamsterdam-findings.json` — readiness findings only
- `run-metadata.json` — machine-readable metadata

## Setup notes

- solmate is a Foundry project (`solc 0.8.15`).
- Workflow runs `forge build` before Slither on the repo root.
- Readiness heuristics scan `src/` only.
- `include_informational: false` in the demo workflow, so informational Slither findings are omitted from `findings.json` and `audit-report.md`.
