from __future__ import annotations

import os
import subprocess
import time
from collections import defaultdict
from dataclasses import asdict, dataclass, field
from typing import Any

try:
    from app.config import MAX_COMMIT_LIMIT, MAX_PROCESSING_TIME_SECONDS
except Exception:
    MAX_COMMIT_LIMIT = 5000
    MAX_PROCESSING_TIME_SECONDS = 30


_COMMIT_MARKER = "__COMMIT__"
_FIELD_SEP = "\x1f"


@dataclass(slots=True)
class FileChangeMetadata:
    path: str
    lines_added: int
    lines_deleted: int


@dataclass(slots=True)
class CommitMetadata:
    commit_hash: str
    author_name: str
    author_email: str
    timestamp: int
    files_modified: int = 0
    lines_added: int = 0
    lines_deleted: int = 0
    file_changes: list[FileChangeMetadata] = field(default_factory=list)


@dataclass(slots=True)
class ParserResult:
    repo_path: str
    total_commits: int
    total_files_touched: int
    commits: list[CommitMetadata]
    contributors: dict[str, dict[str, Any]]
    file_ownership: dict[str, dict[str, int]]

    def to_dict(self) -> dict[str, Any]:
        return {
            "repo_path": self.repo_path,
            "total_commits": self.total_commits,
            "total_files_touched": self.total_files_touched,
            "commits": [asdict(commit) for commit in self.commits],
            "contributors": self.contributors,
            "file_ownership": self.file_ownership,
        }


class GitParser:
    def __init__(
        self,
        max_commits: int = MAX_COMMIT_LIMIT,
        timeout_seconds: int = MAX_PROCESSING_TIME_SECONDS,
    ) -> None:
        self.max_commits = max_commits
        self.timeout_seconds = timeout_seconds

    def parse(self, repo_path: str) -> ParserResult:
        normalized_repo_path = os.path.abspath(repo_path)
        if not os.path.isdir(normalized_repo_path):
            raise FileNotFoundError(f"Repository path not found: {normalized_repo_path}")

        commits: list[CommitMetadata] = []
        touched_files: set[str] = set()
        contributors: dict[str, dict[str, Any]] = {}
        file_ownership: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
        started_at = time.monotonic()

        command = [
            "git",
            "-C",
            normalized_repo_path,
            "log",
            "--all",
            "--date-order",
            "--no-color",
            "--numstat",
            "--no-renames",
            f"--max-count={self.max_commits}",
            f"--pretty=format:{_COMMIT_MARKER}{_FIELD_SEP}%H{_FIELD_SEP}%an{_FIELD_SEP}%ae{_FIELD_SEP}%at",
        ]

        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
            bufsize=1,
        )

        current_commit: CommitMetadata | None = None
        current_file_set: set[str] = set()

        try:
            assert process.stdout is not None
            for raw_line in process.stdout:
                if time.monotonic() - started_at > self.timeout_seconds:
                    process.kill()
                    raise TimeoutError(
                        f"Parsing exceeded timeout of {self.timeout_seconds} seconds"
                    )

                line = raw_line.rstrip("\n")
                if not line:
                    continue

                if line.startswith(_COMMIT_MARKER):
                    if current_commit is not None:
                        current_commit.files_modified = len(current_file_set)
                        commits.append(current_commit)

                    current_file_set = set()
                    current_commit = self._parse_commit_header(line)
                    contributor = contributors.get(current_commit.author_email)
                    if contributor is None:
                        contributor = {
                            "name": current_commit.author_name,
                            "email": current_commit.author_email,
                            "commits": 0,
                            "lines_added": 0,
                            "lines_deleted": 0,
                        }
                        contributors[current_commit.author_email] = contributor
                    contributor["commits"] += 1
                    continue

                if current_commit is None:
                    continue

                file_change = self._parse_numstat_line(line)
                if file_change is None:
                    continue

                current_commit.file_changes.append(file_change)
                current_commit.lines_added += file_change.lines_added
                current_commit.lines_deleted += file_change.lines_deleted

                current_file_set.add(file_change.path)
                touched_files.add(file_change.path)

                lines_changed = file_change.lines_added + file_change.lines_deleted
                file_ownership[file_change.path][current_commit.author_email] += lines_changed

                contributor = contributors[current_commit.author_email]
                contributor["lines_added"] += file_change.lines_added
                contributor["lines_deleted"] += file_change.lines_deleted

            if current_commit is not None:
                current_commit.files_modified = len(current_file_set)
                commits.append(current_commit)

            return_code = process.wait(timeout=5)
            stderr_text = process.stderr.read() if process.stderr is not None else ""
            if return_code != 0:
                raise RuntimeError(stderr_text.strip() or "git log failed")
        finally:
            if process.poll() is None:
                process.kill()
            if process.stdout is not None:
                process.stdout.close()
            if process.stderr is not None:
                process.stderr.close()

        frozen_file_ownership = {
            path: dict(author_to_lines) for path, author_to_lines in file_ownership.items()
        }

        return ParserResult(
            repo_path=normalized_repo_path,
            total_commits=len(commits),
            total_files_touched=len(touched_files),
            commits=commits,
            contributors=contributors,
            file_ownership=frozen_file_ownership,
        )

    @staticmethod
    def _parse_commit_header(line: str) -> CommitMetadata:
        payload = line[len(_COMMIT_MARKER) :]
        if payload.startswith(_FIELD_SEP):
            payload = payload[1:]
        parts = payload.split(_FIELD_SEP)
        if len(parts) != 4:
            raise ValueError(f"Unexpected commit header format: {line}")

        commit_hash, author_name, author_email, timestamp_str = parts

        return CommitMetadata(
            commit_hash=commit_hash,
            author_name=author_name,
            author_email=author_email,
            timestamp=int(timestamp_str),
        )

    @staticmethod
    def _parse_numstat_line(line: str) -> FileChangeMetadata | None:
        parts = line.split("\t", 2)
        if len(parts) != 3:
            return None

        added_raw, deleted_raw, path = parts
        if not path:
            return None

        lines_added = int(added_raw) if added_raw.isdigit() else 0
        lines_deleted = int(deleted_raw) if deleted_raw.isdigit() else 0
        return FileChangeMetadata(path=path, lines_added=lines_added, lines_deleted=lines_deleted)


def parse_repository(repo_path: str) -> dict[str, Any]:
    return GitParser().parse(repo_path).to_dict()


def parse_repo(repo_path: str) -> dict[str, Any]:
    return parse_repository(repo_path)
