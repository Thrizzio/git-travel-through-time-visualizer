import { useState } from "react";
import TimelineCanvas from "./components/timeline/TimelineCanvas";
import HotspotPanel from "./components/heatmap/HotspotPanel";
import { useAnalysis } from "./hooks/useAnalysis";

function App() {
  const [repoPath, setRepoPath] = useState("");
  const {
    snapshots,
    fileMetrics,
    totalCommits,
    processingTimeSeconds,
    loading,
    error,
    runAnalysis,
  } = useAnalysis();

  const hasCompleted =
  !loading &&
  !error &&
  snapshots.length > 0;

  return (
    <div
      style={{
        maxWidth: 1200,
        margin: "0 auto",
        padding: "48px 24px",
        color: "#e2e8f0",
      }}
    >
      <header style={{ marginBottom: 24 }}>
        <h1 style={{ margin: 0 }}>Git History Intelligence</h1>
        <p style={{ opacity: 0.68, margin: "8px 0 0" }}>
          Temporal Software Evolution Intelligence Engine
        </p>
      </header>

      <section
        style={{
          display: "flex",
          gap: 12,
          alignItems: "center",
          marginBottom: 16,
          flexWrap: "wrap",
        }}
      >
        <input
          type="text"
          value={repoPath}
          onChange={(e) => {
            setRepoPath(e.target.value);
          }}
          placeholder="Enter repository path"
          style={{
            flex: "1 1 420px",
            minWidth: 280,
            padding: "10px 12px",
            borderRadius: 10,
            border: "1px solid rgba(148, 163, 184, 0.35)",
            background: "#0f172a",
            color: "#e2e8f0",
          }}
        />
        <button
          type="button"
          disabled={loading || !repoPath.trim()}
          onClick={() => {
          if (!repoPath.trim()) return;
          void runAnalysis(repoPath.trim());
          }}
          style={{
            padding: "10px 16px",
            borderRadius: 10,
            border: "1px solid rgba(59, 130, 246, 0.45)",
            background: loading ? "#1e293b" : "#1d4ed8",
            color: "#f8fafc",
            cursor: loading ? "not-allowed" : "pointer",
          }}
        >
          Analyze
        </button>
      </section>

      {loading ? <div>Processing...</div> : null}
      {error ? <div>Error: {error}</div> : null}
      {hasCompleted ? (
        <div style={{ marginBottom: 16 }}>
          <div>{totalCommits} commits analyzed</div>
          <div>Completed in {processingTimeSeconds.toFixed(2)} seconds</div>
        </div>
      ) : null}

      {!loading && !error ? (
        <>
          <section style={{ marginBottom: 18 }}>
            <TimelineCanvas snapshots={snapshots} />
          </section>

          <section style={{ display: "flex", gap: 16, flexWrap: "wrap" }}>
            <div
              style={{
                flex: "1 1 320px",
                minHeight: 340,
                background: "#020617",
                border: "1px solid rgba(148, 163, 184, 0.16)",
                borderRadius: 16,
                boxShadow: "0 0 32px rgba(56, 189, 248, 0.08)",
                padding: 18,
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                color: "#94a3b8",
              }}
            >
              Heatmap visualization coming soon
            </div>

            <div style={{ flex: "1 1 320px" }}>
              <HotspotPanel fileMetrics={fileMetrics} />
            </div>
          </section>
        </>
      ) : null}
    </div>
  );
}

export default App;
