import pytest
from app.engine.scheduler import ScheduleEngine
from app.models.schemas import Job, JobPriority, Machine


@pytest.fixture
def mock_factory_machines():
    return [
        Machine(
            id="LINE_1",
            name="Primary Prep Line",
            capabilities=["dispensing", "mixing"],
        ),
        Machine(
            id="LINE_2",
            name="Secondary Prep Line",
            capabilities=["mixing", "autoclave"],
        ),
        Machine(
            id="PACK_1",
            name="Packaging Station",
            capabilities=["packaging"],
        ),
    ]


def test_dependency_precedence(mock_factory_machines):
    """Ensure downstream job waits until upstream prerequisite finishes."""
    engine = ScheduleEngine(machines=mock_factory_machines)

    job_a = Job(
        id="JOB_A",
        name="Formulation",
        required_capability="mixing",
        duration_minutes=60,
        priority=JobPriority.MEDIUM,
    )
    job_b = Job(
        id="JOB_B",
        name="Sterilisation",
        required_capability="autoclave",
        duration_minutes=30,
        priority=JobPriority.MEDIUM,
        depends_on=["JOB_A"],
    )

    result = engine.schedule([job_b, job_a])

    task_a = next(t for t in result.tasks if t.job_id == "JOB_A")
    task_b = next(t for t in result.tasks if t.job_id == "JOB_B")

    assert task_b.start_time >= task_a.end_time
    assert result.makespan_minutes == 90
    assert len(result.unassigned_jobs) == 0


def test_priority_tiebreaking(mock_factory_machines):
    """High priority job should run first during contention."""
    engine = ScheduleEngine(machines=mock_factory_machines)

    job_low = Job(
        id="LOW_JOB",
        name="Routine Batch",
        required_capability="dispensing",
        duration_minutes=40,
        priority=JobPriority.LOW,
    )
    job_urgent = Job(
        id="URGENT_JOB",
        name="Emergency Hospital Order",
        required_capability="dispensing",
        duration_minutes=40,
        priority=JobPriority.CRITICAL,
    )

    result = engine.schedule([job_low, job_urgent])

    task_urgent = next(t for t in result.tasks if t.job_id == "URGENT_JOB")
    task_low = next(t for t in result.tasks if t.job_id == "LOW_JOB")

    assert task_urgent.start_time == 0
    assert task_low.start_time >= task_urgent.end_time


def test_cyclic_dependency_handled_gracefully(mock_factory_machines):
    """Circular dependencies must be caught without crashing."""
    engine = ScheduleEngine(machines=mock_factory_machines)

    job_1 = Job(
        id="J1",
        name="Deadlock 1",
        required_capability="mixing",
        duration_minutes=20,
        depends_on=["J2"],
    )
    job_2 = Job(
        id="J2",
        name="Deadlock 2",
        required_capability="mixing",
        duration_minutes=20,
        depends_on=["J1"],
    )

    result = engine.schedule([job_1, job_2])

    assert len(result.tasks) == 0
    assert "J1" in result.unassigned_jobs
    assert "J2" in result.unassigned_jobs