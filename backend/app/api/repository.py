from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.dependencies import get_cached_tig_engine, get_logger


router = APIRouter(prefix="/repository", tags=["repository"])


class RepositoryBuildRequest(BaseModel):
    repo_path: str


class RepositoryBuildResponse(BaseModel):
    status: str
    repo_path: str
    result: Any = None


@router.post("/build", response_model=RepositoryBuildResponse)
async def build_repository_pipeline(
    payload: RepositoryBuildRequest,
    tig_engine=Depends(get_cached_tig_engine),
    logger=Depends(get_logger),
) -> RepositoryBuildResponse:
    try:
        method = None
        for name in ("build_pipeline", "run_pipeline", "build", "run", "analyze"):
            if hasattr(tig_engine, name):
                method = getattr(tig_engine, name)
                break

        if method is None:
            raise RuntimeError("No pipeline method found on TIG engine")

        result = method(payload.repo_path)
        return RepositoryBuildResponse(
            status="success",
            repo_path=payload.repo_path,
            result=result,
        )
    except Exception as exc:
        logger.exception("Failed to build TIG pipeline for repo_path=%s", payload.repo_path)
        raise HTTPException(status_code=500, detail=f"Pipeline build failed: {exc}") from exc
