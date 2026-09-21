import pytest
from pydantic import ValidationError

from app.engine.scheduler import ScheduleEngine
from app.models.schemas import Job, JobPriority, Machine, TimeWindow


def test_negative_machine_changeover_is_rejected():
    with pytest.raises(ValidationError):
        Machine(
            id="M1",
            name="Mixer",
            capabilities=["mixing"],
            changeover_minutes=-1,
        )


def test_product_family_switch_adds_changeover_time():
    machine = Machine(
        id="M1",
        name="Mixer",
        capabilities=["mixing"],
        changeover_minutes=15,
    )
    engine = ScheduleEngine(machines=[machine])
    jobs = [
        Job(
            id="J1",
            name="Family A",
            required_capability="mixing",
            duration_minutes=30,
            priority=JobPriority.HIGH,
            product_family="A",
        ),
        Job(
            id="J2",
            name="Family B",
            required_capability="mixing",
            duration_minutes=20,
            priority=JobPriority.MEDIUM,
            product_family="B",
        ),
    ]

    result = engine.schedule(jobs)
    second = next(task for task in result.tasks if task.job_id == "J2")

    assert second.setup_start_time == 30
    assert second.setup_minutes == 15
    assert second.start_time == 45
    assert second.end_time == 65
    assert result.total_setup_minutes == 15
    assert result.makespan_minutes == 65


def test_same_product_family_does_not_add_changeover():
    machine = Machine(
        id="M1",
        name="Mixer",
        capabilities=["mixing"],
        changeover_minutes=15,
    )
    engine = ScheduleEngine(machines=[machine])
    jobs = [
        Job(
            id="J1",
            name="Family A first",
            required_capability="mixing",
            duration_minutes=30,
            priority=JobPriority.HIGH,
            product_family="A",
        ),
        Job(
            id="J2",
            name="Family A second",
            required_capability="mixing",
            duration_minutes=20,
            priority=JobPriority.MEDIUM,
            product_family="A",
        ),
    ]

    result = engine.schedule(jobs)
    second = next(task for task in result.tasks if task.job_id == "J2")

    assert second.setup_minutes == 0
    assert second.start_time == 30
    assert second.end_time == 50
    assert result.total_setup_minutes == 0


def test_machine_selection_accounts_for_changeover_overhead():
    machines = [
        Machine(
            id="M1",
            name="Line A",
            capabilities=["mixing"],
            changeover_minutes=20,
        ),
        Machine(
            id="M2",
            name="Line B",
            capabilities=["mixing"],
            changeover_minutes=20,
        ),
    ]
    engine = ScheduleEngine(machines=machines)
    jobs = [
        Job(
            id="A1",
            name="Prime A",
            required_capability="mixing",
            duration_minutes=10,
            priority=JobPriority.CRITICAL,
            product_family="A",
        ),
        Job(
            id="B1",
            name="Prime B",
            required_capability="mixing",
            duration_minutes=10,
            priority=JobPriority.HIGH,
            product_family="B",
        ),
        Job(
            id="A2",
            name="Continue A",
            required_capability="mixing",
            duration_minutes=10,
            priority=JobPriority.MEDIUM,
            product_family="A",
        ),
    ]

    result = engine.schedule(jobs)
    continued_family = next(task for task in result.tasks if task.job_id == "A2")

    assert continued_family.machine_id == "M1"
    assert continued_family.setup_minutes == 0
    assert continued_family.start_time == 10


def test_changeover_and_processing_avoid_downtime_together():
    machine = Machine(
        id="M1",
        name="Mixer",
        capabilities=["mixing"],
        changeover_minutes=15,
        unavailable_windows=[TimeWindow(start_minute=25, end_minute=40)],
    )
    engine = ScheduleEngine(machines=[machine])
    jobs = [
        Job(
            id="J1",
            name="Family A",
            required_capability="mixing",
            duration_minutes=20,
            priority=JobPriority.HIGH,
            product_family="A",
        ),
        Job(
            id="J2",
            name="Family B",
            required_capability="mixing",
            duration_minutes=20,
            priority=JobPriority.MEDIUM,
            product_family="B",
        ),
    ]

    result = engine.schedule(jobs)
    second = next(task for task in result.tasks if task.job_id == "J2")

    assert second.setup_start_time == 40
    assert second.start_time == 55
    assert second.end_time == 75
