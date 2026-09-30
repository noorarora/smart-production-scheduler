from app.engine.scheduler import ScheduleEngine
from app.models.schemas import Job, Machine


def test_machine_load_keeps_unused_machine_visible():
    machines = [
        Machine(id="M1", name="Primary mixer", capabilities=["mixing"]),
        Machine(id="M2", name="Backup mixer", capabilities=["mixing"]),
    ]
    engine = ScheduleEngine(machines=machines)
    job = Job(
        id="J1",
        name="Short mix",
        required_capability="mixing",
        duration_minutes=15,
    )

    result = engine.schedule([job])

    assert result.machine_load_minutes == {"M1": 15, "M2": 0}


def test_unassigned_job_does_not_inflate_schedule_metrics():
    machine = Machine(id="M1", name="Mixer", capabilities=["mixing"])
    engine = ScheduleEngine(machines=[machine])
    job = Job(
        id="J1",
        name="Packaging only job",
        required_capability="packaging",
        duration_minutes=30,
    )

    result = engine.schedule([job])

    assert result.tasks == []
    assert result.makespan_minutes == 0
    assert result.machine_load_minutes == {"M1": 0}
    assert result.unassigned_jobs == ["J1"]


def test_dependency_chain_accumulates_tardiness_metrics():
    machine = Machine(id="M1", name="Mixer", capabilities=["mixing"])
    engine = ScheduleEngine(machines=[machine])
    jobs = [
        Job(
            id="A",
            name="First batch",
            required_capability="mixing",
            duration_minutes=40,
            due_minute=30,
        ),
        Job(
            id="B",
            name="Dependent batch",
            required_capability="mixing",
            duration_minutes=20,
            due_minute=50,
            depends_on=["A"],
        ),
    ]

    result = engine.schedule(jobs)

    assert result.makespan_minutes == 60
    assert result.late_jobs == ["A", "B"]
    assert result.total_tardiness_minutes == 20
    assert result.machine_load_minutes == {"M1": 60}
