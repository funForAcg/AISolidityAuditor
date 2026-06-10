# AISolidityAuditor

[![CI](https://github.com/funForAcg/AISolidityAuditor/actions/workflows/ci.yml/badge.svg)](https://github.com/funForAcg/AISolidityAuditor/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

**AI-assisted Solidity smart contract audit platform for the Ethereum EVM ecosystem.**

Upload a Solidity project ZIP → run [Slither](https://github.com/crytic/slither) static analysis → get AI-powered human-readable explanations → download a Markdown audit report. No CLI required.

---

## Table of contents

- [Why AISolidityAuditor?](#why-aisolidityauditor)
- [Features](#features)
- [How it works](#how-it-works)
- [Quick start (Docker)](#quick-start-docker)
- [Demo](#demo)
- [Project structure](#project-structure)
- [Development](#development)
- [API reference](#api-reference)
- [Configuration](#configuration)
- [Testing](#testing)
- [Security](#security)
- [Known limitations](#known-limitations)
- [Roadmap](#roadmap)
- [Documentation](#documentation)
- [Disclaimer](#disclaimer)
- [License](#license)

---

## Why AISolidityAuditor?

Slither is the industry-standard static analyzer for Solidity, but its output is aimed at security experts. Independent developers and small teams often struggle to understand findings and know how to fix them.

AISolidityAuditor bridges that gap:

- **Slither** finds real issues with battle-tested detectors
- **AI** translates each finding into plain English (problem, impact, recommendation)
- **Reports** are generated automatically and ready to share

The project is designed as a **solo-maintainable MVP**: single repo, single process, filesystem storage, no database, no microservices. Docker makes it easy to self-host and demo for Ethereum ecosystem grants.

---

## Features

| Feature | Description |
|---------|-------------|
| ZIP upload | Multi-file Solidity projects with `import` dependencies |
| Slither analysis | Subprocess invocation with JSON output parsing |
| AI explanations | OpenAI-compatible API; up to 20 findings per audit |
| Audit report | Markdown preview + download |
| Web UI | Upload, live status, findings list, report view |
| Self-hosted | One-command Docker deploy with Slither + solc preinstalled |
| Open source | MIT license, full docs, example contracts |

---

## How it works

```
Browser (React)
    │
    ▼  HTTP /api
FastAPI backend
    │
    ├── ZIP extract → /data/jobs/{taskId}/project/
    ├── Slither CLI  → slither.json
    ├── Parse        → findings.json
    ├── AI (LLM)     → enriched findings
    └── Report       → report.md
```

**Task lifecycle:** `pending` → `running_slither` → `running_ai` → `completed` (or `failed`)

The frontend polls task status every 2 seconds until completion.

---

## Quick start (Docker)

**Requirements:** Docker and Docker Compose

```bash
git clone https://github.com/funForAcg/AISolidityAuditor.git
cd AISolidityAuditor

# Optional: set your OpenAI API key
cp backend/.env.example backend/.env
# Edit backend/.env and set OPENAI_API_KEY=sk-...

docker compose up --build
```

Open **http://localhost:8000**

1. Drag and drop `examples/reentrancy-example.zip`
2. Enter your OpenAI API key (or configure it in `.env`)
3. Click **Start Audit**
4. View findings and download the report

> **Note:** After code changes, rebuild the image: `docker compose up --build`. A simple `restart` does not refresh the baked-in frontend.

---

## Demo

A vulnerable reentrancy sample is included for acceptance testing:

| File | Purpose |
|------|---------|
| `examples/reentrancy/Reentrancy.sol` | Source contract |
| `examples/reentrancy-example.zip` | Ready-to-upload ZIP |

See [docs/demo-script.md](docs/demo-script.md) for a 5-minute recording script.

---

## Project structure

```
AISolidityAuditor/
├── backend/                 # FastAPI application
│   ├── app/
│   │   ├── api/             # REST routes
│   │   ├── services/        # upload, slither, ai, report, audit
│   │   ├── models/          # Pydantic schemas
│   │   └── middleware/      # rate limiting
│   └── tests/               # pytest suite (mocked Slither/AI)
├── frontend/                # React + Vite UI
├── docker/                  # Dockerfile
├── docs/                    # architecture, threat model, grant materials
├── examples/                # sample contracts + ZIP
├── docker-compose.yml
└── README.md
```

---

## Development

### Prerequisites

- Python 3.11+ (3.11 recommended; matches Docker image)
- Node.js 20+
- For live audits outside Docker: [Slither](https://github.com/crytic/slither) and `solc`

### Backend

```bash
cd backend
python -m venv .venv

# Windows
.venv\Scripts\activate
# Linux/macOS
source .venv/bin/activate

pip install -r requirements-dev.txt
uvicorn app.main:app --reload --port 8000 --app-dir .
```

Set `PYTHONPATH=.` or run from `backend/` with `--app-dir .`.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open **http://localhost:5173** — Vite proxies `/api` to `http://localhost:8000`.

### Production build (local)

```bash
cd frontend && npm run build
cd ../backend && uvicorn app.main:app --port 8000
```

FastAPI serves `frontend/dist` when present.

---

## API reference

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/v1/audits` | Upload ZIP (`file`, optional `api_key` form field) → `{ "task_id": "..." }` |
| `GET` | `/api/v1/audits/{taskId}` | Task status, progress, summary |
| `GET` | `/api/v1/audits/{taskId}/findings` | Findings with AI fields (when completed) |
| `GET` | `/api/v1/audits/{taskId}/report` | Markdown report (`?download=true` for attachment) |
| `GET` | `/api/v1/audits/{taskId}/slither` | Raw Slither JSON output |
| `GET` | `/api/health` | Slither/solc availability check |

### Example: upload and poll

```bash
# Upload
curl -X POST http://localhost:8000/api/v1/audits \
  -F "file=@examples/reentrancy-example.zip" \
  -F "api_key=$OPENAI_API_KEY"

# Poll status
curl http://localhost:8000/api/v1/audits/{taskId}

# Get report
curl http://localhost:8000/api/v1/audits/{taskId}/report
```

---

## Configuration

Copy [backend/.env.example](backend/.env.example) to `backend/.env` or pass variables via `docker-compose.yml`.

| Variable | Default | Description |
|----------|---------|-------------|
| `DATA_DIR` | `./data/jobs` | Job storage directory |
| `AI_PROVIDER` | `openai` | Default AI provider (`openai` or `claude`) |
| `OPENAI_API_KEY` | — | API key (optional if sent per request) |
| `OPENAI_BASE_URL` | `https://api.openai.com/v1` | OpenAI-compatible endpoint |
| `OPENAI_MODEL` | `gpt-4o-mini` | Model for explanations |
| `ANTHROPIC_API_KEY` | - | Claude API key (optional if sent per request) |
| `CLAUDE_MODEL` | `claude-3-5-haiku-latest` | Claude model for explanations |
| `MAX_UPLOAD_MB` | `10` | Maximum ZIP upload size |
| `SLITHER_TIMEOUT_SEC` | `120` | Slither subprocess timeout |
| `MAX_AI_FINDINGS` | `20` | Max findings to send to AI |
| `JOB_RETENTION_HOURS` | `24` | Auto-cleanup age for job dirs |
| `CORS_ORIGINS` | `http://localhost:5173,...` | Allowed CORS origins |

API keys provided in the web form are used only for that request and are **not** stored or logged.

---

## Testing

```bash
cd backend
pip install -r requirements-dev.txt
pytest tests -v
ruff check app tests
```

Tests mock Slither and AI — no Slither installation required for CI. Coverage includes:

- ZIP upload validation
- Slither JSON parsing
- AI mock responses
- Report generation
- Full pipeline integration

---

## Security

See [docs/threat-model.md](docs/threat-model.md) for details.

- ZIP path traversal and symlink rejection
- 10 MB upload limit
- Per-IP rate limiting on upload endpoint
- Isolated job directories per task
- Automatic cleanup of expired jobs (24h default)

---

## Known limitations

- **Not a formal audit** — automated assistance only; always get manual review before mainnet
- **Static analysis only** — business-logic bugs are out of scope
- **AI may misinterpret** — original Slither output is preserved in reports
- **Complex projects** — Foundry/Hardhat configs may need manual ZIP preparation
- **Ethereum EVM only** — no multi-chain support in MVP

---

## Roadmap

Post-MVP ideas (not yet implemented):

1. GitHub Action for PR audits
2. Foundry / Hardhat project templates
3. Local LLM support (Ollama)
4. Etherscan contract import
5. PDF report export

---

## Documentation

| Document | Description |
|----------|-------------|
| [docs/architecture.md](docs/architecture.md) | System design and data flow |
| [docs/threat-model.md](docs/threat-model.md) | ZIP upload security |
| [docs/demo-script.md](docs/demo-script.md) | Demo recording guide |
| [docs/grant-one-pager.md](docs/grant-one-pager.md) | Ethereum grant summary |

---

## Disclaimer

This tool provides **automated assistance only**. It is not a substitute for a professional security audit. AI explanations may be incomplete or inaccurate. Always perform thorough manual review before deploying contracts to mainnet.

---

## License

[MIT](LICENSE) — see [LICENSE](LICENSE) for details.
