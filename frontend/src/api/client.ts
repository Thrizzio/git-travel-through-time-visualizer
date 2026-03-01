import type { TimelineSnapshot } from "../types/metrics";

export async function fetchTimeline(): Promise<TimelineSnapshot[]> {
  const res = await fetch("http://127.0.0.1:8000/metrics/timeline");
  if (!res.ok) {
    throw new Error("Failed to fetch timeline");
  }

  const json = await res.json();
  return json.data ?? [];
}