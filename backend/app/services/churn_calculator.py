from __future__ import annotations

from typing import Any

from app.models.file_metrics import ChurnWindow, FileMetrics


class ChurnCalculator:
    def __init__(self, window_seconds: int = 86400) -> None:
        self.window_seconds = max(1, int(window_seconds))

    def calculate(
        self,
        commits: list[Any] | None = None,
        snapshots: list[Any] | None = None,
    ) -> list[FileMetrics]:
        if commits:
            return self._from_commits(commits)
        if snapshots:
            return self._from_snapshots(snapshots)
        return []

    def calculate_dicts(
        self,
        commits: list[Any] | None = None,
        snapshots: list[Any] | None = None,
    ) -> list[dict[str, Any]]:
        return [metric.to_dict() for metric in self.calculate(commits=commits, snapshots=snapshots)]

    def _from_commits(self, commits: list[Any]) -> list[FileMetrics]:
        totals: dict[str, int] = {}
        windows: dict[str, list[ChurnWindow]] = {}
        last_window_churn: dict[str, int] = {}
        last_window_ts: dict[str, int] = {}

        first_ts = int(self._read(commits[0], "timestamp", 0))
        window_end = first_ts + self.window_seconds
        window_counts: dict[str, int] = {}

        for commit in commits:
            ts = int(self._read(commit, "timestamp", 0))
            while ts > window_end:
                self._flush_window(
                    window_end=window_end,
                    window_counts=window_counts,
                    totals=totals,
                    windows=windows,
                    last_window_churn=last_window_churn,
                    last_window_ts=last_window_ts,
                )
                window_counts = {}
                window_end += self.window_seconds

            touched_files = self._extract_touched_files(commit)
            for path in touched_files:
                window_counts[path] = window_counts.get(path, 0) + 1

        self._flush_window(
            window_end=window_end,
            window_counts=window_counts,
            totals=totals,
            windows=windows,
            last_window_churn=last_window_churn,
            last_window_ts=last_window_ts,
        )

        return self._build_metrics(totals, windows)

    def _from_snapshots(self, snapshots: list[Any]) -> list[FileMetrics]:
        totals: dict[str, int] = {}
        windows: dict[str, list[ChurnWindow]] = {}
        last_window_churn: dict[str, int] = {}
        last_window_ts: dict[str, int] = {}

        for snapshot in snapshots:
            ts = int(self._read(snapshot, "timestamp", 0))
            file_churn = self._extract_snapshot_file_churn(snapshot)
            for path, churn in file_churn.items():
                totals[path] = totals.get(path, 0) + churn
                prev_churn = last_window_churn.get(path, 0)
                prev_ts = last_window_ts.get(path, ts - self.window_seconds)
                dt = max(1, ts - prev_ts)
                velocity = (churn - prev_churn) / dt
                windows.setdefault(path, []).append(
                    ChurnWindow(timestamp=ts, churn=churn, velocity=velocity)
                )
                last_window_churn[path] = churn
                last_window_ts[path] = ts

        return self._build_metrics(totals, windows)

    def _flush_window(
        self,
        window_end: int,
        window_counts: dict[str, int],
        totals: dict[str, int],
        windows: dict[str, list[ChurnWindow]],
        last_window_churn: dict[str, int],
        last_window_ts: dict[str, int],
    ) -> None:
        for path, count in window_counts.items():
            totals[path] = totals.get(path, 0) + count
            prev_churn = last_window_churn.get(path, 0)
            prev_ts = last_window_ts.get(path, window_end - self.window_seconds)
            dt = max(1, window_end - prev_ts)
            velocity = (count - prev_churn) / dt
            windows.setdefault(path, []).append(
                ChurnWindow(timestamp=window_end, churn=count, velocity=velocity)
            )
            last_window_churn[path] = count
            last_window_ts[path] = window_end

    @staticmethod
    def _read(item: Any, key: str, default: Any) -> Any:
        if isinstance(item, dict):
            return item.get(key, default)
        return getattr(item, key, default)

    def _extract_touched_files(self, commit: Any) -> set[str]:
        paths: set[str] = set()
        file_changes = self._read(commit, "file_changes", [])
        for change in file_changes:
            path = str(self._read(change, "path", "")).strip()
            if path:
                paths.add(path)

        if paths:
            return paths

        files = self._read(commit, "files", self._read(commit, "files_modified", []))
        if isinstance(files, int):
            return paths
        for file_entry in files:
            path = str(file_entry).strip()
            if path:
                paths.add(path)
        return paths

    def _extract_snapshot_file_churn(self, snapshot: Any) -> dict[str, int]:
        for key in ("file_churn", "churn_by_file", "windowed_churn"):
            value = self._read(snapshot, key, None)
            if isinstance(value, dict):
                out: dict[str, int] = {}
                for path, churn in value.items():
                    path_str = str(path).strip()
                    if not path_str:
                        continue
                    out[path_str] = int(churn or 0)
                return out
        return {}

    @staticmethod
    def _build_metrics(
        totals: dict[str, int],
        windows: dict[str, list[ChurnWindow]],
    ) -> list[FileMetrics]:
        metrics: list[FileMetrics] = []
        for path in sorted(totals.keys()):
            series = windows.get(path, [])
            latest_velocity = series[-1].velocity if series else 0.0
            metrics.append(
                FileMetrics(
                    path=path,
                    total_churn=totals[path],
                    windowed_churn=tuple(series),
                    churn_velocity=latest_velocity,
                )
            )
        return metrics


def calculate_file_churn(
    commits: list[Any] | None = None,
    snapshots: list[Any] | None = None,
    window_seconds: int = 86400,
) -> list[FileMetrics]:
    return ChurnCalculator(window_seconds=window_seconds).calculate(
        commits=commits,
        snapshots=snapshots,
    )
