from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class Event:
    sequence: int
    actor: str
    action: str
    target: str
    outcome: str
    detail: str
    technique_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class Technique:
    name: str
    technique_id: str
    first_seen_generation: int
    observed_by: str
    description: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class Playbook:
    priority: list[str] = field(default_factory=list)
    blocked_patterns: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class RoundResult:
    generation: int
    started_at: str
    red_win: bool
    detection_seconds: int | None
    containment_seconds: int | None
    red_score: int
    blue_score: int
    events: list[Event]
    novel_techniques: list[Technique]
    red_playbook: Playbook
    blue_playbook: Playbook
    reflection: str

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["events"] = [event.to_dict() for event in self.events]
        payload["novel_techniques"] = [technique.to_dict() for technique in self.novel_techniques]
        payload["red_playbook"] = self.red_playbook.to_dict()
        payload["blue_playbook"] = self.blue_playbook.to_dict()
        return payload
