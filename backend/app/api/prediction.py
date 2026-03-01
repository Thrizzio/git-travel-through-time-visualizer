from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from app.dependencies import get_cached_tig_engine, get_logger


router = APIRouter(prefix="/prediction", tags=["prediction"])


class TopRiskResponse(BaseModel):
    status: str
    top_n: int
    files: list[dict[str, Any]]


def _extract_predictions(tig_engine: Any) -> list[dict[str, Any]]:
    for key in ("predicted_risks", "risk_predictions", "predictions"):
        value = getattr(tig_engine, key, None)
        if isinstance(value, list):
            return [item for item in value if isinstance(item, dict)]
    return []


def _score(item: dict[str, Any]) -> float:
    for key in ("risk_score", "score", "probability"):
        value = item.get(key)
        if isinstance(value, (int, float)):
            return float(value)
    return 0.0


@router.get("/top-risk", response_model=TopRiskResponse)
async def get_top_risk_files(
    n: int = Query(default=10, ge=1, le=100),
    tig_engine=Depends(get_cached_tig_engine),
    logger=Depends(get_logger),
) -> TopRiskResponse:
    try:
        predictions = _extract_predictions(tig_engine)
        ranked = sorted(predictions, key=_score, reverse=True)
        return TopRiskResponse(
            status="success",
            top_n=n,
            files=ranked[:n],
        )
    except Exception as exc:
        logger.exception("Failed to fetch top risk predictions")
        raise HTTPException(status_code=500, detail=f"Failed to fetch predictions: {exc}") from exc
