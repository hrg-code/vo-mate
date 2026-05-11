from __future__ import annotations

from app.repositories.memory_store import repository


def get_workspace_context() -> dict[str, object]:
    return repository.workspace.model_dump(by_alias=True)

