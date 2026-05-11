from __future__ import annotations

from typing import Any

from app.agents.graphs.content_creation_graph import build_content_creation_graph
from app.agents.runtime.checkpoint import checkpoint_store
from app.agents.runtime.state import ContentCreationState


class AgentGraphRunner:
    def __init__(self) -> None:
        self._content_creation_graph = build_content_creation_graph()

    def run_content_creation(self, initial_state: ContentCreationState) -> ContentCreationState:
        final_state = self._content_creation_graph.invoke(initial_state)
        thread_id = final_state.get("thread_id")
        if thread_id:
            checkpoint_store.save(thread_id, dict(final_state))
        return final_state

    def get_checkpoint(self, thread_id: str) -> dict[str, Any] | None:
        return checkpoint_store.get(thread_id)


agent_graph_runner = AgentGraphRunner()

