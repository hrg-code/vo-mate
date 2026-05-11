from __future__ import annotations

from app.agents.chains.summary_chain import summary_chain
from app.agents.runtime.events import record_step
from app.agents.runtime.state import ContentCreationState
from app.schemas.agent import AgentWorkbenchRequest
from app.services.agent_store_service import agent_store


def compress_thread_memory(state: ContentCreationState) -> ContentCreationState:
    request = AgentWorkbenchRequest(**state["request"])
    summary = summary_chain.invoke(request.topic, state.get("strategy", {}))
    decisions = [{"topic": request.topic, "targetDurationSeconds": request.target_duration_seconds}]
    rejected_ideas = [{"idea": "过度焦虑标题", "reason": "风险分偏高且人设不稳定"}]
    pending_tasks = ["等待用户确认标题或继续改写脚本"]
    record = agent_store.save_summary(
        thread_id=request.thread_id,
        workspace_id=request.workspace_id,
        member_id=request.member_id,
        account_id=request.account_id,
        summary=summary,
        decisions=decisions,
        rejected_ideas=rejected_ideas,
        pending_tasks=pending_tasks,
    )
    record_step(state["run_id"], "compress_thread_memory", {"threadId": request.thread_id}, record.model_dump(by_alias=True))
    return {}

