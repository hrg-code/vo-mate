from typing import List

from fastapi import APIRouter

from app.repositories.memory_store import repository
from app.schemas.common import AgentTask, PublishPlan

router = APIRouter(prefix="/workflows", tags=["workflows"])


@router.get("/tasks", response_model=List[AgentTask])
def list_tasks() -> List[AgentTask]:
    return repository.tasks


@router.get("/publish-plans", response_model=List[PublishPlan])
def list_publish_plans() -> List[PublishPlan]:
    return repository.plans
