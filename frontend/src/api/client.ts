import type { TimelineSnapshot } from "../types/metrics";

const API_BASE =
  "https://git-travel-through-time-visualizer.onrender.com";

/**
 * Trigger backend analysis for a GitHub repo
 */
export async function analyzeRepository(repoUrl: string) {
  const res = await fetch(`${API_BASE}/analyze`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ repo_path: repoUrl }),
  });

  if (!res.ok) {
    throw new Error("Failed to analyze repository");
  }

  return res.json();
}

/**
 * Fetch timeline snapshots after analysis
 */
export async function fetchTimeline(): Promise<TimelineSnapshot[]> {
  const res = await fetch(`${API_BASE}/metrics/timeline`);

  if (!res.ok) {
    throw new Error("Failed to fetch timeline");
  }

  const json = await res.json();

  // Your backend returns { data: [...] }
  return json.data ?? [];
}