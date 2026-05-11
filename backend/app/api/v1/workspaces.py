from fastapi import APIRouter

from app.repositories.memory_store import repository
from app.schemas.common import WorkspaceContext

router = APIRouter(prefix="/workspaces", tags=["workspaces"])


@router.get("/current", response_model=WorkspaceContext)
def get_current_workspace() -> WorkspaceContext:
    return repository.workspace
