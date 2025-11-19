from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any, Dict, List

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .config import ENRICHED_DATA_PATH, FRONTEND_DIR, get_settings
from .etl import ETLPipeline

app = FastAPI(title="City Sustainability Insights", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

pipeline = ETLPipeline()


@app.on_event("startup")
async def startup_event() -> None:
    await pipeline.ensure_output()


@app.get("/health")
def healthcheck() -> Dict[str, str]:
    settings = get_settings()
    return {
        "status": "ok",
        "model": settings.huggingface_model,
        "output_exists": str(ENRICHED_DATA_PATH.exists()).lower(),
    }


@app.get("/insights")
async def get_insights() -> List[Dict[str, Any]]:
    if not ENRICHED_DATA_PATH.exists():
        await pipeline.run()
    return pipeline.load_cached_output()


@app.post("/etl/run")
async def run_etl() -> Dict[str, Any]:
    try:
        result = await pipeline.run()
    except Exception as exc:  # pragma: no cover - surfaced via HTTP 500
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return {"status": "ok", "result": result}


if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")


@app.get("/")
async def index() -> FileResponse:
    index_path = FRONTEND_DIR / "index.html"
    if not index_path.exists():
        raise HTTPException(status_code=404, detail="Frontend not built yet")
    return FileResponse(index_path)
