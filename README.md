# Smart Production Scheduler

A small FastAPI-based production scheduling service that turns jobs, machine capabilities, priorities, and prerequisite relationships into a deterministic feasible schedule.

The current version is a heuristic MVP. It does **not** claim to be an AI/ML optimiser yet; the scheduling engine currently uses transparent priority-based greedy dispatching so that behaviour is easy to test and explain.

## Current capabilities

- Models production jobs, priorities, durations, machines, and machine capabilities.
- Enforces prerequisite relationships between jobs.
- Rejects duplicate IDs, unknown dependencies, self-dependencies, and indirect dependency cycles before scheduling.
- Selects compatible machines and tracks when each machine becomes available.
- Prioritises higher-priority ready jobs, with shorter duration as a deterministic tie-breaker.
- Returns scheduled tasks, total makespan, and any jobs that could not be assigned.
- Includes a realistic demo scenario with preparation, sterilisation, packaging, and QC work.
- Provides API and unit tests for the core scheduling behaviour.

## Project structure

```text
app/
  database/seed_data.py   Demo manufacturing scenario
  engine/scheduler.py     Scheduling heuristic
  models/schemas.py       Pydantic domain/request models
  main.py                 FastAPI application
tests/                    API, model, scenario, and scheduler tests
requirements.txt          Python dependencies
```

## Run locally

Python 3.11+ is recommended.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Then open:

- API docs: `http://127.0.0.1:8000/docs`
- Health check: `GET /health`
- Create a schedule: `POST /schedule`
- Run the built-in demo: `POST /schedule/demo`

## Example request

```json
{
  "machines": [
    {
      "id": "M1",
      "name": "Prep Line",
      "capabilities": ["mixing", "dispensing"]
    }
  ],
  "jobs": [
    {
      "id": "J1",
      "name": "Media preparation",
      "required_capability": "mixing",
      "duration_minutes": 45,
      "priority": 3,
      "depends_on": []
    }
  ]
}
```

## Run tests

```bash
pytest -q
```

## Scheduling approach

At each scheduling step the engine:

1. Finds jobs whose prerequisites have completed.
2. Orders ready jobs by priority, then duration.
3. Finds machines capable of performing the selected job.
4. Calculates the earliest feasible start and finish time for each compatible machine.
5. Assigns the job to the machine that produces the earliest finish time.

This provides a deterministic baseline that can later be compared with optimisation or ML-assisted approaches.

## Current limitations

- No shift calendars, planned downtime, or maintenance windows yet.
- No due-date/tardiness objective yet.
- No sequence-dependent setup/changeover times yet.
- No persistent database or user interface in this standalone repo yet.
- The heuristic is not guaranteed to produce a globally optimal schedule.

## Next development targets

- Add machine availability windows and downtime constraints.
- Add due dates and lateness/KPI calculations.
- Add changeover/setup-time modelling.
- Add scenario comparison for baseline vs optimised schedules.
- Add persistence and a timeline/Gantt-style front end.
