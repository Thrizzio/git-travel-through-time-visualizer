from typing import Any
from fastapi import APIRouter, Request

router = APIRouter(prefix="/metrics", tags=["metrics"])


@router.get("/timeline")
async def get_timeline_metrics(request: Request) -> dict[str, Any]:
    cache = request.app.state.analysis_cache
    return {
        "status": "success",
        "component": "timeline",
        "data": cache.get("timeline", []),
    }