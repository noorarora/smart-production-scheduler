from enum import IntEnum
from typing import List, Optional
from pydantic import BaseModel, Field, model_validator


class JobPriority(IntEnum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


class TimeWindow(BaseModel):
    start_minute: int = Field(ge=0)
    end_minute: int = Field(gt=0)

    @model_validator(mode="after")
    def validate_window(self):
        if self.end_minute <= self.start_minute:
            raise ValueError("Availability window end must be after start")
        return self


class Machine(BaseModel):
    id: str
    name: str
    capabilities: List[str] = Field(default_factory=list)
    unavailable_windows: List[TimeWindow] = Field(
        default_factory=list,
        description="Machine downtime intervals in minutes from schedule start",
    )


class Job(BaseModel):
    id: str
    name: str
    required_capability: str
    duration_minutes: int = Field(gt=0, description="Duration must be positive")
    priority: JobPriority = JobPriority.MEDIUM
    due_minute: Optional[int] = Field(
        default=None,
        ge=0,
        description="Target completion time in minutes from schedule start",
    )
    depends_on: List[str] = Field(
        default_factory=list,
        description="IDs of prerequisite jobs that must complete before this job can start",
    )


class ScheduledTask(BaseModel):
    job_id: str
    machine_id: str
    start_time: int  # Minutes from start of simulation (T=0)
    end_time: int
    due_minute: Optional[int] = None
    lateness_minutes: int = Field(default=0, ge=0)


class ScheduleOutput(BaseModel):
    tasks: List[ScheduledTask]
    makespan_minutes: int
    unassigned_jobs: List[str] = Field(default_factory=list)
    late_jobs: List[str] = Field(default_factory=list)
    total_tardiness_minutes: int = Field(default=0, ge=0)


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
        dependency_graph = {job.id: job.depends_on for job in self.jobs}

        for job in self.jobs:
            if job.id in job.depends_on:
                raise ValueError(f"Job '{job.id}' cannot depend on itself")

            unknown_dependencies = set(job.depends_on) - known_job_ids
            if unknown_dependencies:
                missing = ", ".join(sorted(unknown_dependencies))
                raise ValueError(
                    f"Job '{job.id}' references unknown dependencies: {missing}"
                )

        visiting = set()
        visited = set()
        path: List[str] = []

        def visit(job_id: str) -> None:
            if job_id in visiting:
                cycle_start = path.index(job_id)
                cycle = path[cycle_start:] + [job_id]
                raise ValueError(
                    f"Dependency cycle detected: {' -> '.join(cycle)}"
                )

            if job_id in visited:
                return

            visiting.add(job_id)
            path.append(job_id)

            for dependency_id in dependency_graph[job_id]:
                visit(dependency_id)

            path.pop()
            visiting.remove(job_id)
            visited.add(job_id)

        for job_id in job_ids:
            visit(job_id)

        return self
