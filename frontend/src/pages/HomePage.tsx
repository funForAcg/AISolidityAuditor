import { useState, useRef, DragEvent } from "react";
import { useNavigate } from "react-router-dom";
import { createAudit } from "../api";

export default function HomePage() {
  const navigate = useNavigate();
  const fileRef = useRef<HTMLInputElement>(null);
  const [file, setFile] = useState<File | null>(null);
  const [apiKey, setApiKey] = useState("");
  const [dragging, setDragging] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  function handleFile(f: File) {
    if (!f.name.toLowerCase().endsWith(".zip")) {
      setError("仅支持 .zip 格式的 Solidity 项目包");
      return;
    }
    setFile(f);
    setError("");
  }

  function onDrop(e: DragEvent) {
    e.preventDefault();
    setDragging(false);
    const f = e.dataTransfer.files[0];
    if (f) handleFile(f);
  }

  async function onSubmit() {
    if (!file) {
      setError("请先选择 ZIP 文件");
      return;
    }
    setLoading(true);
    setError("");
    try {
      const { task_id } = await createAudit(file, apiKey || undefined);
      navigate(`/audit/${task_id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "上传失败");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="container">
      <div style={{ textAlign: "center", marginBottom: "2rem" }}>
        <h1 style={{ fontSize: "2rem", fontWeight: 700, marginBottom: "0.5rem" }}>
          AI 智能合约审计
        </h1>
        <p style={{ color: "var(--text-muted)", maxWidth: 560, margin: "0 auto" }}>
          上传 Solidity 项目 ZIP，自动运行 Slither 静态分析，
          并由 AI 将安全问题翻译为易懂的中文说明，生成审计报告。
        </p>
      </div>

      <div className="card" style={{ maxWidth: 600, margin: "0 auto" }}>
        <div
          onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
          onDragLeave={() => setDragging(false)}
          onDrop={onDrop}
          onClick={() => fileRef.current?.click()}
          style={{
            border: `2px dashed ${dragging ? "var(--accent)" : "var(--border)"}`,
            borderRadius: "var(--radius)",
            padding: "2.5rem 1.5rem",
            textAlign: "center",
            cursor: "pointer",
            background: dragging ? "rgba(108, 92, 231, 0.05)" : "transparent",
            transition: "border-color 0.15s, background 0.15s",
          }}
        >
          <input
            ref={fileRef}
            type="file"
            accept=".zip"
            hidden
            onChange={(e) => {
              const f = e.target.files?.[0];
              if (f) handleFile(f);
            }}
          />
          {file ? (
            <>
              <div style={{ fontWeight: 600 }}>{file.name}</div>
              <div style={{ color: "var(--text-muted)", fontSize: "0.85rem", marginTop: "0.25rem" }}>
                {(file.size / 1024).toFixed(1)} KB · 点击更换文件
              </div>
            </>
          ) : (
            <>
              <div style={{ fontSize: "2rem", marginBottom: "0.5rem" }}>📦</div>
              <div style={{ fontWeight: 500 }}>拖拽 ZIP 到此处，或点击选择</div>
              <div style={{ color: "var(--text-muted)", fontSize: "0.85rem", marginTop: "0.25rem" }}>
                最大 10 MB，需包含 .sol 文件
              </div>
            </>
          )}
        </div>

        <div style={{ marginTop: "1.25rem" }}>
          <label style={{ display: "block", marginBottom: "0.4rem", fontSize: "0.9rem" }}>
            OpenAI API Key（可选，用于 AI 解释）
          </label>
          <input
            type="password"
            placeholder="sk-..."
            value={apiKey}
            onChange={(e) => setApiKey(e.target.value)}
          />
          <p style={{ color: "var(--text-muted)", fontSize: "0.8rem", marginTop: "0.35rem" }}>
            Key 仅用于当次请求，不会存储。也可在服务端 .env 中配置。
          </p>
        </div>

        {error && <div className="error-box">{error}</div>}

        <button
          className="btn-primary"
          style={{ width: "100%", marginTop: "1.25rem" }}
          disabled={loading || !file}
          onClick={onSubmit}
        >
          {loading ? "上传中..." : "开始审计"}
        </button>
      </div>
    </div>
  );
}
