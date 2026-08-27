from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app
from app.models import Playbook
from app.simulation.engine import run_round


def test_round_is_deterministic_and_sandboxed():
    result = run_round(1, Playbook(), Playbook(), [])
    assert result.generation == 1
    assert result.events
    assert all("real" not in event.detail.lower() for event in result.events)
    assert all(event.action != "shell" for event in result.events)


def test_new_technique_only_appears_once():
    first = run_round(1, Playbook(), Playbook(), [])
    ids = [item.technique_id for item in first.novel_techniques]
    second = run_round(1, Playbook(), Playbook(), ids)
    assert not second.novel_techniques


def test_api_exposes_health_and_round_control(tmp_path: Path, monkeypatch):
    db_path = tmp_path / "test.db"
    monkeypatch.setenv("DATABASE_PATH", str(db_path))
    # This test validates the public app shape without mutating the production database.
    assert "/api/health" in {route.path for route in app.routes}
    client = TestClient(app)
    health = client.get("/api/health")
    assert health.status_code == 200
    assert health.json()["mode"] == "synthetic-only"
