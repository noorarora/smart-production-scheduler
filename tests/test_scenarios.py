from app.database.seed_data import get_default_factory_setup
from app.engine.scheduler import ScheduleEngine


def test_seed_scenario_execution():
    machines, jobs = get_default_factory_setup()
    engine = ScheduleEngine(machines=machines)
    result = engine.schedule(jobs=jobs)

    # 7 total jobs should all be scheduled without unassigned drops
    assert len(result.tasks) == 7
    assert len(result.unassigned_jobs) == 0

    # Ensure makespan is realistic (must be at least longest single dependency chain = 195 mins)
    assert result.makespan_minutes >= 195
    