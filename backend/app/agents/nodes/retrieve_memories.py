from __future__ import annotations

from app.agents.runtime.events import record_step
from app.agents.runtime.state import ContentCreationState
from app.agents.tools.memory_search_tool import memory_search_tool
from app.schemas.agent import MemorySearchRequest


def retrieve_memories(state: ContentCreationState) -> ContentCreationState:
    request_data = state["request"]
    topic = str(request_data["topic"])
    search_request = MemorySearchRequest(
        query=f"{topic} 普通程序员 职业路线 AI 自救",
        workspace_id=str(request_data["workspaceId"]),
        account_id=str(request_data["accountId"]),
        platform=str(request_data.get("platform", "douyin")),
        memory_types=["content_case", "persona_profile", "search_intent", "success_pattern", "failure_pattern"],
        status="active",
        top_k=8,
    )
    evidence = memory_search_tool.invoke(search_request, run_id=state["run_id"])
    output = {"evidence": [item.model_dump(by_alias=True) for item in evidence]}
    record_step(state["run_id"], "retrieve_memories", search_request.model_dump(by_alias=True), output)
    return {
        "retrieval_queries": [search_request.model_dump(by_alias=True)],
        "evidence": evidence,
    }

