from app.database.seed_data import get_default_factory_setup
from app.engine.scheduler import ScheduleEngine


def test_seed_scenario_execution():
    machines, jobs = get_default_factory_setup()
    engine = ScheduleEngine(machines=machines)
    result = engine.schedule(jobs=jobs)

    # 7 total jobs should all be scheduled without unassigned drops.
    assert len(result.tasks) == 7
    assert len(result.unassigned_jobs) == 0

    # Ensure makespan is realistic (at least the original longest dependency chain).
    assert result.makespan_minutes >= 195

    # The demo now exercises sequence-dependent setup behavior as well.
    setup_tasks = [task for task in result.tasks if task.setup_minutes > 0]
    assert setup_tasks
    assert result.total_setup_minutes > 0

    # Packaging is single-line, so switching from Batch A to Batch B must incur setup.
    batch_b_pack = next(task for task in result.tasks if task.job_id == "BATCH_B_PACK")
    assert batch_b_pack.product_family == "BROTH"
    assert batch_b_pack.setup_minutes == 20
