# Grant 一页纸

## Problem

Slither 是 Ethereum 生态广泛使用的静态分析工具，但其输出面向安全专家，中小开发团队难以理解告警含义并采取修复行动，导致漏洞仍可能进入主网。

## Solution

**AISolidityAuditor** — 开源、可自托管的 Web 平台：

1. 上传 Solidity 项目 ZIP
2. 自动运行 Slither 检测
3. AI 将每条 finding 翻译为中文可读说明（问题、影响、修复建议）
4. 自动生成 Markdown 审计报告

## Impact

- 降低智能合约安全自查门槛
- 与 Slither 官方生态互补，不重复造轮子
- 开源 MIT，Docker 一键部署，无厂商锁定

## Open Source

- GitHub 公开仓库
- MIT License
- 完整文档：架构、威胁模型、已知局限
- 示例合约与 Demo 录屏

## Roadmap (Post-MVP)

1. GitHub Action PR 自动审计
2. Foundry/Hardhat 模板支持
3. 多模型 / 本地 LLM（Ollama）
4. Etherscan 合约地址拉取
