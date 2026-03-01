from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class ChurnWindow:
    timestamp: int
    churn: int
    velocity: float


@dataclass(frozen=True, slots=True)
class FileMetrics:
    path: str
    total_churn: int
    windowed_churn: tuple[ChurnWindow, ...]
    churn_velocity: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "total_churn": self.total_churn,
            "windowed_churn": [
                {
                    "timestamp": window.timestamp,
                    "churn": window.churn,
                    "velocity": window.velocity,
                }
                for window in self.windowed_churn
            ],
            "churn_velocity": self.churn_velocity,
        }
