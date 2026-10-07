import pytest
from fastapi.testclient import TestClient

from app.engine.scheduler import ScheduleEngine
from app.main import app
from app.models.schemas import Job, Machine, TimeWindow


def test_release_waits_for_materials_and_avoids_downtime():
    machine = Machine(
        id="M", name="Mixer", capabilities=["mix"],
        changeover_minutes=10,
        unavailable_windows=[TimeWindow(start_minute=40, end_minute=70)],
    )
    jobs = [
        Job(id="A", name="A", required_capability="mix", duration_minutes=10,
            priority=4, product_family="A"),
        Job(id="B", name="B", required_capability="mix", duration_minutes=20,
            product_family="B", release_minute=30, depends_on=["A"], due_minute=90),
    ]
    result = ScheduleEngine([machine]).schedule(jobs)
    task = result.tasks[1]
    assert (task.setup_start_time, task.start_time, task.end_time) == (70, 80, 100)
    assert result.total_tardiness_minutes == 10
    assert result.machine_load_minutes == {"M": 40}


def test_dependency_can_finish_after_release():
    machine = Machine(id="M", name="Mixer", capabilities=["mix"])
    jobs = [
        Job(id="A", name="A", required_capability="mix", duration_minutes=50),
        Job(id="B", name="B", required_capability="mix", duration_minutes=10,
            release_minute=20, depends_on=["A"]),
    ]
    result = ScheduleEngine([machine]).schedule(jobs)
    assert result.tasks[1].start_time == 50


@pytest.mark.parametrize("release, status", [(15, 200), (-1, 422)])
def test_release_api_validation(release, status):
    response = TestClient(app).post("/schedule", json={
        "machines": [{"id": "M", "name": "Mixer", "capabilities": ["mix"]}],
        "jobs": [{"id": "A", "name": "A", "required_capability": "mix",
                  "duration_minutes": 45, "release_minute": release}],
    })
    assert response.status_code == status
    if status == 200:
        assert response.json()["tasks"][0]["start_time"] == 15
        assert response.json()["makespan_minutes"] == 60
