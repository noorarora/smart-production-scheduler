from typing import Dict, List, Set
from app.models.schemas import Job, Machine, ScheduleOutput, ScheduledTask


class ScheduleEngine:
    """Deterministic heuristic scheduler using priority-based greedy dispatching

    with precedence and machine capability constraints.
    """

    def __init__(self, machines: List[Machine]):
        self.machines = {m.id: m for m in machines}

    def schedule(self, jobs: List[Job]) -> ScheduleOutput:
        scheduled_tasks: List[ScheduledTask] = []
        unassigned_jobs: List[str] = []

        machine_free_at: Dict[str, int] = {m_id: 0 for m_id in self.machines}
        job_completion_times: Dict[str, int] = {}
        pending_jobs: Dict[str, Job] = {j.id: j for j in jobs}

        while pending_jobs:
            ready_jobs: List[Job] = [
                j
                for j in pending_jobs.values()
                if all(dep in job_completion_times for dep in j.depends_on)
            ]

            if not ready_jobs:
                unassigned_jobs.extend(list(pending_jobs.keys()))
                break

            ready_jobs.sort(
                key=lambda j: (-int(j.priority), j.duration_minutes)
            )
            job_to_schedule = ready_jobs[0]

            compatible_machines = [
                m_id
                for m_id, m in self.machines.items()
                if job_to_schedule.required_capability in m.capabilities
            ]

            if not compatible_machines:
                unassigned_jobs.append(job_to_schedule.id)
                del pending_jobs[job_to_schedule.id]
                continue

            dep_finish_time = (
                max(
                    job_completion_times[dep]
                    for dep in job_to_schedule.depends_on
                )
                if job_to_schedule.depends_on
                else 0
            )

            best_machine_id = None
            best_start_time = float("inf")
            best_end_time = float("inf")

            for m_id in compatible_machines:
                possible_start = max(machine_free_at[m_id], dep_finish_time)
                possible_end = possible_start + job_to_schedule.duration_minutes

                if possible_end < best_end_time:
                    best_end_time = possible_end
                    best_start_time = possible_start
                    best_machine_id = m_id

            task = ScheduledTask(
                job_id=job_to_schedule.id,
                machine_id=best_machine_id,
                start_time=best_start_time,
                end_time=best_end_time,
            )
            scheduled_tasks.append(task)

            machine_free_at[best_machine_id] = best_end_time
            job_completion_times[job_to_schedule.id] = best_end_time
            del pending_jobs[job_to_schedule.id]

        makespan = (
            max((t.end_time for t in scheduled_tasks), default=0)
            if scheduled_tasks
            else 0
        )

        return ScheduleOutput(
            tasks=scheduled_tasks,
            makespan_minutes=makespan,
            unassigned_jobs=unassigned_jobs,
        )