# mashk-09

mashk-09 is a self-contained, local-only cyber-range prototype that visualizes a co-evolutionary contest between a synthetic red-team lineage and a synthetic blue-team lineage. It is designed as a portfolio and research artifact: the dashboard shows generation-over-generation outcomes, the event timeline makes each round replayable, and persistent playbooks make the agents visibly adapt rather than behave like a static script.

> **Safety boundary:** mashk-09 never contacts real hosts, opens sockets, executes shell commands, performs DNS lookups, sends HTTP requests, uses real credentials, or provides a path to a non-sandboxed target. Every “tool call” is a typed label applied to in-memory fixture state. The Compose network is explicitly marked `internal: true`, and the published port binds to loopback only.

## Design direction

The interface is intentionally reframed as a sealed-world instrument rather than a conventional admin dashboard. Its editorial-scale typography, generous pacing, deliberate transitions, and dark-mode contrast are informed by [Awwwards’ dark-mode collection](https://www.awwwards.com/awwwards/collections/dark-mode/). Its live-preview energy, material-like gradients, compact status labels, and playground feel take cues from [MetalForge](https://metalforge.xyz/). The implementation is original, CSS-driven, and does not depend on their assets or code.

## What is included

| Area | Implementation |
| --- | --- |
| Orchestrator | FastAPI API with on-demand multi-generation execution |
| Simulation | Seeded, deterministic red/blue contest against synthetic fixtures |
| Memory | SQLite round history plus evolving red and blue playbooks |
| Dashboard | Static HTML, CSS, and JavaScript operations workspace |
| Evidence | Event timeline, scores, detection and containment timing, novel technique register |
| Runtime | Docker Compose with a loopback-only port and internal bridge network |
| Validation | Pytest coverage for sandbox boundaries, novelty behavior, and API health |

## Quick start

The supported runtime is Python 3.12 or Docker. From this directory:

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Open [http://127.0.0.1:8000](http://127.0.0.1:8000). Run one or more generations from **ROUND CONTROL**. The history is stored at `data/mashk_09.db` and remains available after a restart.

To run the same prototype in Docker:

```bash
docker compose up --build
```

The dashboard is still available only at [http://127.0.0.1:8000](http://127.0.0.1:8000). Stop it with `docker compose down`.

## Production deployment

The repository includes a root-level [`render.yaml`](./render.yaml) Blueprint. It creates one free Docker-backed Render web service from this repository, uses `/health` for readiness checks, binds through Render’s injected `PORT`, and stores SQLite at `/tmp/mashk_09.db`.

The free Render filesystem is ephemeral: the app works normally, but generation history can reset when the service restarts or spins down after inactivity. This is intentional for the free deployment. A persistent disk or managed database can be added later without changing the frontend API. No API keys are required by the current deterministic simulator; future secrets should be added through Render’s environment-variable dashboard rather than committed to Git.

Vercel is possible for a separate static frontend, but the FastAPI backend would need its own deployment and CORS/base-URL configuration. Keeping the dashboard and API in one Render service is the lower-complexity production path for this repository.

## Co-evolution loop

Each generation begins with the latest red and blue playbooks. The synthetic red policy selects a constrained action label such as `catalogue`, `probe`, `replay`, `session`, or `correlate`. The blue policy evaluates the resulting synthetic signal, records detection or a miss, and may apply simulated containment and patch state transitions. The orchestrator scores the round, records every event, and registers any technique that has not appeared in an earlier generation.

The final step is reflection. Both lineages append a short outcome note and update their priority or blocked-pattern memory. The next round consumes that state. This creates a readable lineage history while keeping the system deterministic, bounded, and safe to execute locally.

## API surface

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/api/health` | Reports service status and confirms `synthetic-only` mode |
| `POST` | `/api/rounds` | Runs 1–25 rounds; body is `{ "count": 1 }` |
| `GET` | `/api/rounds` | Returns persisted rounds, newest first |
| `GET` | `/api/rounds/{generation}` | Returns a single replayable generation |
| `GET` | `/api/summary` | Returns metrics, history chart data, and novel techniques |
| `GET` | `/api/playbook` | Returns the latest red and blue playbooks |
| `GET` | `/docs` | Opens FastAPI’s local API documentation |

Example:

```bash
curl -X POST http://127.0.0.1:8000/api/rounds \\
  -H 'Content-Type: application/json' \\
  -d '{"count": 3}'
```

## Research extensions

The engine intentionally exposes a small seam for future work. A research-grade local LLM adapter can replace the deterministic policy selector while returning only a validated action enum from the existing synthetic action catalogue. A second blue sub-agent could consume the same event stream with a network- or host-defense specialization. The playbook endpoint can also be extended to export a Markdown or JSON artifact for experiment comparison.

Any future extension must preserve the project’s safety contract: synthetic fixtures only, explicit allowlisted actions, no general-purpose command execution, no network client capability, no real secrets, and no externally reachable training services.

## Test suite

```bash
pytest -q
```

The current suite validates that the engine emits events without shell-like actions, that novel techniques are not duplicated when prior IDs are supplied, and that the local API exposes its health contract.
