from __future__ import annotations

from app.agents.runtime.events import record_step
from app.agents.runtime.state import ContentCreationState
from app.schemas.agent import AgentInference, AgentWorkbenchRequest, AgentWorkbenchResponse


def finalize_response(state: ContentCreationState) -> ContentCreationState:
    request = AgentWorkbenchRequest(**state["request"])
    inferences = [
        AgentInference(claim="建议先做 45 秒版本", reason="这是基于当前选题节奏和历史留存模式的模型推断。"),
        AgentInference(claim="标题应降低纯焦虑表达", reason="可降低风险，同时保留评论讨论空间。"),
    ]
    scores = state["scores"]
    response = AgentWorkbenchResponse(
        run_id=state["run_id"],
        thread_id=request.thread_id,
        status="succeeded",
        topic_score=scores.topic_score,
        scores=scores,
        strategy=state.get("strategy", {}),
        drafts=state.get("drafts", {}),
        qa_report=state.get("qa_report", {}),
        evidence=state.get("evidence", []),
        inferences=inferences,
    )
    record_step(state["run_id"], "finalize_response", {"topic": request.topic}, response.model_dump(by_alias=True))
    return {"final_response": response}

