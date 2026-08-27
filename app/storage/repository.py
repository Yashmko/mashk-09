from __future__ import annotations

import json
import os
import sqlite3
from pathlib import Path
from typing import Any

from app.models import Playbook, RoundResult, Technique


class Repository:
    def __init__(self, path: str | None = None) -> None:
        self.path = path or os.getenv("DATABASE_PATH", str(Path(__file__).resolve().parents[2] / "data" / "mashk_09.db"))
        Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS rounds (
                    generation INTEGER PRIMARY KEY,
                    started_at TEXT NOT NULL,
                    red_win INTEGER NOT NULL,
                    detection_seconds INTEGER,
                    containment_seconds INTEGER,
                    red_score INTEGER NOT NULL,
                    blue_score INTEGER NOT NULL,
                    reflection TEXT NOT NULL,
                    red_playbook TEXT NOT NULL,
                    blue_playbook TEXT NOT NULL,
                    events TEXT NOT NULL,
                    novel_techniques TEXT NOT NULL
                );
                """
            )

    def count(self) -> int:
        with self._connect() as connection:
            return int(connection.execute("SELECT COUNT(*) FROM rounds").fetchone()[0])

    def save_round(self, result: RoundResult) -> None:
        payload = result.to_dict()
        with self._connect() as connection:
            connection.execute(
                """
                INSERT OR REPLACE INTO rounds
                (generation, started_at, red_win, detection_seconds, containment_seconds,
                 red_score, blue_score, reflection, red_playbook, blue_playbook, events, novel_techniques)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    result.generation,
                    result.started_at,
                    int(result.red_win),
                    result.detection_seconds,
                    result.containment_seconds,
                    result.red_score,
                    result.blue_score,
                    result.reflection,
                    json.dumps(payload["red_playbook"]),
                    json.dumps(payload["blue_playbook"]),
                    json.dumps(payload["events"]),
                    json.dumps(payload["novel_techniques"]),
                ),
            )

    def list_rounds(self, limit: int = 100) -> list[dict[str, Any]]:
        with self._connect() as connection:
            rows = connection.execute("SELECT * FROM rounds ORDER BY generation DESC LIMIT ?", (limit,)).fetchall()
        return [self._deserialize(row) for row in rows]

    def get_round(self, generation: int) -> dict[str, Any] | None:
        with self._connect() as connection:
            row = connection.execute("SELECT * FROM rounds WHERE generation = ?", (generation,)).fetchone()
        return self._deserialize(row) if row else None

    def all_techniques(self) -> list[dict[str, Any]]:
        techniques: dict[str, dict[str, Any]] = {}
        for item in self.list_rounds(1000):
            for technique in item["novel_techniques"]:
                techniques.setdefault(technique["technique_id"], technique)
        return sorted(techniques.values(), key=lambda item: item["first_seen_generation"])

    def latest_playbooks(self) -> dict[str, dict[str, Any]]:
        rounds = self.list_rounds(1)
        if not rounds:
            return {"red": Playbook().to_dict(), "blue": Playbook().to_dict()}
        return {"red": rounds[0]["red_playbook"], "blue": rounds[0]["blue_playbook"]}

    @staticmethod
    def _deserialize(row: sqlite3.Row) -> dict[str, Any]:
        return {
            "generation": row["generation"],
            "started_at": row["started_at"],
            "red_win": bool(row["red_win"]),
            "detection_seconds": row["detection_seconds"],
            "containment_seconds": row["containment_seconds"],
            "red_score": row["red_score"],
            "blue_score": row["blue_score"],
            "reflection": row["reflection"],
            "red_playbook": json.loads(row["red_playbook"]),
            "blue_playbook": json.loads(row["blue_playbook"]),
            "events": json.loads(row["events"]),
            "novel_techniques": json.loads(row["novel_techniques"]),
        }
