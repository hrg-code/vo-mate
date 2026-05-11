from typing import List

from fastapi import APIRouter
from pydantic import BaseModel

from app.repositories.memory_store import repository
from app.schemas.common import AgentTask, ContentItem, MetricSummary

router = APIRouter(prefix="/analytics", tags=["analytics"])


class DashboardResponse(BaseModel):
    metrics: List[MetricSummary]
    contents: List[ContentItem]
    tasks: List[AgentTask]


@router.get("/dashboard", response_model=DashboardResponse)
def get_dashboard() -> DashboardResponse:
    return DashboardResponse(metrics=repository.metrics, contents=repository.contents[:3], tasks=repository.tasks)


@router.get("/dashboard/overview", response_model=DashboardResponse)
def get_dashboard_overview() -> DashboardResponse:
    return get_dashboard()
