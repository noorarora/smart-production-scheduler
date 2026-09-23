from typing import Dict, List, Optional
from app.models.schemas import Job, Machine, ScheduleOutput, ScheduledTask


class ScheduleEngine:
    """Deterministic heuristic scheduler using priority-based greedy dispatching

    with precedence, machine capability, availability, due-date, and changeover
    constraints.
    """

    def __init__(self, machines: List[Machine]):
        self.machines = {m.id: m for m in machines}

    @staticmethod
    def _next_available_start(
        machine: Machine,
        earliest_start: int,
        duration_minutes: int,
    ) -> int:
        """Return the earliest start that does not overlap machine downtime."""
        candidate_start = earliest_start

        for window in sorted(
            machine.unavailable_windows,
            key=lambda item: item.start_minute,
        ):
            candidate_end = candidate_start + duration_minutes

            if candidate_end <= window.start_minute:
                break

            if candidate_start >= window.end_minute:
                continue

            candidate_start = window.end_minute

        return candidate_start

    @staticmethod
    def _changeover_minutes(
        machine: Machine,
        previous_product_family: Optional[str],
        next_product_family: Optional[str],
    ) -> int:
        """Return directional setup time for a product-family transition."""
        if (
            previous_product_family is None
            or next_product_family is None
            or previous_product_family == next_product_family
        ):
            return 0

        matrix_minutes = machine.changeover_matrix.get(
            previous_product_family, {}
        ).get(next_product_family)
        if matrix_minutes is not None:
            return matrix_minutes

        return machine.changeover_minutes

    def schedule(self, jobs: List[Job]) -> ScheduleOutput:
        scheduled_tasks: List[ScheduledTask] = []
        unassigned_jobs: List[str] = []
        late_jobs: List[str] = []
        total_tardiness_minutes = 0
        total_setup_minutes = 0

        machine_free_at: Dict[str, int] = {m_id: 0 for m_id in self.machines}
        machine_product_family: Dict[str, Optional[str]] = {
            m_id: None for m_id in self.machines
        }
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
                key=lambda j: (
                    -int(j.priority),
                    j.due_minute if j.due_minute is not None else float("inf"),
                    j.duration_minutes,
                )
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
            best_setup_start = 0
            best_processing_start = 0
            best_end_time = float("inf")
            best_setup_minutes = 0

            for m_id in compatible_machines:
                machine = self.machines[m_id]
                setup_minutes = self._changeover_minutes(
                    machine=machine,
                    previous_product_family=machine_product_family[m_id],
                    next_product_family=job_to_schedule.product_family,
                )
                earliest_setup_start = max(machine_free_at[m_id], dep_finish_time)
                occupied_duration = setup_minutes + job_to_schedule.duration_minutes
                setup_start = self._next_available_start(
                    machine=machine,
                    earliest_start=earliest_setup_start,
                    duration_minutes=occupied_duration,
                )
                processing_start = setup_start + setup_minutes
                possible_end = processing_start + job_to_schedule.duration_minutes

                if possible_end < best_end_time:
                    best_end_time = possible_end
                    best_setup_start = setup_start
                    best_processing_start = processing_start
                    best_machine_id = m_id
                    best_setup_minutes = setup_minutes

            lateness_minutes = (
                max(0, int(best_end_time) - job_to_schedule.due_minute)
                if job_to_schedule.due_minute is not None
                else 0
            )

            task = ScheduledTask(
                job_id=job_to_schedule.id,
                machine_id=best_machine_id,
                product_family=job_to_schedule.product_family,
                setup_start_time=best_setup_start,
                setup_minutes=best_setup_minutes,
                start_time=best_processing_start,
                end_time=best_end_time,
                due_minute=job_to_schedule.due_minute,
                lateness_minutes=lateness_minutes,
            )
            scheduled_tasks.append(task)
            total_setup_minutes += best_setup_minutes

            if lateness_minutes > 0:
                late_jobs.append(job_to_schedule.id)
                total_tardiness_minutes += lateness_minutes

            machine_free_at[best_machine_id] = int(best_end_time)
            if job_to_schedule.product_family is not None:
                machine_product_family[best_machine_id] = job_to_schedule.product_family
            job_completion_times[job_to_schedule.id] = int(best_end_time)
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
            late_jobs=late_jobs,
            total_tardiness_minutes=total_tardiness_minutes,
            total_setup_minutes=total_setup_minutes,
        )
