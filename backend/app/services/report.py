from datetime import datetime, timezone

from app.models.schemas import SEVERITY_LABELS, AuditMeta, AuditSummary, Finding

DISCLAIMER = (
    "> **免责声明**：本报告由自动化工具（Slither）与 AI 辅助生成，"
    "仅供参考，不构成正式安全审计。部署前请务必进行人工安全审查。"
)


def _location_str(finding: Finding) -> str:
    if finding.file and finding.line:
        return f"{finding.file}:{finding.line}"
    if finding.file:
        return finding.file
    return "未知"


def build_summary(findings: list[Finding]) -> AuditSummary:
    summary = AuditSummary(total=len(findings))
    for f in findings:
        if f.severity.value == "High":
            summary.high += 1
        elif f.severity.value == "Medium":
            summary.medium += 1
        elif f.severity.value == "Low":
            summary.low += 1
        elif f.severity.value == "Informational":
            summary.informational += 1
        elif f.severity.value == "Optimization":
            summary.optimization += 1
        if f.ai.ai_success:
            summary.ai_explained += 1
    return summary


def generate_report(
    meta: AuditMeta,
    findings: list[Finding],
    slither_version: str = "unknown",
) -> str:
    summary = meta.summary or build_summary(findings)
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    lines = [
        "# 智能合约审计报告",
        "",
        f"- **项目名称**：{meta.filename}",
        f"- **任务 ID**：{meta.task_id}",
        f"- **审计时间**：{now}",
        f"- **工具版本**：Slither {slither_version}",
        f"- **耗时**：{meta.duration_sec:.1f} 秒" if meta.duration_sec else "",
        "",
        "## 摘要",
        "",
        "| 级别 | 数量 |",
        "|------|------|",
        f"| 高危 | {summary.high} |",
        f"| 中危 | {summary.medium} |",
        f"| 低危 | {summary.low} |",
        f"| 信息 | {summary.informational} |",
        f"| 优化建议 | {summary.optimization} |",
        f"| **合计** | **{summary.total}** |",
        f"| AI 已解释 | {summary.ai_explained} |",
        "",
        DISCLAIMER,
        "",
        "## 发现项详情",
        "",
    ]

    if not findings:
        lines.append("*Slither 未检测到安全问题。*")
        lines.append("")
    else:
        for finding in findings:
            label = SEVERITY_LABELS.get(finding.severity, finding.severity.value)
            title = finding.ai.title or finding.detector
            lines.append(f"### [{label}] {title}")
            lines.append("")
            lines.append(f"- **位置**：{_location_str(finding)}")
            if finding.contract:
                lines.append(f"- **合约**：`{finding.contract}`")
            if finding.function:
                lines.append(f"- **函数**：`{finding.function}`")

            if finding.ai_expanded and finding.ai.ai_success:
                lines.append(f"- **问题说明**：{finding.ai.problem}")
                lines.append(f"- **潜在影响**：{finding.ai.impact}")
                lines.append(f"- **修复建议**：{finding.ai.recommendation}")
            elif not finding.ai_expanded:
                lines.append("- **AI 解释**：未展开（超出 AI 解释数量限制）")
                lines.append(f"- **原始描述**：{finding.description}")
            else:
                lines.append(f"- **原始描述**：{finding.description}")

            lines.append(f"- **Slither 检测器**：`{finding.detector}`")
            lines.append("")

    lines.extend([
        "## 附录",
        "",
        f"完整 Slither JSON 输出：`GET /api/v1/audits/{meta.task_id}/slither`",
        "",
        "---",
        "*由 AISolidityAuditor 自动生成*",
    ])

    return "\n".join(line for line in lines if line is not None)
