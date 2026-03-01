from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.dependencies import get_cached_tig_engine, get_logger


router = APIRouter(prefix="/metrics", tags=["metrics"])


class MetricsResponse(BaseModel):
    status: str
    component: str
    data: Any


def _read_precomputed_metrics(tig_engine: Any) -> dict[str, Any]:
    metrics = getattr(tig_engine, "precomputed_metrics", None)
    if isinstance(metrics, dict):
        return metrics
    return {}


@router.get("/timeline", response_model=MetricsResponse)
async def get_timeline_metrics(
    tig_engine=Depends(get_cached_tig_engine),
    logger=Depends(get_logger),
) -> MetricsResponse:
    try:
        metrics = _read_precomputed_metrics(tig_engine)
        data = metrics.get("timeline", [])
        return MetricsResponse(status="success", component="timeline", data=data)
    except Exception as exc:
        logger.exception("Failed to fetch timeline metrics")
        raise HTTPException(status_code=500, detail=f"Failed to fetch timeline metrics: {exc}") from exc


@router.get("/debt-heatmap", response_model=MetricsResponse)
async def get_debt_heatmap_metrics(
    tig_engine=Depends(get_cached_tig_engine),
    logger=Depends(get_logger),
) -> MetricsResponse:
    try:
        metrics = _read_precomputed_metrics(tig_engine)
        data = metrics.get("debt_heatmap", [])
        return MetricsResponse(status="success", component="debt_heatmap", data=data)
    except Exception as exc:
        logger.exception("Failed to fetch debt heatmap metrics")
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch debt heatmap metrics: {exc}"
        ) from exc


@router.get("/contributor-network", response_model=MetricsResponse)
async def get_contributor_network_metrics(
    tig_engine=Depends(get_cached_tig_engine),
    logger=Depends(get_logger),
) -> MetricsResponse:
    try:
        metrics = _read_precomputed_metrics(tig_engine)
        data = metrics.get("contributor_network", {"nodes": [], "edges": []})
        return MetricsResponse(status="success", component="contributor_network", data=data)
    except Exception as exc:
        logger.exception("Failed to fetch contributor network metrics")
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch contributor network metrics: {exc}"
        ) from exc


@router.get("/risk-panel", response_model=MetricsResponse)
async def get_risk_panel_metrics(
    tig_engine=Depends(get_cached_tig_engine),
    logger=Depends(get_logger),
) -> MetricsResponse:
    try:
        metrics = _read_precomputed_metrics(tig_engine)
        data = metrics.get("risk_panel", {})
        return MetricsResponse(status="success", component="risk_panel", data=data)
    except Exception as exc:
        logger.exception("Failed to fetch risk panel metrics")
        raise HTTPException(status_code=500, detail=f"Failed to fetch risk panel metrics: {exc}") from exc


@router.get("/all")
async def get_all_metrics(
    tig_engine=Depends(get_cached_tig_engine),
    logger=Depends(get_logger),
) -> dict[str, Any]:
    try:
        metrics = _read_precomputed_metrics(tig_engine)
        return {
            "status": "success",
            "timeline": metrics.get("timeline", []),
            "debt_heatmap": metrics.get("debt_heatmap", []),
            "contributor_network": metrics.get("contributor_network", {"nodes": [], "edges": []}),
            "risk_panel": metrics.get("risk_panel", {}),
        }
    except Exception as exc:
        logger.exception("Failed to fetch all metrics")
        raise HTTPException(status_code=500, detail=f"Failed to fetch metrics: {exc}") from exc
