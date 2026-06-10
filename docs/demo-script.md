# Demo 录屏脚本（约 5 分钟）

## 准备

1. `docker compose up --build`
2. 浏览器打开 http://localhost:8000
3. 使用仓库内预置的 `examples/reentrancy-example.zip`（无需手动打包）
4. 准备 OpenAI API Key（或已在 .env 配置）

## 流程

1. **介绍**（30s）
   - 展示首页：「AI 智能合约审计平台」
   - 说明：上传 ZIP → Slither → AI 解释 → 报告

2. **上传**（30s）
   - 拖拽 `reentrancy-example.zip`
   - 输入 API Key（如需要）
   - 点击「开始审计」

3. **等待**（60–120s）
   - 展示任务页状态：Slither 分析中 → AI 解释中
   - 说明无需命令行

4. **结果**（90s）
   - 展示摘要统计（高危/中危等）
   - 切换「发现项」标签，展示 AI 解释的重入漏洞
   - 切换「审计报告」标签，展示 Markdown 报告
   - 点击「下载报告」

5. **收尾**（30s）
   - 强调：开源、可自托管、Ethereum 生态
   - 展示 GitHub 仓库与 `docker compose up` 一键部署
