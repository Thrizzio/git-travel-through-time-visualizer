import csv
import io
import json
from typing import Any

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel, Field


router = APIRouter(prefix="/export", tags=["export"])


class ExportRequest(BaseModel):
    metrics: list[dict[str, Any]] | dict[str, Any]
    format: str = Field(default="json", pattern="^(json|csv)$")
    filename: str = "metrics_export"


@router.post("")
async def export_metrics(payload: ExportRequest) -> Response:
    try:
        if payload.format == "json":
            content = json.dumps(payload.metrics, indent=2, default=str)
            return Response(
                content=content,
                media_type="application/json",
                headers={
                    "Content-Disposition": f'attachment; filename="{payload.filename}.json"'
                },
            )

        rows: list[dict[str, Any]]
        if isinstance(payload.metrics, dict):
            rows = [payload.metrics]
        else:
            rows = payload.metrics

        if not rows:
            csv_content = ""
        else:
            all_keys: list[str] = []
            seen = set()
            for row in rows:
                for key in row.keys():
                    if key not in seen:
                        seen.add(key)
                        all_keys.append(key)

            buffer = io.StringIO()
            writer = csv.DictWriter(buffer, fieldnames=all_keys)
            writer.writeheader()
            writer.writerows(rows)
            csv_content = buffer.getvalue()

        return Response(
            content=csv_content,
            media_type="text/csv",
            headers={"Content-Disposition": f'attachment; filename="{payload.filename}.csv"'},
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to export metrics: {exc}") from exc
