import { useMemo } from "react";

type FileMetric = {
  path: string;
  total_churn: number;
  windowed_churn: number[];
  churn_velocity: number;
};

type HotspotPanelProps = {
  fileMetrics: FileMetric[];
};

function getIntensityColor(ratio: number) {
  const clamped = Math.max(0, Math.min(1, ratio));
  const hue = 210 - clamped * 210;
  return `hsl(${hue}, 90%, 55%)`;
}

export default function HotspotPanel({ fileMetrics }: HotspotPanelProps) {
  const topFiles = useMemo(
    () => [...fileMetrics].sort((a, b) => b.total_churn - a.total_churn).slice(0, 10),
    [fileMetrics]
  );

  const maxChurn = useMemo(
    () => topFiles.reduce((max, file) => Math.max(max, file.total_churn), 0),
    [topFiles]
  );

  return (
    <section
      style={{
        background: "#020617",
        border: "1px solid rgba(148, 163, 184, 0.16)",
        borderRadius: 16,
        boxShadow: "0 0 40px rgba(56, 189, 248, 0.12)",
        padding: 18,
      }}
    >
      <h3 style={{ color: "#e2e8f0", margin: "0 0 12px", fontSize: 18 }}>Architectural Hotspots</h3>

      {topFiles.length === 0 ? (
        <p style={{ color: "#94a3b8", margin: 0 }}>No file metrics available.</p>
      ) : (
        <div style={{ display: "grid", gap: 10 }}>
          {topFiles.map((file) => {
            const ratio = maxChurn > 0 ? file.total_churn / maxChurn : 0;
            const width = `${Math.max(4, ratio * 100)}%`;
            const color = getIntensityColor(ratio);

            return (
              <div
                key={file.path}
                style={{
                  background: "rgba(15, 23, 42, 0.7)",
                  border: "1px solid rgba(148, 163, 184, 0.14)",
                  borderRadius: 12,
                  padding: "10px 12px",
                  transition: "transform 160ms ease, border-color 160ms ease, box-shadow 160ms ease",
                }}
                onMouseEnter={(event) => {
                  event.currentTarget.style.transform = "translateY(-1px)";
                  event.currentTarget.style.borderColor = "rgba(56, 189, 248, 0.36)";
                  event.currentTarget.style.boxShadow = "0 0 18px rgba(56, 189, 248, 0.16)";
                }}
                onMouseLeave={(event) => {
                  event.currentTarget.style.transform = "translateY(0)";
                  event.currentTarget.style.borderColor = "rgba(148, 163, 184, 0.14)";
                  event.currentTarget.style.boxShadow = "none";
                }}
              >
                <div
                  style={{
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "space-between",
                    gap: 12,
                    marginBottom: 8,
                  }}
                >
                  <span
                    title={file.path}
                    style={{
                      color: "#cbd5e1",
                      fontSize: 13,
                      overflow: "hidden",
                      textOverflow: "ellipsis",
                      whiteSpace: "nowrap",
                      flex: 1,
                    }}
                  >
                    {file.path}
                  </span>
                  <span style={{ color: "#f8fafc", fontWeight: 600, fontSize: 13 }}>
                    {file.total_churn}
                  </span>
                </div>

                <div
                  style={{
                    height: 8,
                    borderRadius: 999,
                    background: "rgba(30, 41, 59, 0.9)",
                    overflow: "hidden",
                  }}
                >
                  <div
                    style={{
                      width,
                      height: "100%",
                      borderRadius: 999,
                      background: color,
                      boxShadow: `0 0 12px ${color}`,
                      transition: "width 260ms ease, background-color 260ms ease",
                    }}
                  />
                </div>
              </div>
            );
          })}
        </div>
      )}
    </section>
  );
}
