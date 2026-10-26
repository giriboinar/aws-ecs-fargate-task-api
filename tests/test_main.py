"""Tests for the ECS Fargate Task API (run with pytest)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app"))

from fastapi.testclient import TestClient  # noqa: E402

from main import app, tasks  # noqa: E402

client = TestClient(app)


def setup_function():
    tasks.clear()


def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_health_empty():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "tasks": 0}


def test_create_and_get_task():
    created = client.post("/tasks", json={"title": "Deploy to Fargate"})
    assert created.status_code == 201
    task_id = created.json()["id"]
    assert created.json()["title"] == "Deploy to Fargate"
    assert created.json()["done"] is False

    fetched = client.get(f"/tasks/{task_id}")
    assert fetched.status_code == 200
    assert fetched.json()["id"] == task_id


def test_list_tasks():
    client.post("/tasks", json={"title": "First"})
    client.post("/tasks", json={"title": "Second", "done": True})
    response = client.get("/tasks")
    assert response.status_code == 200
    assert len(response.json()) == 2


def test_get_missing_task_404():
    response = client.get("/tasks/does-not-exist")
    assert response.status_code == 404


def test_delete_task():
    created = client.post("/tasks", json={"title": "To delete"})
    task_id = created.json()["id"]
    deleted = client.delete(f"/tasks/{task_id}")
    assert deleted.status_code == 204
    assert client.get(f"/tasks/{task_id}").status_code == 404


def test_create_task_validation():
    response = client.post("/tasks", json={"title": ""})
    assert response.status_code == 422


def test_metrics_exposes_task_counters():
    client.post("/tasks", json={"title": "Metric check"})
    response = client.get("/metrics")
    assert response.status_code == 200
    assert b"tasks_created_total" in response.content
    assert b"tasks_total" in response.content
