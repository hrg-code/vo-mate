from typing import List

from fastapi import APIRouter, HTTPException

from app.schemas.agent import (
    AgentRunRecord,
    AgentRunStepRecord,
    AgentThreadSummaryRecord,
    AgentWorkbenchRequest,
    AgentWorkbenchResponse,
)
from app.services.agent_store_service import agent_store
from app.services.agent_workbench_service import agent_workbench_service

router = APIRouter(prefix="/agent", tags=["agent"])


@router.post("/topic-workbench/run", response_model=AgentWorkbenchResponse)
def run_topic_workbench(payload: AgentWorkbenchRequest) -> AgentWorkbenchResponse:
    return agent_workbench_service.run(payload)


@router.get("/runs/{run_id}", response_model=AgentRunRecord)
def get_agent_run(run_id: str) -> AgentRunRecord:
    run = agent_store.get_run(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Agent run not found")
    return run


@router.get("/runs/{run_id}/steps", response_model=List[AgentRunStepRecord])
def get_agent_run_steps(run_id: str) -> List[AgentRunStepRecord]:
    return agent_store.get_steps(run_id)


@router.get("/runs/{run_id}/retrieval-traces")
def get_agent_retrieval_traces(run_id: str):
    return agent_store.get_traces(run_id)


@router.get("/threads/{thread_id}/summary", response_model=AgentThreadSummaryRecord)
def get_thread_summary(thread_id: str) -> AgentThreadSummaryRecord:
    summary = agent_store.get_summary(thread_id)
    if summary is None:
        raise HTTPException(status_code=404, detail="Agent thread summary not found")
    return summary


@router.post("/threads/{thread_id}/compress", response_model=AgentThreadSummaryRecord)
def compress_thread(thread_id: str) -> AgentThreadSummaryRecord:
    existing = agent_store.get_summary(thread_id)
    if existing is not None:
        return existing
    return agent_store.save_summary(
        thread_id=thread_id,
        workspace_id="ws_northstar",
        member_id="m_demo",
        account_id="douyin_demo",
        summary="该线程暂无历史上下文，已创建空摘要。",
        decisions=[],
        rejected_ideas=[],
        pending_tasks=[],
    )
