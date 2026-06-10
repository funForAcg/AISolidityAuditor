import { useState, useRef, DragEvent } from "react";
import { useNavigate } from "react-router-dom";
import { createAudit } from "../api";

export default function HomePage() {
  const navigate = useNavigate();
  const fileRef = useRef<HTMLInputElement>(null);
  const [file, setFile] = useState<File | null>(null);
  const [apiKey, setApiKey] = useState("");
  const [aiProvider, setAiProvider] = useState<"openai" | "claude">("openai");
  const [dragging, setDragging] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  function handleFile(f: File) {
    if (!f.name.toLowerCase().endsWith(".zip")) {
      setError("Only .zip Solidity project archives are supported");
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
      setError("Please select a ZIP file first");
      return;
    }
    setLoading(true);
    setError("");
    try {
      const { task_id } = await createAudit(file, apiKey || undefined, aiProvider);
      navigate(`/audit/${task_id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="container">
      <div style={{ textAlign: "center", marginBottom: "2rem" }}>
        <h1 style={{ fontSize: "2rem", fontWeight: 700, marginBottom: "0.5rem" }}>
          AI Smart Contract Audit
        </h1>
        <p style={{ color: "var(--text-muted)", maxWidth: 560, margin: "0 auto" }}>
          Upload a Solidity project ZIP for Slither static analysis and AI-powered
          explanations, then get an audit report automatically.
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
                {(file.size / 1024).toFixed(1)} KB · Click to change file
              </div>
            </>
          ) : (
            <>
              <div style={{ fontSize: "2rem", marginBottom: "0.5rem" }}>📦</div>
              <div style={{ fontWeight: 500 }}>Drag a ZIP here, or click to browse</div>
              <div style={{ color: "var(--text-muted)", fontSize: "0.85rem", marginTop: "0.25rem" }}>
                Max 10 MB, must include .sol files
              </div>
            </>
          )}
        </div>

        <div style={{ marginTop: "1.25rem" }}>
          <label style={{ display: "block", marginBottom: "0.4rem", fontSize: "0.9rem" }}>
            AI Provider
          </label>
          <select value={aiProvider} onChange={(e) => setAiProvider(e.target.value as "openai" | "claude")}>
            <option value="openai">OpenAI compatible</option>
            <option value="claude">Claude</option>
          </select>
        </div>

        <div style={{ marginTop: "1rem" }}>
          <label style={{ display: "block", marginBottom: "0.4rem", fontSize: "0.9rem" }}>
            API Key (optional, for AI explanations)
          </label>
          <input
            type="password"
            placeholder={aiProvider === "claude" ? "sk-ant-..." : "sk-..."}
            value={apiKey}
            onChange={(e) => setApiKey(e.target.value)}
          />
          <p style={{ color: "var(--text-muted)", fontSize: "0.8rem", marginTop: "0.35rem" }}>
            Key is used only for this request and is not stored. You can also set it in server .env.
          </p>
        </div>

        {error && <div className="error-box">{error}</div>}

        <button
          className="btn-primary"
          style={{ width: "100%", marginTop: "1.25rem" }}
          disabled={loading || !file}
          onClick={onSubmit}
        >
          {loading ? "Uploading..." : "Start Audit"}
        </button>
      </div>
    </div>
  );
}
