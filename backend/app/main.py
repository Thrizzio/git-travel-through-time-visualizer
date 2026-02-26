import logging
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("git-history-time-traveller")


class AnalyzeRequest(BaseModel):
    repo_path: str


class AnalyzeResponse(BaseModel):
    status: str
    snapshots: list[dict[str, Any]]
    summary: dict[str, Any]


class HealthResponse(BaseModel):
    status: str
    service: str


class SummaryResponse(BaseModel):
    status: str
    summary: dict[str, Any]


app = FastAPI(
    title="Git History Time Traveller",
    version="1.0.0",
    description="Backend orchestration API for timeline, debt heatmap, contributor graph, and risk panel.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def run_analysis(repo_path: str) -> dict[str, Any]:
    """
    Placeholder analysis pipeline orchestrator.
    Real implementation will live in service modules.
    """
    logger.info("Running analysis pipeline for repo_path=%s", repo_path)
    return {
        "status": "success",
        "snapshots": [],
        "summary": {},
    }


@app.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(
        status="ok",
        service="git-history-time-traveller-backend",
    )


@app.post("/analyze", response_model=AnalyzeResponse)
async def analyze(payload: AnalyzeRequest) -> AnalyzeResponse:
    try:
        result = run_analysis(payload.repo_path)
        return AnalyzeResponse(
            status=result.get("status", "success"),
            snapshots=result.get("snapshots", []),
            summary=result.get("summary", {}),
        )
    except Exception as exc:
        logger.exception("Analysis failed for repo_path=%s", payload.repo_path)
        raise HTTPException(status_code=500, detail=f"Analysis failed: {exc}") from exc


@app.get("/summary", response_model=SummaryResponse)
async def summary() -> SummaryResponse:
    try:
        return SummaryResponse(
            status="success",
            summary={
                "message": "Summary pipeline placeholder",
                "total_commits": 0,
                "active_contributors": 0,
                "risk_score": 0.0,
            },
        )
    except Exception as exc:
        logger.exception("Failed to build summary response")
        raise HTTPException(status_code=500, detail=f"Summary failed: {exc}") from exc