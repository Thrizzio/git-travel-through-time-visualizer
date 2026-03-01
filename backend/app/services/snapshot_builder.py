from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class SnapshotChurn:
    lines_added: int
    lines_deleted: int
    total: int


@dataclass(frozen=True, slots=True)
class Snapshot:
    timestamp: int
    commit_hash: str
    author: str
    email: str
    message: str
    files_changed: int

    active_files: tuple[str, ...]
    file_sizes: tuple[tuple[str, int], ...]
    churn: SnapshotChurn
    contributor_distribution: tuple[tuple[str, float], ...]
    complexity: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "active_files": list(self.active_files),
            "file_sizes": {path: loc for path, loc in self.file_sizes},
            "churn": {
                "lines_added": self.churn.lines_added,
                "lines_deleted": self.churn.lines_deleted,
                "total": self.churn.total,
            },
            "contributor_distribution": {
                author: share for author, share in self.contributor_distribution
            },
            "complexity": self.complexity,
            "commit_hash": self.commit_hash,
            "author": self.author,
            "email": self.email,
            "message": self.message,
            "files_changed": self.files_changed,
        }


class TemporalSnapshotBuilder:
    def __init__(
        self,
        mode: str = "commit",
        window_seconds: int = 86400,
        complexity_placeholder: float = 0.0,
    ) -> None:
        self.mode = mode
        self.window_seconds = max(1, int(window_seconds))
        self.complexity_placeholder = float(complexity_placeholder)

    def build(self, commits: list[Any]) -> list[Snapshot]:
        return self.build_snapshots(commits)

    def build_snapshots(self, commits: list[Any]) -> list[Snapshot]:
        if not commits:
            return []

        file_sizes: dict[str, int] = {}
        snapshots: list[Snapshot] = []

        window_lines_added = 0
        window_lines_deleted = 0
        contributor_churn: dict[str, int] = {}

        first_timestamp = int(self._read_field(commits[0], "timestamp", 0))
        current_window_end = first_timestamp + self.window_seconds

        for commit in commits:
            timestamp = int(self._read_field(commit, "timestamp", 0))
            commit_hash = str(self._read_field(commit, "hash", ""))
            author_name = str(self._read_field(commit, "author_name", "unknown"))
            author_email = str(self._read_field(commit, "author_email", "unknown"))
            message = str(self._read_field(commit, "message", ""))

            file_changes = self._iter_file_changes(commit)
            files_changed = len(file_changes)

            if self.mode != "commit":
                while timestamp > current_window_end:
                    snapshots.append(
                    self._freeze_snapshot(
                    timestamp=timestamp,
                    commit_hash=commit_hash,
                    author=author_name,
                    email=author_email,
                    message=message,
                    files_changed=files_changed,
                    file_sizes=file_sizes,
                    lines_added=window_lines_added,
                    lines_deleted=window_lines_deleted,
                    contributor_churn=contributor_churn,
                )
            )
            current_window_end += self.window_seconds
            window_lines_added = 0
            window_lines_deleted = 0
            contributor_churn = {}
            current_window_end += self.window_seconds
            window_lines_added = 0
            window_lines_deleted = 0
            contributor_churn = {}

            author_delta = 0
            file_changes = self._iter_file_changes(commit)
            files_changed = len(file_changes)

            for path, added, deleted in file_changes:
                previous_loc = file_sizes.get(path, 0)
                next_loc = previous_loc + added - deleted
                if next_loc <= 0:
                    file_sizes.pop(path, None)
                else:
                    file_sizes[path] = next_loc

                window_lines_added += added
                window_lines_deleted += deleted
                author_delta += added + deleted

            if author_delta > 0:
                contributor_churn[author_name] = contributor_churn.get(author_name, 0) + author_delta

            if self.mode == "commit":
                snapshots.append(
                    self._freeze_snapshot(
                        timestamp=timestamp,
                        commit_hash=commit_hash,
                        author=author_name,
                        email=author_email,
                        message=message,
                        files_changed=files_changed,
                        file_sizes=file_sizes,
                        lines_added=window_lines_added,
                        lines_deleted=window_lines_deleted,
                        contributor_churn=contributor_churn,
                    )
                )
                window_lines_added = 0
                window_lines_deleted = 0
                contributor_churn = {}
            elif timestamp >= current_window_end:
                snapshots.append(
                    self._freeze_snapshot(
                        timestamp=timestamp,
                        commit_hash=commit_hash,
                        author=author_name,
                        email=author_email,
                        message=message,
                        files_changed=files_changed,
                        file_sizes=file_sizes,
                        lines_added=window_lines_added,
                        lines_deleted=window_lines_deleted,
                        contributor_churn=contributor_churn,
                    )
                )
                current_window_end += self.window_seconds
                window_lines_added = 0
                window_lines_deleted = 0
                contributor_churn = {}

        if self.mode != "commit" and (window_lines_added > 0 or window_lines_deleted > 0):
            last_ts = int(self._read_field(commits[-1], "timestamp", current_window_end))
            snapshots.append(
                self._freeze_snapshot(
                    timestamp=timestamp,
                    commit_hash=commit_hash,
                    author=author_name,
                    email=author_email,
                    message=message,
                    files_changed=files_changed,    
                    file_sizes=file_sizes,
                    lines_added=window_lines_added,
                    lines_deleted=window_lines_deleted,
                    contributor_churn=contributor_churn,
                )
            )

        return snapshots

    def build_dicts(self, commits: list[Any]) -> list[dict[str, Any]]:
        return [snapshot.to_dict() for snapshot in self.build_snapshots(commits)]

    def _freeze_snapshot(
        self,
        timestamp: int,
        commit_hash: str,
        author: str,
        email: str,
        message: str,
        files_changed: int,
        file_sizes: dict[str, int],
        lines_added: int,
        lines_deleted: int,
        contributor_churn: dict[str, int],
    ) -> Snapshot:
        active_files = tuple(sorted(file_sizes.keys()))
        file_sizes_tuple = tuple(sorted(file_sizes.items()))
        churn_total = lines_added + lines_deleted

        if churn_total > 0 and contributor_churn:
            distribution = tuple(
                sorted(
                    (author, churn / churn_total)
                    for author, churn in contributor_churn.items()
                    if churn > 0
                )
            )
        else:
            distribution = tuple()

        return Snapshot(
            timestamp=timestamp,
            commit_hash=commit_hash,
            author=author,
            email=email,
            message=message,
            files_changed=files_changed,
            active_files=active_files,
            file_sizes=file_sizes_tuple,
            churn=SnapshotChurn(
                lines_added=lines_added,
                lines_deleted=lines_deleted,
                total=churn_total,
            ),
            contributor_distribution=distribution,
            complexity=self.complexity_placeholder,
        )

    @staticmethod
    def _read_field(item: Any, name: str, default: Any) -> Any:
        if isinstance(item, dict):
            return item.get(name, default)
        return getattr(item, name, default)

    def _iter_file_changes(self, commit: Any) -> list[tuple[str, int, int]]:
        file_changes = self._read_field(commit, "file_changes", [])
        out: list[tuple[str, int, int]] = []
        for change in file_changes:
            path = str(self._read_field(change, "path", ""))
            if not path:
                continue
            added = int(self._read_field(change, "lines_added", 0) or 0)
            deleted = int(self._read_field(change, "lines_deleted", 0) or 0)
            out.append((path, added, deleted))
        return out


def build_snapshots(
    commits: list[Any],
    mode: str = "commit",
    window_seconds: int = 86400,
) -> list[Snapshot]:
    return TemporalSnapshotBuilder(mode=mode, window_seconds=window_seconds).build_snapshots(commits)
