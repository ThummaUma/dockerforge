import { useState } from "react";

function App() {
  const [url, setUrl] = useState("");
  const [loading, setLoading] = useState(false);
  const [logs, setLogs] = useState([]);
  const [dockerfile, setDockerfile] = useState("");
  const [success, setSuccess] = useState(null);

  const handleSubmit = async () => {
    setLoading(true);
    setLogs([]);
    setDockerfile("");
    setSuccess(null);

    try {
      const response = await fetch("http://localhost:8000/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ github_url: url }),
      });

      const data = await response.json();
      setLogs(data.logs);
      setDockerfile(data.dockerfile);
      setSuccess(data.success);
    } catch (err) {
      setLogs(["Connection error. Is the backend running?"]);
    }

    setLoading(false);
  };

  return (
    <div style={{ padding: "40px", fontFamily: "Arial", maxWidth: "900px", margin: "0 auto" }}>
      
      <h1>🐳 DockerForge</h1>
      <p>Paste a GitHub URL and get a working Dockerfile instantly</p>

      <div style={{ display: "flex", gap: "10px", marginBottom: "20px" }}>
        <input
          type="text"
          placeholder="https://github.com/username/repo"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          style={{ flex: 1, padding: "10px", fontSize: "16px", borderRadius: "6px", border: "1px solid #ccc" }}
        />
        <button
          onClick={handleSubmit}
          disabled={loading || !url}
          style={{ padding: "10px 20px", backgroundColor: "#0070f3", color: "white", border: "none", borderRadius: "6px", cursor: "pointer", fontSize: "16px" }}
        >
          {loading ? "Working..." : "Generate"}
        </button>
      </div>

      {logs.length > 0 && (
        <div style={{ backgroundColor: "#1a1a1a", color: "#00ff00", padding: "20px", borderRadius: "8px", marginBottom: "20px" }}>
          <h3 style={{ color: "white" }}>Agent Logs:</h3>
          {logs.map((log, i) => (
            <p key={i} style={{ margin: "4px 0", fontFamily: "monospace" }}>
              ▶ {log}
            </p>
          ))}
        </div>
      )}

      {dockerfile && (
        <div>
          <h3 style={{ color: success ? "green" : "red" }}>
            {success ? "✅ Build Successful!" : "❌ Build Failed after 3 attempts"}
          </h3>
          <h3>Generated Dockerfile:</h3>
          <pre style={{ backgroundColor: "#f4f4f4", padding: "20px", borderRadius: "8px", overflow: "auto", border: "1px solid #ddd" }}>
            {dockerfile}
          </pre>
          <button
            onClick={() => navigator.clipboard.writeText(dockerfile)}
            style={{ padding: "8px 16px", cursor: "pointer" }}
          >
            Copy Dockerfile
          </button>
        </div>
      )}
    </div>
  );
}

export default App;