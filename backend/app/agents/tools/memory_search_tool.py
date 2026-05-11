from __future__ import annotations

from app.schemas.agent import AgentEvidence, MemorySearchRequest
from app.services.memory_record_service import memory_vector_service


class MemorySearchTool:
    def invoke(self, request: MemorySearchRequest, run_id: str) -> list[AgentEvidence]:
        return memory_vector_service.search(request, run_id=run_id)


memory_search_tool = MemorySearchTool()

