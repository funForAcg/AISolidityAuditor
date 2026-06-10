import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import ReactMarkdown from "react-markdown";
import {
  AuditStatusResponse,
  Finding,
  getAuditStatus,
  getFindings,
  getReport,
  getReportDownloadUrl,
} from "../api";
import FindingCard from "../components/FindingCard";

const POLL_INTERVAL = 2000;

const STATUS_LABELS: Record<string, string> = {
  pending: "排队中",
  running_slither: "Slither 分析中",
  running_ai: "AI 解释中",
  completed: "已完成",
  failed: "失败",
};

export default function AuditPage() {
  const { taskId } = useParams<{ taskId: string }>();
  const [status, setStatus] = useState<AuditStatusResponse | null>(null);
  const [findings, setFindings] = useState<Finding[]>([]);
  const [report, setReport] = useState("");
  const [activeTab, setActiveTab] = useState<"findings" | "report">("findings");
  const [error, setError] = useState("");

  useEffect(() => {
    if (!taskId) return;

    let cancelled = false;
    let timer: ReturnType<typeof setTimeout>;

    async function poll() {
      try {
        const s = await getAuditStatus(taskId!);
        if (cancelled) return;
        setStatus(s);

        if (s.status === "completed") {
          const [f, r] = await Promise.all([
            getFindings(taskId!),
            getReport(taskId!),
          ]);
          if (!cancelled) {
            setFindings(f.findings);
            setReport(r);
          }
          return;
        }

        if (s.status === "failed") return;

        timer = setTimeout(poll, POLL_INTERVAL);
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "加载失败");
        }
      }
    }

    poll();
    return () => {
      cancelled = true;
      clearTimeout(timer);
    };
  }, [taskId]);

  if (!taskId) return null;

  const isRunning =
    status &&
    !["completed", "failed"].includes(status.status);

  return (
    <div className="container">
      <div style={{ marginBottom: "1.5rem" }}>
        <Link to="/" style={{ fontSize: "0.9rem" }}>← 返回上传</Link>
      </div>

      <div className="card" style={{ marginBottom: "1.5rem" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: "1rem" }}>
          <div>
            <h1 style={{ fontSize: "1.35rem", fontWeight: 700 }}>
              审计任务
            </h1>
            <p style={{ color: "var(--text-muted)", fontSize: "0.85rem", fontFamily: "var(--mono)", marginTop: "0.25rem" }}>
              {taskId}
            </p>
            {status?.filename && (
              <p style={{ marginTop: "0.5rem" }}>文件：{status.filename}</p>
            )}
          </div>
          {status && (
            <div style={{ textAlign: "right" }}>
              <div
                style={{
                  fontWeight: 600,
                  color:
                    status.status === "completed"
                      ? "var(--success)"
                      : status.status === "failed"
                        ? "var(--error)"
                        : "var(--accent)",
                }}
              >
                {STATUS_LABELS[status.status] || status.status}
              </div>
              <p style={{ color: "var(--text-muted)", fontSize: "0.85rem", marginTop: "0.25rem" }}>
                {status.progress}
              </p>
              {status.duration_sec != null && (
                <p style={{ color: "var(--text-muted)", fontSize: "0.85rem" }}>
                  耗时 {status.duration_sec}s
                </p>
              )}
            </div>
          )}
        </div>

        {isRunning && (
          <div
            style={{
              marginTop: "1rem",
              padding: "1rem",
              background: "var(--surface-2)",
              borderRadius: "var(--radius)",
              textAlign: "center",
              color: "var(--text-muted)",
            }}
          >
            <div
              style={{
                display: "inline-block",
                width: 20,
                height: 20,
                border: "2px solid var(--border)",
                borderTopColor: "var(--accent)",
                borderRadius: "50%",
                animation: "spin 0.8s linear infinite",
                marginRight: "0.5rem",
                verticalAlign: "middle",
              }}
            />
            正在处理，请稍候...
            <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
          </div>
        )}

        {status?.status === "failed" && (
          <div className="error-box" style={{ marginTop: "1rem" }}>
            {status.error || "审计失败"}
            <div style={{ marginTop: "0.75rem" }}>
              <Link to="/">
                <button className="btn-secondary">重新上传</button>
              </Link>
            </div>
          </div>
        )}

        {status?.summary && status.status === "completed" && (
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fit, minmax(100px, 1fr))",
              gap: "0.75rem",
              marginTop: "1rem",
            }}
          >
            {[
              { label: "高危", value: status.summary.high, color: "var(--high)" },
              { label: "中危", value: status.summary.medium, color: "var(--medium)" },
              { label: "低危", value: status.summary.low, color: "var(--low)" },
              { label: "信息", value: status.summary.informational, color: "var(--info)" },
              { label: "优化", value: status.summary.optimization, color: "var(--opt)" },
              { label: "合计", value: status.summary.total, color: "var(--text)" },
            ].map((item) => (
              <div
                key={item.label}
                style={{
                  background: "var(--surface-2)",
                  borderRadius: "var(--radius)",
                  padding: "0.75rem",
                  textAlign: "center",
                }}
              >
                <div style={{ fontSize: "1.5rem", fontWeight: 700, color: item.color }}>
                  {item.value}
                </div>
                <div style={{ fontSize: "0.8rem", color: "var(--text-muted)" }}>
                  {item.label}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {error && <div className="error-box">{error}</div>}

      {status?.status === "completed" && (
        <>
          <div style={{ display: "flex", gap: "0.5rem", marginBottom: "1rem" }}>
            <button
              className={activeTab === "findings" ? "btn-primary" : "btn-secondary"}
              onClick={() => setActiveTab("findings")}
            >
              发现项 ({findings.length})
            </button>
            <button
              className={activeTab === "report" ? "btn-primary" : "btn-secondary"}
              onClick={() => setActiveTab("report")}
            >
              审计报告
            </button>
            <a
              href={getReportDownloadUrl(taskId)}
              download
              style={{ marginLeft: "auto" }}
            >
              <button className="btn-secondary">下载报告 (.md)</button>
            </a>
          </div>

          {activeTab === "findings" && (
            <div>
              {findings.length === 0 ? (
                <div className="card" style={{ textAlign: "center", color: "var(--text-muted)" }}>
                  Slither 未检测到安全问题
                </div>
              ) : (
                findings.map((f) => <FindingCard key={f.id} finding={f} />)
              )}
            </div>
          )}

          {activeTab === "report" && (
            <div className="card markdown-body">
              <ReactMarkdown>{report}</ReactMarkdown>
            </div>
          )}
        </>
      )}
    </div>
  );
}
