# Smart Production Scheduler

A small FastAPI-based production scheduling service that turns jobs, machine capabilities, priorities, prerequisite relationships, machine downtime, and due dates into a deterministic feasible schedule.

The current version is a heuristic MVP. It does **not** claim to be an AI/ML optimiser yet; the scheduling engine uses transparent priority-based greedy dispatching so that behaviour is easy to test, inspect, and explain.

## Current capabilities

- Models production jobs, priorities, durations, due dates, machines, and machine capabilities.
- Enforces prerequisite relationships between jobs.
- Rejects duplicate IDs, unknown dependencies, self-dependencies, and indirect dependency cycles before scheduling.
- Supports machine downtime/maintenance windows on the minute-based planning timeline.
- Avoids assigning work across a machine's unavailable periods and can choose another compatible machine when it finishes earlier.
- Prioritises higher-priority ready jobs, then earlier due dates, then shorter duration as deterministic tie-breakers.
- Reports per-task lateness plus schedule-level late-job and total-tardiness KPIs.
- Returns scheduled tasks, total makespan, and any jobs that could not be assigned.
- Includes a realistic demo scenario with preparation, sterilisation, packaging, and QC work.
- Runs the full pytest suite automatically with GitHub Actions on pushes and pull requests.

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

All times are expressed as minutes from the start of the planning horizon (`T=0`).

```json
{
  "machines": [
    {
      "id": "M1",
      "name": "Prep Line",
      "capabilities": ["mixing", "dispensing"],
      "unavailable_windows": [
        {
          "start_minute": 60,
          "end_minute": 120
        }
      ]
    }
  ],
  "jobs": [
    {
      "id": "J1",
      "name": "Media preparation",
      "required_capability": "mixing",
      "duration_minutes": 45,
      "priority": 3,
      "due_minute": 150,
      "depends_on": []
    }
  ]
}
```

A scheduled task can include fields such as:

```json
{
  "job_id": "J1",
  "machine_id": "M1",
  "start_time": 0,
  "end_time": 45,
  "due_minute": 150,
  "lateness_minutes": 0
}
```

The schedule response also reports `makespan_minutes`, `unassigned_jobs`, `late_jobs`, and `total_tardiness_minutes`.

## Run tests

```bash
pytest -q
```

## Scheduling approach

At each scheduling step the engine:

1. Finds jobs whose prerequisites have completed.
2. Orders ready jobs by priority, then due date, then duration.
3. Finds machines capable of performing the selected job.
4. Calculates each machine's earliest feasible start while avoiding configured downtime windows.
5. Assigns the job to the compatible machine that produces the earliest finish time.
6. Calculates lateness when a due date is present and aggregates tardiness KPIs.

This provides a deterministic baseline that can later be compared with optimisation or ML-assisted approaches.

## Current limitations

- Downtime windows are supported, but full repeating shift calendars are not yet modelled.
- No sequence-dependent setup/changeover times yet.
- The current objective is heuristic rather than a formal global tardiness/makespan optimisation model.
- No persistent database or user interface in this standalone repo yet.
- The heuristic is not guaranteed to produce a globally optimal schedule.

## Next development targets

- Add shift calendars and richer machine availability rules.
- Add changeover/setup-time modelling.
- Add schedule quality comparison for baseline vs alternative heuristics/optimisation.
- Add persistence and schedule history.
- Add a timeline/Gantt-style front end.
