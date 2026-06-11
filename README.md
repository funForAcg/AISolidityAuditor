# AISolidityAuditor

[![CI](https://github.com/PXLabs-code/AISolidityAuditor/actions/workflows/ci.yml/badge.svg)](https://github.com/PXLabs-code/AISolidityAuditor/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

**Solidity Security Triage Assistant**

Slither-based static analysis with AI-assisted explanations for developer education and early risk review.

AISolidityAuditor turns Slither output into developer-friendly Markdown reports, raw JSON, findings JSON, and SARIF for GitHub code scanning. It is built for early risk triage and learning. It is not a replacement for a professional audit.

## Table of contents

- [Problem](#problem)
- [Who it helps](#who-it-helps)
- [Why this is public-good infrastructure](#why-this-is-public-good-infrastructure)
- [Features](#features)
- [How it works](#how-it-works)
- [Quick start](#quick-start)
- [Demo](#demo)
- [Example reports](#example-reports)
- [GitHub Action](#github-action)
- [Security model](#security-model)
- [Evaluation and benchmark](#evaluation-and-benchmark)
- [Limitations](#limitations)
- [Roadmap](#roadmap)
- [Development](#development)
- [API reference](#api-reference)
- [Configuration](#configuration)
- [Testing](#testing)
- [Documentation](#documentation)
- [Disclaimer](#disclaimer)

## Problem

Slither is one of the most useful static analyzers in the Solidity ecosystem, but its raw output can be difficult for new teams to act on. Early-stage protocols, hackathon teams, grant applicants, and students often need a fast way to understand what a finding means, where it appears in source code, and what kind of manual review is still required.

AISolidityAuditor addresses this gap by combining Slither findings, nearby source-code context, optional AI explanations, and shareable machine-readable outputs.

## Who it helps

- Solidity learners who need plain-English explanations of static-analysis results.
- Hackathon teams and early-stage projects doing pre-review checks before asking for feedback.
- Open-source maintainers who want CI artifacts and SARIF code-scanning results.
- Educators and mentors who need repeatable examples for common vulnerability classes.
- Grant reviewers who want lightweight, reproducible risk triage for submitted code.

## Why this is public-good infrastructure

This project is designed as open infrastructure rather than a closed audit product:

- It preserves raw Slither JSON and never treats AI text as the source of truth.
- It emits SARIF so results can appear in GitHub code scanning.
- It runs as a self-hosted web app or a reusable GitHub Action.
- It includes evaluation fixtures for common Solidity risk patterns.
- It clearly marks manual-review requirements and avoids claiming to replace audits.

## Features

| Feature | Description |
|---------|-------------|
| ZIP upload | Multi-file Solidity projects with safety limits and file allowlists |
| Slither triage | Static analysis, finding deduplication, and severity ordering |
| AI assistance | OpenAI-compatible, Claude, or DeepSeek explanations grounded in source context |
| Markdown report | Top risks, source snippets, folded informational findings |
| SARIF output | GitHub code scanning compatible results |
| GitHub Action | CI triage mode with artifacts, SARIF upload, optional PR comment, and configurable failure policy |
| Evaluation fixtures | 30 sample contracts with expected detectors, severities, SARIF checks, and explanation keywords |
| Glamsterdam readiness | Optional Action mode for Solidity upgrade-readiness triage around gas, EVM, ETH transfer logs, block context, and contract-size watch points |

## How it works

```text
ZIP or GitHub workspace
  -> safe project extraction / checkout
  -> Slither JSON
  -> finding deduplication and severity ordering
  -> source-context extraction
  -> optional AI explanation and validation
  -> Markdown, findings JSON, Slither JSON, SARIF
```

AI explanations are validated for required JSON fields and basic grounding against the Slither finding and source context. Missing or detached explanations are marked low-confidence. All explanations are assistive only and always require manual review.

## Quick start

```bash
git clone https://github.com/PXLabs-code/AISolidityAuditor.git
cd AISolidityAuditor

cp backend/.env.example backend/.env
# Optional: set OPENAI_API_KEY=sk-...
# Or set AI_PROVIDER=claude and ANTHROPIC_API_KEY=sk-ant-...
# Or set AI_PROVIDER=deepseek and DEEPSEEK_API_KEY=sk-...

docker compose up --build
```

Open `http://localhost:8000`.

1. Upload `examples/reentrancy-example.zip`.
2. Optionally provide an AI provider API key.
3. Click **Start Triage**.
4. Review findings, source context, Markdown report, and SARIF output.

If no AI key is configured, Slither triage still completes and the report records why AI explanations were unavailable.

## Demo

A vulnerable reentrancy example is included:

| File | Purpose |
|------|---------|
| `examples/reentrancy/Reentrancy.sol` | Source contract |
| `examples/reentrancy-example.zip` | Ready-to-upload ZIP |
| `examples/evaluation/` | 30 evaluation fixtures covering common risk patterns |

See [docs/demo-script.md](docs/demo-script.md) for a short demo flow.

## Example reports

Generated example reports are available for quick review:

- [Reentrancy report](examples/reports/reentrancy-report.md)
- [Clean contract report](examples/reports/clean-report.md)
- [Multi-finding report](examples/reports/multi-finding-report.md)

These examples show how the project separates Slither findings, source context, AI explanations, confidence, and manual-review requirements.

## GitHub Action

AISolidityAuditor can run as a security triage step in Solidity repositories. It produces:

- `audit-report.md`
- `slither.json`
- `findings.json`
- `audit-results.sarif`
- GitHub Actions artifact
- Optional pull request comment
- Optional SARIF upload to GitHub code scanning

> **Release status**: the composite action currently lives at the root of this repository (`action.yml`) and is referenced as `PXLabs-code/AISolidityAuditor@master`. A dedicated `AISolidityAuditor-action` repository with a stable `v1` tag is a **planned release** and part of the proposed grant scope. Pin a commit SHA for reproducible CI until the tagged release exists.

```yaml
name: Solidity Security Triage

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
          openai_api_key: ${{ secrets.OPENAI_API_KEY }}
          ai_provider: openai
          comment_on_pr: "true"
```

For Claude:

```yaml
- uses: PXLabs-code/AISolidityAuditor@master
  with:
    ai_provider: claude
    anthropic_api_key: ${{ secrets.ANTHROPIC_API_KEY }}
```

For DeepSeek:

```yaml
- uses: PXLabs-code/AISolidityAuditor@master
  with:
    ai_provider: deepseek
    deepseek_api_key: ${{ secrets.DEEPSEEK_API_KEY }}
```

For a no-AI CI gate that fails on High findings and keeps SARIF focused on primary risks:

```yaml
- uses: PXLabs-code/AISolidityAuditor@master
  with:
    upload_sarif: "true"
    comment_on_pr: "true"
    fail_on_high: "true"
    include_informational: "false"
```

For a Glamsterdam readiness run aligned with the current ESP Wishlist:

```yaml
- uses: PXLabs-code/AISolidityAuditor@master
  with:
    mode: glamsterdam-readiness
    upload_sarif: "true"
    comment_on_pr: "true"
    include_informational: "false"
```

Inside this repository the same action can be exercised with `uses: ./`, which is how the end-to-end demo workflow ([.github/workflows/action-e2e-demo.yml](.github/workflows/action-e2e-demo.yml)) validates the full Action, SARIF upload, artifact, and PR comment chain.

This mode emits the normal Slither triage artifacts plus:

- `glamsterdam-readiness-report.md`
- `glamsterdam-findings.json`
- SARIF rule tags such as `glamsterdam`, `gas-repricing`, `evm-compatibility`, `eth-transfer-logs`, and `contract-size`

Each readiness finding carries a rule confidence level (low-confidence rules are intentionally high-recall), a rule rationale, and the related Glamsterdam fork candidates (for example EIP-7732 ePBS, EIP-7928 BALs, EIP-7708 ETH transfer logs). Reviewed matches can be suppressed with inline `// glamsterdam-ignore` markers or a `glamsterdam-baseline.json` file at the scan root.

## Security model

Uploaded ZIP files are treated as untrusted input.

- Rejects path traversal, absolute paths, and symlinks.
- Enforces upload size, file count, single-file, and total extracted-size limits.
- Allows only Solidity sources and common project configuration files.
- Runs Slither with `SLITHER_TIMEOUT_SEC`.
- Stores each job in an isolated directory.
- Docker Compose uses a read-only root filesystem, tmpfs `/tmp`, dropped Linux capabilities, `no-new-privileges`, and process/memory/CPU limits.
- Does not persist or log user-provided AI keys.
- Preserves raw Slither output for independent review.
- Marks every result as requiring manual review, including successful AI explanations.

See [docs/threat-model.md](docs/threat-model.md) and [docs/sandbox.md](docs/sandbox.md).

## Evaluation and benchmark

The evaluation suite turns `examples/evaluation/` into a CI-backed harness. It runs Slither against the fixture contracts, checks expected detector IDs and severities, verifies SARIF generation, and validates deterministic grounded explanation payloads through the same grounding guard used for AI responses.

See [docs/benchmark-report.md](docs/benchmark-report.md) for the raw Slither vs AISolidityAuditor benchmark plan and the fixture expansion backlog.

## ESP Wishlist alignment

The current small-grant scope is a **Glamsterdam Solidity Readiness Triage Toolkit**. It builds on AISolidityAuditor to help Ethereum builders review Solidity projects for patterns that may need attention as Glamsterdam candidates evolve, including gas repricing, EVM/opcode assumptions, native ETH transfer logs, block context assumptions, and contract-size discussions.

See [docs/grant-one-pager.md](docs/grant-one-pager.md) for the 6-8 week grant scope.

## Limitations

- Not a formal audit and not a substitute for professional review.
- Static analysis cannot reliably detect business-logic bugs.
- AI explanations can be incomplete or wrong, even with grounding checks.
- Complex Foundry or Hardhat projects may need manual ZIP preparation.
- Current scope is Solidity/EVM projects.

## Roadmap

Near-term:

1. Publish a dedicated `AISolidityAuditor-action` repository and `v1` tag.
2. Add SARIF severity tuning and detector-specific docs links.
3. Add 2-3 real-project Action demo runs with report, JSON, and SARIF artifacts.
4. Improve Foundry and Hardhat project detection.
5. Add generated example reports for more detector classes.

Longer-term:

1. Add multi-tool aggregation, such as Slither plus Aderyn.
2. Add source-aware false-positive triage.
3. Add local/offline LLM support.
4. Add Etherscan contract import.
5. Add PDF export.

## Development

### Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/macOS
pip install -r requirements-dev.txt
uvicorn app.main:app --reload --port 8000 --app-dir .
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`; Vite proxies `/api` to the backend.

## API reference

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/v1/audits` | Upload ZIP (`file`, optional `api_key`, optional `ai_provider`) |
| `GET` | `/api/v1/audits/{taskId}` | Task status |
| `GET` | `/api/v1/audits/{taskId}/findings` | Findings with AI and source-context fields |
| `GET` | `/api/v1/audits/{taskId}/report` | Markdown report |
| `GET` | `/api/v1/audits/{taskId}/sarif` | SARIF for GitHub code scanning |
| `GET` | `/api/v1/audits/{taskId}/slither` | Raw Slither JSON |
| `GET` | `/api/health` | Slither, solc, and AI provider configuration |

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `DATA_DIR` | `./data/jobs` | Job storage directory |
| `AI_PROVIDER` | `openai` | Default AI provider (`openai`, `claude`, or `deepseek`) |
| `OPENAI_API_KEY` | empty | OpenAI-compatible API key |
| `OPENAI_BASE_URL` | `https://api.openai.com/v1` | OpenAI-compatible endpoint |
| `OPENAI_MODEL` | `gpt-4o-mini` | OpenAI-compatible model |
| `ANTHROPIC_API_KEY` | empty | Claude API key |
| `CLAUDE_MODEL` | `claude-3-5-haiku-latest` | Claude model |
| `DEEPSEEK_API_KEY` | empty | DeepSeek API key |
| `DEEPSEEK_BASE_URL` | `https://api.deepseek.com/v1` | DeepSeek OpenAI-compatible endpoint |
| `DEEPSEEK_MODEL` | `deepseek-chat` | DeepSeek model |
| `MAX_UPLOAD_MB` | `10` | Maximum ZIP upload size |
| `MAX_ZIP_FILES` | `200` | Maximum extracted file count |
| `MAX_ZIP_FILE_MB` | `2` | Maximum uncompressed size for one ZIP member |
| `MAX_EXTRACTED_MB` | `30` | Maximum total uncompressed ZIP size |
| `SLITHER_TIMEOUT_SEC` | `120` | Slither subprocess timeout |
| `MAX_AI_FINDINGS` | `20` | Max findings to explain with AI |
| `JOB_RETENTION_HOURS` | `24` | Auto-cleanup age |
| `CORS_ORIGINS` | localhost origins | Allowed CORS origins |

## Testing

```bash
cd backend
ruff check app tests
pytest tests -v

cd ../frontend
npm run build

cd ..
docker build -f docker/Dockerfile .
```

Docker-based verification is useful for grant reviewers and contributors who do not have local Python, Node, Slither, or solc installed:

```bash
# Build the production image, including frontend assets and Slither runtime.
docker build -f docker/Dockerfile .

# Run backend tests in a disposable Python container with solc installed.
docker run --rm -v "$PWD:/workspace" -w /workspace/backend python:3.11-slim bash -lc "\
  apt-get update && apt-get install -y --no-install-recommends curl git build-essential && \
  curl -fsSL https://github.com/ethereum/solidity/releases/download/v0.8.20/solc-static-linux -o /usr/local/bin/solc && \
  chmod +x /usr/local/bin/solc && \
  pip install -r requirements-dev.txt && \
  ruff check app tests && \
  pytest tests -v"
```

PowerShell equivalent:

```powershell
docker build -f docker/Dockerfile .
docker run --rm -v "${PWD}:/workspace" -w /workspace/backend python:3.11-slim bash -lc "apt-get update && apt-get install -y --no-install-recommends curl git build-essential && curl -fsSL https://github.com/ethereum/solidity/releases/download/v0.8.20/solc-static-linux -o /usr/local/bin/solc && chmod +x /usr/local/bin/solc && pip install -r requirements-dev.txt && ruff check app tests && pytest tests -v"
```

The test suite covers upload safety, Slither parsing, finding deduplication, AI output validation, source-context extraction, SARIF generation, report generation, evaluation fixture metadata, and CI-backed evaluation runs when Slither and solc are available.

## Documentation

| Document | Description |
|----------|-------------|
| [docs/architecture.md](docs/architecture.md) | System design and data flow |
| [docs/threat-model.md](docs/threat-model.md) | ZIP upload security model |
| [docs/sandbox.md](docs/sandbox.md) | Docker sandbox boundaries and hardening roadmap |
| [docs/benchmark-report.md](docs/benchmark-report.md) | Evaluation and benchmark plan |
| [docs/demo-script.md](docs/demo-script.md) | Demo recording guide |
| [docs/real-project-demo.md](docs/real-project-demo.md) | Real public Solidity repository demo guide |
| [docs/grant-one-pager.md](docs/grant-one-pager.md) | Ethereum grant summary |

## Disclaimer

This tool provides automated assistance only. It is not a formal security audit. AI explanations may be incomplete or inaccurate. Always perform manual review before deploying contracts to mainnet.

## License

[MIT](LICENSE)
