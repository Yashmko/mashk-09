from __future__ import annotations

import random
from datetime import UTC, datetime
from typing import Iterable

from app.models import Event, Playbook, RoundResult, Technique


TECHNIQUES = [
    {
        "name": "Synthetic endpoint discovery",
        "id": "T1595-SIM",
        "description": "Enumerates the catalog of simulated services without opening real sockets.",
    },
    {
        "name": "Fixture parameter probing",
        "id": "T1190-SIM",
        "description": "Tests deliberately seeded fixture parameters in the simulation state.",
    },
    {
        "name": "Credential replay fixture",
        "id": "T1078-SIM",
        "description": "Replays a synthetic credential pair that exists only in the fixture dataset.",
    },
    {
        "name": "Session boundary test",
        "id": "T1539-SIM",
        "description": "Exercises a simulated session boundary and records the defensive response.",
    },
    {
        "name": "Audit trail correlation",
        "id": "T1005-SIM",
        "description": "Correlates synthetic audit records to identify a simulated compromise path.",
    },
]

RED_ACTIONS = [
    ("catalogue", "Synthetic service catalogue", "Recon command", "Read-only fixture catalogue queried."),
    ("probe", "Parameter lab", "HTTP request", "Seeded parameter behavior evaluated in memory."),
    ("replay", "Credential vault fixture", "Fixture lookup", "Synthetic credential pair tested against the fixture."),
    ("session", "Session lab", "HTTP request", "Session boundary tested without a real server."),
    ("correlate", "Audit dataset", "Log query", "Synthetic audit records correlated for evidence."),
]

BLUE_ACTIONS = [
    ("watch", "Telemetry stream", "Log query", "Telemetry window reviewed."),
    ("detect", "Detection rules", "Rule evaluation", "Behavioral rule evaluation completed."),
    ("contain", "Synthetic segment", "State transition", "Fixture segment marked contained."),
    ("patch", "Service fixture", "State transition", "Synthetic weakness marked patched."),
]


def _pick_strategy(playbook: Playbook, generation: int, rng: random.Random) -> int:
    bias = min(generation // 3, 2)
    if playbook.priority:
        for index, action in enumerate(RED_ACTIONS):
            if action[0] in playbook.priority:
                return index
    return (generation + bias + rng.randrange(len(RED_ACTIONS))) % len(RED_ACTIONS)


def _new_technique(generation: int, action_key: str, prior: set[str]) -> Technique | None:
    match = next((item for item in TECHNIQUES if item["id"].startswith({
        "catalogue": "T1595",
        "probe": "T1190",
        "replay": "T1078",
        "session": "T1539",
        "correlate": "T1005",
    }[action_key])), None)
    if not match or match["id"] in prior:
        return None
    return Technique(
        name=match["name"],
        technique_id=match["id"],
        first_seen_generation=generation,
        observed_by="red",
        description=match["description"],
    )


def run_round(
    generation: int,
    red_playbook: Playbook,
    blue_playbook: Playbook,
    prior_technique_ids: Iterable[str],
) -> RoundResult:
    """Run one deterministic, seeded contest entirely against in-memory fixtures.

    This engine intentionally has no subprocess, socket, DNS, HTTP-client, or shell
    execution capability. Agent actions are labels applied to synthetic state only.
    """
    rng = random.Random(2026 + generation * 97)
    prior = set(prior_technique_ids)
    events: list[Event] = []
    novel: list[Technique] = []
    sequence = 1

    red_index = _pick_strategy(red_playbook, generation, rng)
    red_key, red_target, red_tool, red_detail = RED_ACTIONS[red_index]
    red_technique = _new_technique(generation, red_key, prior)
    if red_technique:
        novel.append(red_technique)

    events.append(Event(sequence, "red", red_tool, red_target, "attempted", red_detail, red_technique.technique_id if red_technique else None))
    sequence += 1

    blue_pressure = min(0.82, 0.38 + generation * 0.035 + (0.08 if blue_playbook.blocked_patterns else 0))
    detected = rng.random() < blue_pressure
    detection_seconds = 8 + rng.randrange(24) if detected else None
    if detected:
        detector = BLUE_ACTIONS[(generation + len(blue_playbook.blocked_patterns)) % len(BLUE_ACTIONS)]
        events.append(Event(sequence, "blue", detector[2], detector[1], "detected", detector[3], red_technique.technique_id if red_technique else None))
        sequence += 1
    else:
        events.append(Event(sequence, "blue", BLUE_ACTIONS[0][2], BLUE_ACTIONS[0][1], "missed", "No rule matched the synthetic behavior in this window."))
        sequence += 1

    red_win = not detected and rng.random() < 0.72
    containment_seconds: int | None = None
    if detected:
        containment_seconds = detection_seconds + 10 + rng.randrange(32)
        result = "contained" if rng.random() < min(0.94, 0.68 + generation * 0.025) else "escalated"
        events.append(Event(sequence, "blue", BLUE_ACTIONS[2][2], BLUE_ACTIONS[2][1], result, "Synthetic segment state updated; no production system was contacted."))
        sequence += 1
        if result == "contained":
            events.append(Event(sequence, "blue", BLUE_ACTIONS[3][2], BLUE_ACTIONS[3][1], "patched", "Fixture weakness patched for the next generation."))
            sequence += 1
            red_win = False
    else:
        events.append(Event(sequence, "red", "State transition", red_target, "compromised" if red_win else "blocked", "Synthetic outcome recorded in the isolated simulator."))
        sequence += 1

    red_score = 60 if red_win else 25
    blue_score = 25 if red_win else 80
    if detected:
        blue_score += max(0, 20 - (detection_seconds or 20) // 3)
    if novel:
        red_score += 8

    next_red = Playbook(
        priority=[red_key] + [key for key, *_ in RED_ACTIONS if key != red_key][:2],
        blocked_patterns=red_playbook.blocked_patterns[-4:],
        notes=(red_playbook.notes + [f"Generation {generation}: {red_key} produced {'a win' if red_win else 'a detected response'}."])[-5:],
    )
    next_blue = Playbook(
        priority=blue_playbook.priority[-4:] + (["detect"] if detected else ["watch"]),
        blocked_patterns=(blue_playbook.blocked_patterns + ([red_key] if detected else []))[-6:],
        notes=(blue_playbook.notes + [f"Generation {generation}: {'tighten ' + red_key if detected else 'review missed signal'}."])[-5:],
    )
    reflection = (
        f"Red reflected on {red_key}: {'preserve the path and vary its timing' if red_win else 'reduce exposure after blue detection'}. "
        f"Blue reflected on {'faster correlation and containment' if detected else 'coverage for the missed synthetic signal'}."
    )

    return RoundResult(
        generation=generation,
        started_at=datetime.now(UTC).isoformat(),
        red_win=red_win,
        detection_seconds=detection_seconds,
        containment_seconds=containment_seconds,
        red_score=red_score,
        blue_score=blue_score,
        events=events,
        novel_techniques=novel,
        red_playbook=next_red,
        blue_playbook=next_blue,
        reflection=reflection,
    )
