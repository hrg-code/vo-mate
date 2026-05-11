from __future__ import annotations

from app.agents.runtime.events import record_step
from app.agents.runtime.state import ContentCreationState
from app.agents.tools.content_lookup_tool import get_workspace_context
from app.agents.tools.platform_policy_tool import get_platform_policy
from app.schemas.agent import AgentWorkbenchRequest
from app.services.agent_store_service import agent_store


def load_account_context(state: ContentCreationState) -> ContentCreationState:
    request = AgentWorkbenchRequest(**state["request"])
    previous_summary = agent_store.get_summary(request.thread_id)
    output = {
        "workspace": get_workspace_context(),
        "accountId": request.account_id,
        "persona": "15 年野生程序员，高中学历，普通人视角，AI 自救方向。",
        "platformPolicy": get_platform_policy(request.platform),
        "previousSummary": previous_summary.model_dump(by_alias=True) if previous_summary else None,
    }
    record_step(state["run_id"], "load_account_context", {"threadId": request.thread_id}, output)
    return {"account_context": output}

