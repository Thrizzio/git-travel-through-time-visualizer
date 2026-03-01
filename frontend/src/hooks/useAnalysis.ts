import { useCallback, useState } from "react";
import type { TimelineSnapshot } from "../types/metrics";

export type FileMetric = {
  path: string;
  total_churn: number;
  windowed_churn: number[];
  churn_velocity: number;
};

type AnalyzeResponse = {
  status: string;
  snapshots?: TimelineSnapshot[];
  summary?: {
    file_metrics?: FileMetric[];
    total_commits?: number;
  };
};

export function useAnalysis() {
  const [snapshots, setSnapshots] = useState<TimelineSnapshot[]>([]);
  const [fileMetrics, setFileMetrics] = useState<FileMetric[]>([]);
  const [totalCommits, setTotalCommits] = useState(0);
  const [processingTimeSeconds, setProcessingTimeSeconds] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const runAnalysis = useCallback(async (repoPath: string) => {
    setLoading(true);
    setError(null);

    const startTime = performance.now();

    try {
      const res = await fetch("https://git-travel-through-time-visualizer.onrender.com/analyze", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ repo_path: repoPath }),
      });

      if (!res.ok) {
        throw new Error("Failed to analyze repository");
      }

      const json = (await res.json()) as AnalyzeResponse;
      const elapsedSeconds = (performance.now() - startTime) / 1000;

      setSnapshots(json.snapshots ?? []);
      setFileMetrics(json.summary?.file_metrics ?? []);
      setTotalCommits(json.summary?.total_commits ?? 0);
      setProcessingTimeSeconds(elapsedSeconds);
    } catch (err) {
      const message = err instanceof Error ? err.message : "Unknown analysis error";
      setError(message);
    } finally {
      setLoading(false);
    }
  }, []);

  return {
    snapshots,
    fileMetrics,
    totalCommits,
    processingTimeSeconds,
    loading,
    error,
    runAnalysis,
  };
}
