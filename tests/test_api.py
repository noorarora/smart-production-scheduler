from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {
        "status": "healthy",
        "service": "production-scheduler",
    }


def test_schedule_endpoint_valid_run():
    payload = {
        "machines": [
            {
                "id": "M1",
                "name": "Line 1",
                "capabilities": ["dispense", "pack"],
            }
        ],
        "jobs": [
            {
                "id": "J1",
                "name": "Bottle Fill",
                "required_capability": "dispense",
                "duration_minutes": 45,
                "priority": 3,
                "depends_on": [],
            }
        ],
    }
    response = client.post("/schedule", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert len(data["tasks"]) == 1
    assert data["tasks"][0]["job_id"] == "J1"
    assert data["makespan_minutes"] == 45
    assert len(data["unassigned_jobs"]) == 0


def test_schedule_endpoint_empty_payload():
    response = client.post("/schedule", json={"machines": [], "jobs": []})
    assert response.status_code == 400