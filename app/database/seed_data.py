from typing import List, Tuple
from app.models.schemas import Job, JobPriority, Machine


def get_default_factory_setup() -> Tuple[List[Machine], List[Job]]:
    """Generates a realistic 3-stage biomanufacturing plant scenario.

    Stage 1: Media Preparation / Dispensing
    Stage 2: High-Pressure Autoclave Sterilisation
    Stage 3: Automated Filling & Packaging
    """
    machines = [
        Machine(
            id="M_PREP_01",
            name="Dispensing Suite A",
            capabilities=["dispensing", "mixing"],
        ),
        Machine(
            id="M_PREP_02",
            name="Dispensing Suite B",
            capabilities=["dispensing"],
        ),
        Machine(
            id="M_STERILE_01",
            name="Industrial Autoclave Alpha",
            capabilities=["autoclave"],
        ),
        Machine(
            id="M_STERILE_02",
            name="Industrial Autoclave Beta",
            capabilities=["autoclave"],
        ),
        Machine(
            id="M_PACK_01",
            name="High-Speed Bottling Line",
            capabilities=["packaging", "labeling"],
        ),
    ]

    # Batch A: High priority diagnostic reagents (dependency chain: Prep -> Sterile -> Pack)
    batch_a_jobs = [
        Job(
            id="BATCH_A_PREP",
            name="Formulate Agar Base (Batch A)",
            required_capability="dispensing",
            duration_minutes=90,
            priority=JobPriority.CRITICAL,
            depends_on=[],
        ),
        Job(
            id="BATCH_A_STERILE",
            name="Sterilise Agar Base (Batch A)",
            required_capability="autoclave",
            duration_minutes=60,
            priority=JobPriority.CRITICAL,
            depends_on=["BATCH_A_PREP"],
        ),
        Job(
            id="BATCH_A_PACK",
            name="Aseptic Fill & Pack (Batch A)",
            required_capability="packaging",
            duration_minutes=45,
            priority=JobPriority.CRITICAL,
            depends_on=["BATCH_A_STERILE"],
        ),
    ]

    # Batch B: Standard hospital transport media (Routine priority)
    batch_b_jobs = [
        Job(
            id="BATCH_B_PREP",
            name="Formulate Broth (Batch B)",
            required_capability="dispensing",
            duration_minutes=60,
            priority=JobPriority.MEDIUM,
            depends_on=[],
        ),
        Job(
            id="BATCH_B_STERILE",
            name="Sterilise Broth (Batch B)",
            required_capability="autoclave",
            duration_minutes=75,
            priority=JobPriority.MEDIUM,
            depends_on=["BATCH_B_PREP"],
        ),
        Job(
            id="BATCH_B_PACK",
            name="Bottling & Labeling (Batch B)",
            required_capability="packaging",
            duration_minutes=60,
            priority=JobPriority.MEDIUM,
            depends_on=["BATCH_B_STERILE"],
        ),
    ]

    # Independent quick quality control task
    independent_jobs = [
        Job(
            id="QC_BUFFER_MIX",
            name="Buffer Prep for Calibration",
            required_capability="mixing",
            duration_minutes=30,
            priority=JobPriority.HIGH,
            depends_on=[],
        )
    ]

    all_jobs = batch_a_jobs + batch_b_jobs + independent_jobs
    return machines, all_jobs