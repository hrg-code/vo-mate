from typing import Any, Dict

from fastapi import APIRouter

from app.core.connections import connection_manager

router = APIRouter(prefix="/system", tags=["system"])


@router.get("/dependencies")
def get_dependency_status() -> Dict[str, Dict[str, Any]]:
    return connection_manager.dependency_status()
