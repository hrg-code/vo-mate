from __future__ import annotations

from app.agents.runtime.events import record_step
from app.agents.runtime.state import ContentCreationState


def schedule_memory_learning(state: ContentCreationState) -> ContentCreationState:
    output = {
        "scheduled": True,
        "workflow": "memory-learning",
        "reason": "MVP 仅记录调度意图，后续接入 Redis 或任务表。",
    }
    record_step(state["run_id"], "schedule_memory_learning", {"runId": state["run_id"]}, output)
    return {}

