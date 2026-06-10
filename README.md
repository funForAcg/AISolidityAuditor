# AISolidityAuditor

AI-assisted Solidity smart contract audit platform for the Ethereum EVM ecosystem.

Upload a Solidity project ZIP → Slither static analysis → AI human-readable explanations → automatic audit report.

## Features (MVP)

- ZIP project upload (multi-file Solidity with imports)
- Slither static analysis
- AI explanations (problem, impact, fix recommendations)
- Markdown audit report (preview + download)
- Web UI — no CLI required

## Quick Start (Docker)

```bash
# Clone and start
git clone <repo-url>
cd AISolidityAuditor
cp backend/.env.example backend/.env   # optional: set OPENAI_API_KEY

docker compose up --build

# Open http://localhost:8000
```

Upload `examples/reentrancy-example.zip` to run a full audit demo.

## Development

### Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # Linux/macOS
pip install -r requirements-dev.txt

# Requires Slither + solc for live audits; tests use mocks
uvicorn app.main:app --reload --port 8000
```

### Tests

```bash
cd backend
pip install -r requirements-dev.txt
pytest tests -v
```

### Frontend

```bash
cd frontend
npm install
npm run dev
# Open http://localhost:5173 (proxies /api to :8000)
```

## API

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/audits` | Upload ZIP (`file`, optional `api_key`) |
| GET | `/api/v1/audits/{taskId}` | Task status |
| GET | `/api/v1/audits/{taskId}/findings` | Findings list |
| GET | `/api/v1/audits/{taskId}/report` | Markdown report |
| GET | `/api/v1/audits/{taskId}/slither` | Raw Slither JSON |
| GET | `/api/health` | Health check |

## Configuration

See [backend/.env.example](backend/.env.example).

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENAI_API_KEY` | — | OpenAI API key (or pass per-request) |
| `OPENAI_MODEL` | `gpt-4o-mini` | Model name |
| `MAX_UPLOAD_MB` | `10` | Max ZIP size |
| `MAX_AI_FINDINGS` | `20` | Max findings to AI-explain |

## 中文快速开始

1. 安装 Docker，运行 `docker compose up --build`
2. 打开 http://localhost:8000
3. 上传 `examples/reentrancy-example.zip`
4. 输入 OpenAI API Key（或在 `.env` 中配置）
5. 等待审计完成，查看发现项与报告

## Architecture

See [docs/architecture.md](docs/architecture.md).

## Disclaimer

This tool provides automated assistance only. It is **not** a substitute for professional security audit. Always perform manual review before mainnet deployment.

## License

MIT
