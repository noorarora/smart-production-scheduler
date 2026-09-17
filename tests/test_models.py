import pytest
from pydantic import ValidationError
from app.models.schemas import Job, JobPriority, Machine


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