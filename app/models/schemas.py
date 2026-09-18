from enum import IntEnum
from typing import List
from pydantic import BaseModel, Field, model_validator


class JobPriority(IntEnum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


class Machine(BaseModel):
    id: str
    name: str
    capabilities: List[str] = Field(default_factory=list)


class Job(BaseModel):
    id: str
    name: str
    required_capability: str
    duration_minutes: int = Field(gt=0, description="Duration must be positive")
    priority: JobPriority = JobPriority.MEDIUM
    depends_on: List[str] = Field(
        default_factory=list,
        description="IDs of prerequisite jobs that must complete before this job can start",
    )


class ScheduledTask(BaseModel):
    job_id: str
    machine_id: str
    start_time: int  # Minutes from start of simulation (T=0)
    end_time: int


class ScheduleOutput(BaseModel):
    tasks: List[ScheduledTask]
    makespan_minutes: int
    unassigned_jobs: List[str] = Field(default_factory=list)


class ScheduleRequest(BaseModel):
    machines: List[Machine]
    jobs: List[Job]

    @model_validator(mode="after")
    def validate_schedule_references(self):
        machine_ids = [machine.id for machine in self.machines]
        if len(machine_ids) != len(set(machine_ids)):
            raise ValueError("Machine IDs must be unique")

        job_ids = [job.id for job in self.jobs]
        if len(job_ids) != len(set(job_ids)):
            raise ValueError("Job IDs must be unique")

        known_job_ids = set(job_ids)
        for job in self.jobs:
            if job.id in job.depends_on:
                raise ValueError(f"Job '{job.id}' cannot depend on itself")

            unknown_dependencies = set(job.depends_on) - known_job_ids
            if unknown_dependencies:
                missing = ", ".join(sorted(unknown_dependencies))
                raise ValueError(
                    f"Job '{job.id}' references unknown dependencies: {missing}"
                )

        return self
