import { useEffect, useMemo, useState } from "react";
import type { ChangeEventHandler } from "react";
import {
  CartesianGrid,
  Line,
  LineChart,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { TimelineSnapshot } from "../../types/metrics";

function formatDate(ts: number) {
  const d = new Date(ts * 1000);
  const hours = String(d.getHours()).padStart(2, "0");
  const minutes = String(d.getMinutes()).padStart(2, "0");
  return `${hours}:${minutes} ${d.getDate()}/${d.getMonth() + 1}`;
}

type TimelineCanvasProps = {
  snapshots: TimelineSnapshot[];
};

type Severity = "Stable" | "Elevated" | "High" | "Critical";

type Thresholds = {
  p50: number;
  p75: number;
  p90: number;
};

type TimelinePoint = {
  time: string;
  churn: number;
  delta: number;
  severity: Severity;
  isAnomaly: boolean;
  commitMessage: string;
  author: string;
  filesChanged: number;
};

type TooltipEntry = {
  value: number;
  payload: TimelinePoint;
};

type StableTooltipProps = {
  active?: boolean;
  payload?: TooltipEntry[];
  label?: string;
};

const SEVERITY_COLORS: Record<Severity, string> = {
  Stable: "#3b82f6",
  Elevated: "#f59e0b",
  High: "#ef4444",
  Critical: "#991b1b",
};
const LINE_COLOR = "#3b82f6";

function percentile(sortedValues: number[], p: number) {
  if (sortedValues.length === 0) {
    return 0;
  }

  const index = (sortedValues.length - 1) * p;
  const lower = Math.floor(index);
  const upper = Math.ceil(index);

  if (lower === upper) {
    return sortedValues[lower] ?? 0;
  }

  const lowerValue = sortedValues[lower] ?? 0;
  const upperValue = sortedValues[upper] ?? lowerValue;
  return lowerValue + (upperValue - lowerValue) * (index - lower);
}

function getSeverity(churn: number, thresholds: Thresholds): Severity {
  if (churn <= thresholds.p50) return "Stable";
  if (churn <= thresholds.p75) return "Elevated";
  if (churn <= thresholds.p90) return "High";
  return "Critical";
}

function TimelineTooltip({ active, payload, label }: StableTooltipProps) {
  if (!active || !payload?.length) {
    return null;
  }

  const point = payload[0]?.payload;
  const churnValue = payload[0]?.value;
  const delta = point?.delta ?? 0;
  const deltaColor = delta > 0 ? "#ef4444" : delta < 0 ? "#22c55e" : "#94a3b8";
  const deltaPrefix = delta > 0 ? "+" : "";
  const severityColor = point ? SEVERITY_COLORS[point.severity] : "#94a3b8";

  return (
    <div
      style={{
        background: "rgba(2, 6, 23, 0.92)",
        border: "1px solid rgba(148, 163, 184, 0.28)",
        borderRadius: 10,
        boxShadow: "0 8px 24px rgba(15, 23, 42, 0.45)",
        color: "#cbd5e1",
        padding: "10px 12px",
      }}
    >
      <div style={{ color: "#94a3b8", fontSize: 12, marginBottom: 4 }}>Timestamp</div>
      <div style={{ color: "#e2e8f0", fontSize: 13, marginBottom: 8 }}>{label}</div>
      <div style={{ color: "#94a3b8", fontSize: 12, marginBottom: 4 }}>Commit message</div>
      <div style={{ color: "#f8fafc", fontWeight: 600, marginBottom: 8 }}>{point?.commitMessage ?? "-"}</div>
      <div style={{ color: "#94a3b8", fontSize: 12, marginBottom: 4 }}>Author</div>
      <div style={{ color: "#f8fafc", fontWeight: 600, marginBottom: 8 }}>{point?.author ?? "-"}</div>
      <div style={{ color: "#94a3b8", fontSize: 12, marginBottom: 4 }}>Churn total</div>
      <div style={{ color: "#f8fafc", fontWeight: 600, marginBottom: 8 }}>{churnValue}</div>
      <div style={{ color: "#94a3b8", fontSize: 12, marginBottom: 4 }}>Delta vs previous</div>
      <div style={{ color: deltaColor, fontWeight: 600 }}>{`Delta vs previous: ${deltaPrefix}${delta}`}</div>
      <div style={{ color: "#94a3b8", fontSize: 12, marginTop: 8, marginBottom: 4 }}>Files changed</div>
      <div style={{ color: "#f8fafc", fontWeight: 600, marginBottom: 8 }}>{point?.filesChanged ?? 0}</div>
      <div style={{ color: "#94a3b8", fontSize: 12, marginBottom: 4 }}>Severity</div>
      <div style={{ color: severityColor, fontWeight: 700 }}>{point?.severity ?? "-"}</div>
    </div>
  );
}

export default function TimelineCanvas({ snapshots }: TimelineCanvasProps) {
  const [visibleCount, setVisibleCount] = useState(1);
  const [isPlaying, setIsPlaying] = useState(true);

  const chartData = useMemo(() => {
    const rawPoints = snapshots.map((snap) => ({
      time: formatDate(snap.timestamp),
      churn: snap.churn.total,
      commitMessage:
        (snap as TimelineSnapshot & { commit_message?: string; message?: string }).commit_message ??
        (snap as TimelineSnapshot & { commit_message?: string; message?: string }).message ??
        "N/A",
      author: (snap as TimelineSnapshot & { author?: string }).author ?? "N/A",
      filesChanged:
        (snap as TimelineSnapshot & { files_changed?: number }).files_changed ?? snap.active_files.length,
    }));

    const sortedChurn = rawPoints.map((point) => point.churn).sort((a, b) => a - b);
    const computedThresholds: Thresholds = {
      p50: percentile(sortedChurn, 0.5),
      p75: percentile(sortedChurn, 0.75),
      p90: percentile(sortedChurn, 0.9),
    };

    const enrichedPoints: TimelinePoint[] = rawPoints.map((point, index) => {
      const previousChurn = rawPoints[index - 1]?.churn ?? point.churn;
      const severity = getSeverity(point.churn, computedThresholds);

      return {
        time: point.time,
        churn: point.churn,
        delta: point.churn - previousChurn,
        severity,
        isAnomaly: point.churn >= computedThresholds.p90,
        commitMessage: point.commitMessage,
        author: point.author,
        filesChanged: point.filesChanged,
      };
    });

    return enrichedPoints;
  }, [snapshots]);

  const clampedVisibleCount = chartData.length === 0 ? 0 : Math.max(1, Math.min(visibleCount, chartData.length));
  const visibleData = chartData.slice(0, clampedVisibleCount);
  const maxChurn = useMemo(
    () => chartData.reduce((max, point) => Math.max(max, point.churn), 0),
    [chartData]
  );
  const tdiData = useMemo(
    () => {
      if (chartData.length === 0) {
        return [];
      }

      const binCount = Math.min(50, chartData.length);
      const binSize = chartData.length / binCount;
      const sortedChurn = chartData.map((point) => point.churn).sort((a, b) => a - b);
      const thresholds: Thresholds = {
        p50: percentile(sortedChurn, 0.5),
        p75: percentile(sortedChurn, 0.75),
        p90: percentile(sortedChurn, 0.9),
      };

      return Array.from({ length: binCount }, (_, index) => {
        const start = Math.floor(index * binSize);
        const end = Math.max(start + 1, Math.floor((index + 1) * binSize));
        const slice = chartData.slice(start, Math.min(end, chartData.length));
        const avgChurn =
          slice.reduce((sum, point) => sum + point.churn, 0) / Math.max(1, slice.length);

        return {
          tdi: maxChurn > 0 ? avgChurn / maxChurn : 0,
          severity: getSeverity(avgChurn, thresholds),
        };
      });
    },
    [chartData, maxChurn]
  );

  const currentPoint = clampedVisibleCount > 0 ? chartData[clampedVisibleCount - 1] : undefined;
  const currentSeverity = currentPoint?.severity ?? "Stable";

  useEffect(() => {
    if (!isPlaying || chartData.length === 0) {
      return;
    }

    const interval = window.setInterval(() => {
      setVisibleCount((prev) => {
        if (prev >= chartData.length) {
          window.clearInterval(interval);
          return prev;
        }
        return prev + 1;
      });
    }, 200);

    return () => {
      window.clearInterval(interval);
    };
  }, [chartData.length, isPlaying]);

  useEffect(() => {
    if (chartData.length === 0) {
      const resetEmptyTimeout = window.setTimeout(() => {
        setVisibleCount(0);
      }, 0);
      return () => {
        window.clearTimeout(resetEmptyTimeout);
      };
    }

    const clampTimeout = window.setTimeout(() => {
      setVisibleCount((prev) => Math.max(1, Math.min(prev, chartData.length)));
    }, 0);
    return () => {
      window.clearTimeout(clampTimeout);
    };
  }, [chartData.length]);

  const handleScrub: ChangeEventHandler<HTMLInputElement> = (event) => {
    setVisibleCount(Number(event.target.value));
    setIsPlaying(false);
  };

  return (
    <div
      style={{
        width: "100%",
        height: 520,
        padding: 16,
        borderRadius: 12,
        background: "#020617",
        boxShadow: "0 8px 20px rgba(15, 23, 42, 0.35)",
        border: "1px solid rgba(148, 163, 184, 0.16)",
      }}
    >
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          gap: 12,
          marginBottom: 6,
        }}
      >
        <h2 style={{ color: "#e2e8f0", margin: 0 }}>Cinematic Timeline (Churn Over Time)</h2>
        <button
          type="button"
          onClick={() => {
            setIsPlaying((prev) => !prev);
          }}
          style={{
            border: "1px solid rgba(148, 163, 184, 0.35)",
            background: "rgba(15, 23, 42, 0.8)",
            color: "#e2e8f0",
            borderRadius: 8,
            padding: "6px 12px",
            cursor: "pointer",
            fontWeight: 600,
          }}
        >
          {isPlaying ? "Pause" : "Play"}
        </button>
      </div>

      <div
        style={{
          color: SEVERITY_COLORS[currentSeverity],
          fontSize: 12,
          fontWeight: 700,
          letterSpacing: 0.4,
          marginBottom: 6,
        }}
      >
        {`Current Risk Level: ${currentSeverity.toUpperCase()}`}
      </div>

      <div style={{ color: "#94a3b8", fontSize: 13, marginBottom: 10 }}>
        Viewing: {currentPoint?.time ?? "-"}
      </div>

      <div style={{ marginBottom: 12 }}>
        <input
          type="range"
          min={1}
          max={Math.max(1, chartData.length)}
          value={Math.max(1, clampedVisibleCount)}
          onChange={handleScrub}
          disabled={chartData.length === 0}
          style={{ width: "100%", accentColor: LINE_COLOR, cursor: "pointer" }}
        />
      </div>

      <div style={{ width: "100%", height: 340 }}>
        <ResponsiveContainer>
          <LineChart data={visibleData}>
            <CartesianGrid stroke="rgba(148, 163, 184, 0.18)" strokeDasharray="3 3" />
            <XAxis
              dataKey="time"
              stroke="#94a3b8"
              tick={{ fill: "#94a3b8", fontSize: 12 }}
              axisLine={{ stroke: "rgba(148, 163, 184, 0.2)" }}
              tickLine={{ stroke: "rgba(148, 163, 184, 0.2)" }}
            />
            <YAxis
              stroke="#94a3b8"
              tick={{ fill: "#94a3b8", fontSize: 12 }}
              axisLine={{ stroke: "rgba(148, 163, 184, 0.2)" }}
              tickLine={{ stroke: "rgba(148, 163, 184, 0.2)" }}
            />
            {visibleData
              .filter((point) => point.isAnomaly)
              .map((point) => (
                <ReferenceLine
                  key={`anomaly-${point.time}-${point.churn}`}
                  x={point.time}
                  stroke="rgba(239, 68, 68, 0.35)"
                  strokeWidth={1}
                />
              ))}
            <Tooltip
              content={<TimelineTooltip />}
              cursor={{ stroke: "rgba(148, 163, 184, 0.32)", strokeWidth: 1 }}
              wrapperStyle={{ outline: "none" }}
            />
            <Line
              type="monotone"
              dataKey="churn"
              stroke={LINE_COLOR}
              strokeWidth={3}
              dot={(props) => {
                const { cx, cy, payload } = props as {
                  cx?: number;
                  cy?: number;
                  payload?: TimelinePoint;
                };

                if (cx == null || cy == null || !payload) {
                  return null;
                }

                const anomalyRadius = payload.isAnomaly ? 6 : 4;

                return (
                  <circle
                    cx={cx}
                    cy={cy}
                    r={anomalyRadius}
                    fill={payload.isAnomaly ? "#ef4444" : LINE_COLOR}
                    stroke={payload.isAnomaly ? "#fecaca" : "#cbd5e1"}
                    strokeWidth={payload.isAnomaly ? 1.5 : 1}
                    style={
                      payload.isAnomaly
                        ? { filter: "drop-shadow(0 0 8px rgba(239, 68, 68, 0.45))" }
                        : undefined
                    }
                  />
                );
              }}
              activeDot={(props) => {
                const { cx, cy, payload } = props as {
                  cx?: number;
                  cy?: number;
                  payload?: TimelinePoint;
                };

                if (cx == null || cy == null || !payload) {
                  return null;
                }

                const radius = payload.isAnomaly ? 8 : 6;
                const shadow = payload.isAnomaly
                  ? "drop-shadow(0 0 12px rgba(239, 68, 68, 0.55))"
                  : "drop-shadow(0 0 6px rgba(59, 130, 246, 0.3))";

                return (
                  <circle
                    cx={cx}
                    cy={cy}
                    r={radius}
                    fill={payload.isAnomaly ? "#ef4444" : LINE_COLOR}
                    stroke="#f8fafc"
                    strokeWidth={1.5}
                    style={{ filter: shadow }}
                  />
                );
              }}
              isAnimationActive={false}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>

      <div style={{ marginTop: 14 }}>
        <div style={{ color: "#94a3b8", fontSize: 12, fontWeight: 600, marginBottom: 6 }}>
          Technical Debt Index (TDI) Over Time
        </div>
        <div
          style={{
            height: 16,
            width: "100%",
            display: "flex",
            border: "1px solid rgba(148,163,184,0.2)",
            borderRadius: 6,
            overflow: "hidden",
          }}
        >
          {tdiData.map((segment, index) => (
            <div
              key={`tdi-${index}`}
              style={{
                flex: 1,
                background: SEVERITY_COLORS[segment.severity],
                opacity: 0.3 + segment.tdi * 0.7,
              }}
            />
          ))}
        </div>
      </div>
    </div>
  );
}
