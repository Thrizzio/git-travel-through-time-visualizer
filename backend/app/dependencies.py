import logging
from functools import lru_cache

from app.config import settings
from app.core.tig_engine import TIGEengine


def get_logger() -> logging.Logger:
    return logging.getLogger("git-history-time-traveller")


def get_tig_engine() -> TIGEengine:
    return TIGEengine()


@lru_cache()
def get_cached_tig_engine() -> TIGEengine:
    return TIGEengine()


def get_repo_base_path() -> str:
    return settings.REPO_BASE_PATH
