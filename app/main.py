from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from app.models import Playbook
from app.simulation.engine import run_round
from app.storage.repository import Repository


BASE_DIR = Path(__file__).resolve().parents[1]
app = FastAPI(
    title="mashk-09",
    description="A local-only co-evolution simulator for red-team and blue-team AI research.",
    version="0.1.0",
)
repo = Repository()
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")


class RoundRequest(BaseModel):
    count: int = Field(default=1, ge=1, le=25, description="Number of synthetic rounds to run")


def _run_one() -> dict[str, Any]:
    latest = repo.latest_playbooks()
    history = repo.list_rounds(1000)
    prior_ids = [technique["technique_id"] for item in history for technique in item["novel_techniques"]]
    result = run_round(
        generation=repo.count() + 1,
        red_playbook=Playbook(**latest["red"]),
        blue_playbook=Playbook(**latest["blue"]),
        prior_technique_ids=prior_ids,
    )
    repo.save_round(result)
    return result.to_dict()


@app.get("/", response_class=FileResponse)
def dashboard() -> Path:
    return BASE_DIR / "static" / "index.html"


@app.get("/health")
@app.get("/api/health")
def health() -> dict[str, Any]:
    return {"status": "ok", "mode": "synthetic-only", "rounds": repo.count()}


@app.post("/api/rounds")
def create_rounds(request: RoundRequest) -> dict[str, Any]:
    rounds = [_run_one() for _ in range(request.count)]
    return {"created": len(rounds), "latest": rounds[-1]}


@app.get("/api/rounds")
def list_rounds(limit: int = 100) -> list[dict[str, Any]]:
    return repo.list_rounds(max(1, min(limit, 1000)))


@app.get("/api/rounds/{generation}")
def get_round(generation: int) -> dict[str, Any]:
    item = repo.get_round(generation)
    if not item:
        raise HTTPException(status_code=404, detail="Generation not found")
    return item


@app.get("/api/summary")
def summary() -> dict[str, Any]:
    history = list(reversed(repo.list_rounds(1000)))
    total = len(history)
    red_wins = sum(item["red_win"] for item in history)
    detections = [item["detection_seconds"] for item in history if item["detection_seconds"] is not None]
    containment = [item["containment_seconds"] for item in history if item["containment_seconds"] is not None]
    return {
        "total_rounds": total,
        "red_win_rate": round(red_wins / total, 3) if total else 0,
        "blue_detection_rate": round(len(detections) / total, 3) if total else 0,
        "average_detection_seconds": round(sum(detections) / len(detections), 1) if detections else None,
        "average_containment_seconds": round(sum(containment) / len(containment), 1) if containment else None,
        "novel_techniques": repo.all_techniques(),
        "history": [
            {
                "generation": item["generation"],
                "red_win": item["red_win"],
                "red_score": item["red_score"],
                "blue_score": item["blue_score"],
                "detection_seconds": item["detection_seconds"],
            }
            for item in history
        ],
    }


@app.get("/api/playbook")
def playbook() -> dict[str, Any]:
    return repo.latest_playbooks()
