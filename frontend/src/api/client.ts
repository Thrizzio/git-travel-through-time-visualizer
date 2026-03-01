import type { TimelineSnapshot } from "../types/metrics";

export async function fetchTimeline(): Promise<TimelineSnapshot[]> {
  const res = await fetch("https://git-travel-through-time-visualizer.onrender.com");
  if (!res.ok) {
    throw new Error("Failed to fetch timeline");
  }

  const json = await res.json();
  return json.data ?? [];
}