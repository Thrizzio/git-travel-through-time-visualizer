import { useEffect, useState } from "react";
import { fetchTimeline } from "../api/client";
import type { TimelineSnapshot } from "../types/metrics";

export function useTimeline() {
  const [data, setData] = useState<TimelineSnapshot[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchTimeline()
      .then(setData)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  return { data, loading, error };
}