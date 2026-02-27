try:
    from pydantic_settings import BaseSettings, SettingsConfigDict
except ImportError:
    try:
        from pydantic.v1 import BaseSettings  # type: ignore
    except ImportError:  # Pydantic v1 fallback
        from pydantic import BaseSettings  # type: ignore
    SettingsConfigDict = None  # type: ignore


TDI_WEIGHTS = {
    "churn": 0.4,
    "complexity": 0.35,
    "ownership_risk": 0.25,
}

NORMALIZATION_LIMITS = {
    "max_churn": 100,
    "max_complexity": 50,
    "max_entropy": 2.5,
}

DEFAULT_TIME_WINDOW_DAYS = 30
SNAPSHOT_GRANULARITY = "monthly"  # daily | weekly | monthly

MAX_COMMIT_LIMIT = 5000
MAX_PROCESSING_TIME_SECONDS = 30
ENABLE_SNAPSHOT_CACHING = True

PREDICTION_SETTINGS = {
    "min_history_points": 5,
    "forecast_horizon": 1,
    "confidence_threshold": 0.7,
}

RISK_THRESHOLDS = {
    "low": 0.3,
    "medium": 0.6,
    "high": 0.8,
}

FEATURE_FLAGS = {
    "enable_prediction": True,
    "enable_bus_factor": True,
    "enable_entropy": True,
}


class Settings(BaseSettings):
    APP_NAME: str = "Git History Time Traveller"
    DEBUG: bool = True
    REPO_BASE_PATH: str = "./repos"

    if SettingsConfigDict is not None:
        model_config = SettingsConfigDict(env_file=".env")
    else:
        class Config:
            env_file = ".env"


settings = Settings()


def _validate_tdi_weights() -> None:
    total = sum(TDI_WEIGHTS.values())
    if abs(total - 1.0) > 1e-9:
        raise ValueError(f"TDI_WEIGHTS must sum to 1.0, got {total}")


def _validate_risk_thresholds() -> None:
    low = RISK_THRESHOLDS["low"]
    medium = RISK_THRESHOLDS["medium"]
    high = RISK_THRESHOLDS["high"]
    if not (low < medium < high):
        raise ValueError("RISK_THRESHOLDS must be in increasing order: low < medium < high")


def _validate_snapshot_granularity() -> None:
    allowed = {"daily", "weekly", "monthly"}
    if SNAPSHOT_GRANULARITY not in allowed:
        raise ValueError(
            f"SNAPSHOT_GRANULARITY must be one of {sorted(allowed)}, got {SNAPSHOT_GRANULARITY}"
        )


def _validate_config() -> None:
    _validate_tdi_weights()
    _validate_risk_thresholds()
    _validate_snapshot_granularity()


_validate_config()
