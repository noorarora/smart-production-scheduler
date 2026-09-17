from enum import IntEnum
from typing import List
from pydantic import BaseModel, Field


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