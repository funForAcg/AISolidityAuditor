import { Severity } from "../api";

const LABELS: Record<Severity, string> = {
  High: "高危",
  Medium: "中危",
  Low: "低危",
  Informational: "信息",
  Optimization: "优化",
};

export default function SeverityBadge({ severity }: { severity: Severity }) {
  const cls = `badge badge-${severity.toLowerCase()}`;
  return <span className={cls}>{LABELS[severity]}</span>;
}
