import { Finding } from "../api";
import SeverityBadge from "./SeverityBadge";

export default function FindingCard({ finding }: { finding: Finding }) {
  const location =
    finding.file && finding.line
      ? `${finding.file}:${finding.line}`
      : finding.file || "unknown";

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
        {finding.contract && <> · Contract: {finding.contract}</>}
        {finding.function && <> · Function: {finding.function}</>}
      </div>

      {finding.ai_expanded && finding.ai.ai_success ? (
        <>
          {finding.ai.provider && (
            <p style={{ color: "var(--text-muted)", fontSize: "0.85rem" }}>
              AI provider: <code>{finding.ai.provider}</code>
            </p>
          )}
          <p><strong>Problem:</strong> {finding.ai.problem}</p>
          <p style={{ marginTop: "0.5rem" }}><strong>Impact:</strong> {finding.ai.impact}</p>
          <p style={{ marginTop: "0.5rem" }}><strong>Recommendation:</strong> {finding.ai.recommendation}</p>
        </>
      ) : (
        <>
          {finding.ai_expanded && finding.ai.error && (
            <p style={{ color: "var(--text-muted)", fontSize: "0.85rem", marginBottom: "0.5rem" }}>
              AI explanation unavailable: {finding.ai.error}
            </p>
          )}
          <p>{finding.description}</p>
        </>
      )}

      {!finding.ai_expanded && (
        <p style={{ marginTop: "0.5rem", color: "var(--text-muted)", fontSize: "0.85rem" }}>
          AI explanation skipped (exceeds limit)
        </p>
      )}

      <div style={{ marginTop: "0.75rem", fontSize: "0.8rem", color: "var(--text-muted)" }}>
        Slither: <code>{finding.detector}</code>
      </div>
    </div>
  );
}
