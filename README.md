# Smart Production Scheduler

A small FastAPI-based production scheduling service that turns jobs, machine capabilities, priorities, prerequisite relationships, machine downtime, due dates, and product-family changeovers into a deterministic feasible schedule.

The current version is a heuristic MVP. It does **not** claim to be an AI/ML optimiser yet; the scheduling engine uses transparent priority-based greedy dispatching so that behaviour is easy to test, inspect, and explain.

## Current capabilities

- Models production jobs, priorities, durations, due dates, product families, machines, and machine capabilities.
- Enforces prerequisite relationships between jobs.
- Rejects duplicate IDs, unknown dependencies, self-dependencies, and indirect dependency cycles before scheduling.
- Supports machine downtime/maintenance windows on the minute-based planning timeline.
- Avoids assigning work across a machine's unavailable periods and can choose another compatible machine when it finishes earlier.
- Supports per-machine fallback setup/changeover time when consecutive jobs switch between different product families.
- Supports optional directional product-to-product changeover matrices such as `A -> B = 8` minutes and `B -> A = 20` minutes.
- Uses a matrix transition when configured and falls back to the machine's default changeover time when a transition is missing.
- Includes setup time when comparing compatible machine finish times, so a machine with a shorter transition can be selected even when another line becomes free earlier.
- Prioritises higher-priority ready jobs, then earlier due dates, then shorter duration as deterministic tie-breakers.
- Reports per-task lateness plus schedule-level late-job, total-tardiness, and total-setup-time KPIs.
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
tests/                    API, model, scenario, scheduler, and changeover tests
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

All times are expressed as minutes from the start of the planning horizon (`T=0`). `changeover_minutes` is the fallback when a machine switches between two known, different `product_family` values. `changeover_matrix` can override that fallback for individual directional transitions.

```json
{
  "machines": [
    {
      "id": "M1",
      "name": "Prep Line",
      "capabilities": ["mixing", "dispensing"],
      "changeover_minutes": 15,
      "changeover_matrix": {
        "FAMILY_A": {
          "FAMILY_B": 8
        },
        "FAMILY_B": {
          "FAMILY_A": 20
        }
      },
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
      "product_family": "FAMILY_A",
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
  "product_family": "FAMILY_A",
  "setup_start_time": 0,
  "setup_minutes": 0,
  "start_time": 0,
  "end_time": 45,
  "due_minute": 150,
  "lateness_minutes": 0
}
```

`setup_start_time` marks when the machine becomes occupied for any required setup. `start_time` marks processing start after setup. The schedule response also reports `makespan_minutes`, `unassigned_jobs`, `late_jobs`, `total_tardiness_minutes`, and `total_setup_minutes`.

## Changeover behavior

For consecutive jobs with known product families, the engine resolves setup time in this order:

1. Same product family: no setup time.
2. Matching directional entry in `changeover_matrix`: use the matrix value.
3. No matrix entry: use `changeover_minutes` as the fallback.
4. Missing product-family information: no sequence-dependent setup is assumed.

The matrix is directional, so `A -> B` and `B -> A` may have different durations.

## Run tests

```bash
pytest -q
```

## Scheduling approach

At each scheduling step the engine:

1. Finds jobs whose prerequisites have completed.
2. Orders ready jobs by priority, then due date, then duration.
3. Finds machines capable of performing the selected job.
4. Resolves sequence-dependent setup time from the machine's previous product family, using the directional matrix first and fallback setup time second.
5. Calculates each machine's earliest feasible setup + processing window while avoiding configured downtime.
6. Assigns the job to the compatible machine that produces the earliest finish time.
7. Updates the machine's product-family state after the job is assigned.
8. Calculates lateness when a due date is present and aggregates tardiness and setup-time KPIs.

This provides a deterministic baseline that can later be compared with optimisation or ML-assisted approaches.

## Current limitations

- Downtime windows are supported, but full repeating shift calendars are not yet modelled.
- Changeover matrices currently use product-family names only; cleaning class, allergen risk, tooling, and operator-specific setup rules are not modelled.
- Setup is conservatively scheduled after job prerequisites have completed; anticipatory setup is not modelled yet.
- The current objective is heuristic rather than a formal global tardiness/makespan optimisation model.
- No persistent database or user interface in this standalone repo yet.
- The heuristic is not guaranteed to produce a globally optimal schedule.

## Next development targets

- Add shift calendars and richer machine availability rules.
- Add cleaning/setup categories on top of the product-family matrix.
- Add schedule quality comparison for baseline vs alternative heuristics/optimisation.
- Add persistence and schedule history.
- Add a timeline/Gantt-style front end.
