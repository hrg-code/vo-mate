from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException

from app.repositories.memory_store import repository
from app.schemas.agent import MemoryRecord, MemoryRecordCreate, MemoryRecordUpdate, MemorySearchRequest, MemorySearchResponse
from app.schemas.common import MemoryPattern
from app.services.memory_record_service import memory_record_service, memory_vector_service

router = APIRouter(prefix="/memory", tags=["memory"])


@router.get("/patterns", response_model=List[MemoryPattern])
def list_patterns() -> List[MemoryPattern]:
    return repository.memories


@router.post("/patterns", response_model=MemoryPattern)
def create_pattern(payload: Dict[str, Any]) -> MemoryPattern:
    pattern = MemoryPattern(
        id=f"mem_{len(repository.memories) + 1}",
        type=str(payload.get("type", "success")),
        summary=str(payload["summary"]),
        confidence=float(payload.get("confidence", 0.5)),
        source_count=int(payload.get("sourceCount", 1)),
        last_verified_at=str(payload.get("lastVerifiedAt", "2026-05-10")),
    )
    repository.memories.insert(0, pattern)
    return pattern


@router.patch("/patterns/{pattern_id}", response_model=MemoryPattern)
def update_pattern(pattern_id: str, payload: Dict[str, Any]) -> MemoryPattern:
    for index, pattern in enumerate(repository.memories):
        if pattern.id == pattern_id:
            data = pattern.model_dump()
            data.update(payload)
            updated = MemoryPattern(**data)
            repository.memories[index] = updated
            return updated
    raise HTTPException(status_code=404, detail="Memory pattern not found")


@router.delete("/patterns/{pattern_id}")
def delete_pattern(pattern_id: str) -> Dict[str, bool]:
    before = len(repository.memories)
    repository.memories = [pattern for pattern in repository.memories if pattern.id != pattern_id]
    return {"deleted": len(repository.memories) < before}


@router.post("/search")
def search_memory(payload: MemorySearchRequest) -> MemorySearchResponse:
    return MemorySearchResponse(query=payload.query, results=memory_vector_service.search(payload))


@router.post("/index-content")
def index_content(payload: Dict[str, Any]) -> Dict[str, str]:
    title = str(payload.get("title", payload.get("topic", "候选内容记忆")))
    summary = str(payload.get("summary", f"围绕“{title}”生成的候选内容记忆。"))
    memory_vector_service.upsert_memory(
        MemoryRecordCreate(
            workspace_id=str(payload.get("workspaceId", "ws_northstar")),
            account_id=str(payload.get("accountId", "douyin_demo")),
            platform=str(payload.get("platform", "douyin")),
            memory_type=str(payload.get("memoryType", "content_case")),
            title=title,
            content=str(payload.get("content", summary)),
            summary=summary,
            metadata={"topicCluster": payload.get("topicCluster", title)},
            source_type="index_content",
            source_ids=[str(payload.get("contentId", "manual"))],
            confidence=float(payload.get("confidence", 0.5)),
            evidence_count=int(payload.get("evidenceCount", 1)),
            status="candidate",
        )
    )
    task = repository.create_task("memory-index-content", payload)
    return {"taskId": task.id, "status": task.status.value}


@router.get("/records", response_model=List[MemoryRecord])
def list_memory_records() -> List[MemoryRecord]:
    return memory_record_service.list_records()


@router.post("/records", response_model=MemoryRecord)
def create_memory_record(payload: MemoryRecordCreate) -> MemoryRecord:
    return memory_vector_service.upsert_memory(payload)


@router.patch("/records/{memory_id}", response_model=MemoryRecord)
def update_memory_record(memory_id: str, payload: MemoryRecordUpdate) -> MemoryRecord:
    from app.services.agent_store_service import agent_store

    record = agent_store.update_memory(memory_id, payload)
    if record is None:
        raise HTTPException(status_code=404, detail="Memory record not found")
    return record


@router.post("/records/{memory_id}/activate", response_model=MemoryRecord)
def activate_memory_record(memory_id: str) -> MemoryRecord:
    return memory_record_service.transition(memory_id, "active")


@router.post("/records/{memory_id}/deprecate", response_model=MemoryRecord)
def deprecate_memory_record(memory_id: str) -> MemoryRecord:
    return memory_record_service.transition(memory_id, "deprecated")


@router.post("/records/{memory_id}/reject", response_model=MemoryRecord)
def reject_memory_record(memory_id: str) -> MemoryRecord:
    return memory_record_service.transition(memory_id, "rejected")
