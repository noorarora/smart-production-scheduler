# Scheduling metrics reference

The scheduler returns operational metrics alongside the generated task list so schedule quality can be inspected without recalculating values in the UI.

## Makespan

`makespan_minutes` is the end time of the final scheduled task. It represents the total elapsed schedule horizon from minute zero.

## Machine load

`machine_load_minutes` reports occupied minutes per machine. Load includes both processing time and sequence-dependent setup/changeover time.

Machines with no assigned work remain in the dictionary with a value of `0`. This makes the output useful for capacity comparisons because unused resources are still visible.

## Setup time

`total_setup_minutes` is the sum of all changeover time added by product-family transitions. A machine-specific changeover matrix takes precedence over the fallback `changeover_minutes` value.

## Lateness

A task is late when its completion time exceeds `due_minute`.

- `late_jobs` lists the IDs of jobs that finish late.
- `lateness_minutes` on each scheduled task records that task’s delay.
- `total_tardiness_minutes` is the sum of lateness across all late jobs.

Jobs without a due date contribute zero tardiness.

## Unassigned work

`unassigned_jobs` contains jobs that could not be scheduled, for example because no machine provides the required capability or because unresolved dependencies prevent progress.

Unassigned jobs do not add processing time to makespan or machine-load metrics.

## Regression coverage

`tests/test_schedule_metrics.py` verifies that unused machines remain visible in load output, unassigned work does not inflate schedule metrics, and tardiness is accumulated correctly across dependency chains.
