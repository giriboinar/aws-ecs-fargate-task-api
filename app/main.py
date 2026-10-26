"""FastAPI Task API for the AWS ECS Fargate demo.

A small, dependency-light service: in-memory task CRUD, a health
endpoint for the ALB target-group health check, and a Prometheus
/metrics endpoint for CloudWatch/Prometheus scraping.
"""

import os
import uuid

from fastapi import FastAPI, HTTPException
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    Counter,
    Gauge,
    generate_latest,
)
from pydantic import BaseModel, Field
from starlette.responses import Response

app = FastAPI(
    title="ECS Fargate Task API",
    description="Demo Task API deployed on AWS ECS Fargate behind an ALB.",
    version="1.0.0",
)

TASKS_CREATED = Counter(
    "tasks_created_total", "Total number of tasks created"
)
TASKS_TOTAL = Gauge("tasks_total", "Current number of stored tasks")

tasks: dict[str, dict] = {}


class TaskCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    done: bool = False


class Task(TaskCreate):
    id: str


@app.get("/")
def root():
    return {"service": "ecs-fargate-task-api", "status": "ok"}


@app.get("/health")
def health():
    return {"status": "ok", "tasks": len(tasks)}


@app.get("/metrics")
def metrics():
    TASKS_TOTAL.set(len(tasks))
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.get("/tasks", response_model=list[Task])
def list_tasks():
    return list(tasks.values())


@app.post("/tasks", response_model=Task, status_code=201)
def create_task(task: TaskCreate):
    task_id = str(uuid.uuid4())
    record = {"id": task_id, "title": task.title, "done": task.done}
    tasks[task_id] = record
    TASKS_CREATED.inc()
    return record


@app.get("/tasks/{task_id}", response_model=Task)
def get_task(task_id: str):
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    return tasks[task_id]


@app.delete("/tasks/{task_id}", status_code=204)
def delete_task(task_id: str):
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    del tasks[task_id]
    return None


if __name__ == "__main__":  # pragma: no cover
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.environ.get("PORT", "8000")),
    )
