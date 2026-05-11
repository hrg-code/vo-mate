from __future__ import annotations

from typing import Any


class InMemoryCheckpointStore:
    """Tiny checkpoint boundary until PostgreSQL checkpointer is introduced."""

    def __init__(self) -> None:
        self._states: dict[str, dict[str, Any]] = {}

    def save(self, thread_id: str, state: dict[str, Any]) -> None:
        self._states[thread_id] = dict(state)

    def get(self, thread_id: str) -> dict[str, Any] | None:
        state = self._states.get(thread_id)
        if state is None:
            return None
        return dict(state)


checkpoint_store = InMemoryCheckpointStore()

