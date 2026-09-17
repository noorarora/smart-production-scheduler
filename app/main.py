from fastapi import FastAPI, HTTPException
from app.engine.scheduler import ScheduleEngine
from app.models.schemas import ScheduleOutput, ScheduleRequest
from app.database.seed_data import get_default_factory_setup


app = FastAPI(
    title="Smart Production Scheduler API",
    description="Deterministic priority-based scheduling engine with precedence and machine capability constraints.",
    version="1.0.0",
)


@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "production-scheduler"}


@app.post("/schedule", response_model=ScheduleOutput)
def create_schedule(request: ScheduleRequest):
    if not request.machines:
        raise HTTPException(
            status_code=400, detail="At least one machine must be provided."
        )

    if not request.jobs:
        raise HTTPException(
            status_code=400, detail="At least one job must be provided."
        )

    engine = ScheduleEngine(machines=request.machines)
    result = engine.schedule(jobs=request.jobs)
    return result

@app.post("/schedule/demo", response_model=ScheduleOutput)
def run_demo_simulation():
    """Runs scheduling heuristic on a pre-configured 3-stage manufacturing scenario."""
    machines, jobs = get_default_factory_setup()
    engine = ScheduleEngine(machines=machines)
    return engine.schedule(jobs=jobs)