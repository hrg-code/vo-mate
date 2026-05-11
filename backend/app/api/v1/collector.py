from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException

from app.repositories.memory_store import repository
from app.schemas.common import AgentTask

router = APIRouter(prefix="/collector", tags=["collector"])


@router.post("/tasks", response_model=AgentTask)
def create_collector_task(payload: Dict[str, Any]) -> AgentTask:
    return repository.create_task("collector", payload)


@router.get("/tasks", response_model=List[AgentTask])
def list_collector_tasks() -> List[AgentTask]:
    return [task for task in repository.tasks if "collector" in task.id or "ETL" in task.name]


@router.get("/tasks/{task_id}", response_model=AgentTask)
def get_collector_task(task_id: str) -> AgentTask:
    task = next((task for task in repository.tasks if task.id == task_id), None)
    if task is None:
        raise HTTPException(status_code=404, detail="Collector task not found")
    return task


@router.post("/upload")
def upload_collected_data(payload: Dict[str, Any]) -> Dict[str, Any]:
    raw = repository.add_raw_upload(payload)
    task = repository.create_task("etl", {"rawId": raw["id"]})
    return {"rawId": raw["id"], "taskId": task.id, "status": "accepted"}


@router.get("/logs")
def list_collector_logs() -> List[Dict[str, Any]]:
    return [{"level": "info", "message": "Collector API ready", "source": "fastapi"}]


@router.post("/import")
def import_raw_data(payload: Dict[str, Any]) -> Dict[str, str]:
    task = repository.create_task("raw-import", payload)
    return {"taskId": task.id, "status": task.status.value}
