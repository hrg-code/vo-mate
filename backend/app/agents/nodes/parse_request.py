from __future__ import annotations

from app.agents.runtime.events import record_step
from app.agents.runtime.state import ContentCreationState
from app.schemas.agent import AgentWorkbenchRequest


def parse_request(state: ContentCreationState) -> ContentCreationState:
    request = AgentWorkbenchRequest(**state["request"])
    output = {
        "taskType": request.task_type,
        "topic": request.topic,
        "platform": request.platform,
        "targetDurationSeconds": request.target_duration_seconds,
    }
    record_step(state["run_id"], "parse_request", state["request"], output)
    return {"topic_brief": output}

