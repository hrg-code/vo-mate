from typing import List

from fastapi import APIRouter
from pydantic import BaseModel

from app.repositories.content_item_repository import content_item_repository
from app.repositories.memory_store import repository
from app.schemas.common import AgentTask, ContentItem, MetricSummary

router = APIRouter(prefix="/analytics", tags=["analytics"])


class DashboardResponse(BaseModel):
    metrics: List[MetricSummary]
    contents: List[ContentItem]
    tasks: List[AgentTask]


@router.get("/dashboard", response_model=DashboardResponse)
def get_dashboard() -> DashboardResponse:
    contents = content_item_repository.list_contents(limit=3)
    return DashboardResponse(metrics=repository.metrics, contents=contents or repository.contents[:3], tasks=repository.tasks)


@router.get("/dashboard/overview", response_model=DashboardResponse)
def get_dashboard_overview() -> DashboardResponse:
    return get_dashboard()
