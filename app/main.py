from pathlib import Path
from typing import Dict, List

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.database.seed_data import get_default_factory_setup
from app.engine.scheduler import ScheduleEngine
from app.models.schemas import Job, JobPriority, Machine, ScheduleOutput, ScheduleRequest


BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"

app = FastAPI(
    title="Smart Production Scheduler API",
    description="Deterministic priority-based scheduling engine with precedence and machine capability constraints.",
    version="1.1.0",
)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

PRIORITY_LABELS = {
    JobPriority.LOW: "Low",
    JobPriority.MEDIUM: "Medium",
    JobPriority.HIGH: "High",
    JobPriority.CRITICAL: "Critical",
}


@app.get("/", include_in_schema=False)
def schedule_ui():
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/schedule-ui", include_in_schema=False)
def schedule_ui_alias():
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "production-scheduler"}


def _build_schedule_view(machines: List[Machine], jobs: List[Job]) -> Dict:
    engine = ScheduleEngine(machines=machines)
    result = engine.schedule(jobs=jobs)

    jobs_by_id = {job.id: job for job in jobs}
    machines_by_id = {machine.id: machine for machine in machines}

    tasks = []
    for task in result.tasks:
        job = jobs_by_id[task.job_id]
        machine = machines_by_id[task.machine_id]
        tasks.append(
            {
                "job_id": task.job_id,
                "job_name": job.name,
                "category": job.category or job.required_capability.replace("_", " ").title(),
                "required_capability": job.required_capability,
                "machine_id": machine.id,
                "machine_name": machine.name,
                "vessel": machine.vessel or machine.name,
                "lane": machine.lane or machine.name,
                "start_time": task.start_time,
                "end_time": task.end_time,
                "duration_minutes": task.end_time - task.start_time,
                "priority": int(job.priority),
                "priority_label": PRIORITY_LABELS[job.priority],
                "status": job.status,
                "depends_on": job.depends_on,
            }
        )

    return {
        "tasks": tasks,
        "makespan_minutes": result.makespan_minutes,
        "unassigned_jobs": result.unassigned_jobs,
        "resource_count": len(machines),
        "scheduled_count": len(tasks),
    }


@app.post("/schedule", response_model=ScheduleOutput)
def create_schedule(request: ScheduleRequest):
    if not request.machines:
        raise HTTPException(status_code=400, detail="At least one machine must be provided.")
    if not request.jobs:
        raise HTTPException(status_code=400, detail="At least one job must be provided.")

    engine = ScheduleEngine(machines=request.machines)
    return engine.schedule(jobs=request.jobs)


@app.post("/schedule/view")
def create_schedule_view(request: ScheduleRequest):
    """Return scheduler output enriched with the metadata required by the schedule UI."""
    if not request.machines:
        raise HTTPException(status_code=400, detail="At least one machine must be provided.")
    if not request.jobs:
        raise HTTPException(status_code=400, detail="At least one job must be provided.")
    return _build_schedule_view(request.machines, request.jobs)


@app.post("/schedule/demo", response_model=ScheduleOutput)
def run_demo_simulation():
    """Runs scheduling heuristic on a pre-configured manufacturing scenario."""
    machines, jobs = get_default_factory_setup()
    engine = ScheduleEngine(machines=machines)
    return engine.schedule(jobs=jobs)


@app.get("/schedule/demo/view")
def run_demo_schedule_view():
    """Return a UI-ready view of the generated demo schedule."""
    machines, jobs = get_default_factory_setup()
    return _build_schedule_view(machines, jobs)
