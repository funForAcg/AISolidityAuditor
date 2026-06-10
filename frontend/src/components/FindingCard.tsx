import { Finding } from "../api";
import SeverityBadge from "./SeverityBadge";

export default function FindingCard({ finding }: { finding: Finding }) {
  const location =
    finding.file && finding.line
      ? `${finding.file}:${finding.line}`
      : finding.file || "未知";

  return (
    <div className="card" style={{ marginBottom: "1rem" }}>
      <div style={{ display: "flex", alignItems: "center", gap: "0.75rem", marginBottom: "0.75rem" }}>
        <SeverityBadge severity={finding.severity} />
        <h3 style={{ fontSize: "1.05rem", fontWeight: 600 }}>
          {finding.ai.title || finding.detector}
        </h3>
      </div>

      <div style={{ color: "var(--text-muted)", fontSize: "0.85rem", marginBottom: "0.75rem" }}>
        <span style={{ fontFamily: "var(--mono)" }}>{location}</span>
        {finding.contract && <> · 合约: {finding.contract}</>}
        {finding.function && <> · 函数: {finding.function}</>}
      </div>

      {finding.ai_expanded && finding.ai.ai_success ? (
        <>
          <p><strong>问题说明：</strong>{finding.ai.problem}</p>
          <p style={{ marginTop: "0.5rem" }}><strong>潜在影响：</strong>{finding.ai.impact}</p>
          <p style={{ marginTop: "0.5rem" }}><strong>修复建议：</strong>{finding.ai.recommendation}</p>
        </>
      ) : (
        <p>{finding.description}</p>
      )}

      {!finding.ai_expanded && (
        <p style={{ marginTop: "0.5rem", color: "var(--text-muted)", fontSize: "0.85rem" }}>
          未进行 AI 展开（超出数量限制）
        </p>
      )}

      <div style={{ marginTop: "0.75rem", fontSize: "0.8rem", color: "var(--text-muted)" }}>
        Slither: <code>{finding.detector}</code>
      </div>
    </div>
  );
}
