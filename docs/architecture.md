# 架构说明

## 概述

AISolidityAuditor 是单体应用：Python FastAPI 后端 + React 前端，通过子进程调用 Slither，通过 HTTP 调用 OpenAI 兼容 API 进行 AI 解释。

## 数据流

```
用户上传 ZIP
  → 解压到 /data/jobs/{taskId}/project/
  → Slither --json 输出 slither.json
  → 解析为 findings.json（标准化）
  → AI 逐条解释（最多 20 条）
  → 生成 report.md
  → 前端轮询展示
```

## 组件

| 组件 | 职责 |
|------|------|
| `upload.py` | ZIP 校验、安全解压 |
| `slither.py` | 调用 Slither CLI、解析 JSON |
| `ai.py` | OpenAI 兼容 API 解释 |
| `report.py` | Markdown 报告生成 |
| `audit.py` | 审计流水线编排 |
| `storage.py` | 文件系统任务存储 |
| `cleanup.py` | 过期任务目录清理 |

## API

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/v1/audits` | 上传 ZIP |
| GET | `/api/v1/audits/{taskId}` | 任务状态 |
| GET | `/api/v1/audits/{taskId}/findings` | 发现项列表 |
| GET | `/api/v1/audits/{taskId}/report` | Markdown 报告 |
| GET | `/api/v1/audits/{taskId}/slither` | Slither 原始 JSON |
| GET | `/api/health` | 健康检查 |

## 部署

- 开发：后端 `uvicorn` + 前端 `vite dev`（代理 /api）
- 生产：`docker compose up` 单容器，前端静态文件由 FastAPI 托管

## 安全

- ZIP 路径穿越防护
- 禁止符号链接
- 文件大小限制（10 MB）
- API Key 不落盘、不写日志
- 上传接口按 IP 限流（内存计数器）

## 任务清理

`cleanup.py` 在应用启动时与每小时定时任务中执行，删除超过 `JOB_RETENTION_HOURS`（默认 24h）的任务目录。

## 已知局限

- 非正式审计，AI 可能误释
- 仅静态分析，不覆盖业务逻辑漏洞
- 复杂 Foundry/Hardhat 项目可能需要手动调整 ZIP
