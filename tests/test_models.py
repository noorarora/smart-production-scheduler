import pytest
from pydantic import ValidationError
from app.models.schemas import Job, JobPriority, Machine, ScheduleRequest


def test_job_validation_success():
    job = Job(
        id="JOB_001",
        name="Media Preparation",
        required_capability="media_prep",
        duration_minutes=60,
        priority=JobPriority.CRITICAL,
        depends_on=[],
    )
    assert job.id == "JOB_001"
    assert job.priority == JobPriority.CRITICAL


def test_job_negative_duration_fails():
    with pytest.raises(ValidationError):
        Job(
            id="JOB_002",
            name="Defective Formulation",
            required_capability="formulation",
            duration_minutes=-10,
        )


def test_machine_initialisation():
    machine = Machine(
        id="M_AUTOCLAVE_1",
        name="Industrial Autoclave A",
        capabilities=["sterilisation", "media_prep"],
    )
    assert "sterilisation" in machine.capabilities


def test_schedule_request_rejects_duplicate_job_ids():
    jobs = [
        Job(id="J1", name="First", required_capability="mixing", duration_minutes=10),
        Job(id="J1", name="Duplicate", required_capability="mixing", duration_minutes=20),
    ]

    with pytest.raises(ValidationError, match="Job IDs must be unique"):
        ScheduleRequest(machines=[], jobs=jobs)


def test_schedule_request_rejects_unknown_dependency():
    job = Job(
        id="J1",
        name="Dependent batch",
        required_capability="mixing",
        duration_minutes=10,
        depends_on=["MISSING_JOB"],
    )

    with pytest.raises(ValidationError, match="unknown dependencies: MISSING_JOB"):
        ScheduleRequest(machines=[], jobs=[job])


def test_schedule_request_rejects_self_dependency():
    job = Job(
        id="J1",
        name="Invalid batch",
        required_capability="mixing",
        duration_minutes=10,
        depends_on=["J1"],
    )

    with pytest.raises(ValidationError, match="cannot depend on itself"):
        ScheduleRequest(machines=[], jobs=[job])
