from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from starlette.responses import StreamingResponse

from app.repositories.memory_store import repository
from app.repositories.topic_idea_repository import topic_idea_repository
from app.schemas.common import AgentTask, AIGenerationRecord, EvidenceItem, Platform, TopicIdea, TopicIdeaGenerateRequest
from app.services.ai_evidence_service import ai_evidence_service
from app.services.topic_idea_service import topic_idea_service

router = APIRouter(prefix="/ai", tags=["ai"])


@router.get("/topic-ideas", response_model=List[TopicIdea])
def list_topic_ideas() -> List[TopicIdea]:
    return topic_idea_repository.list_topic_ideas()


@router.post(
    "/topic-ideas",
    responses={200: {"content": {"text/event-stream": {}}}},
)
def create_topic_ideas(payload: TopicIdeaGenerateRequest) -> StreamingResponse:
    return StreamingResponse(topic_idea_service.stream_topic_idea_events(payload), media_type="text/event-stream")


@router.get("/generations/{generation_id}", response_model=AIGenerationRecord)
def get_ai_generation(generation_id: str) -> AIGenerationRecord:
    generation = topic_idea_repository.get_generation(generation_id)
    if generation is None:
        raise HTTPException(status_code=404, detail="AI generation not found")
    return AIGenerationRecord(**generation)


@router.get("/evidence", response_model=List[EvidenceItem])
def list_evidence(
    generation_id: Optional[str] = Query(default=None, alias="generationId"),
    workspace_id: Optional[str] = Query(default=None, alias="workspaceId"),
    account_id: Optional[str] = Query(default=None, alias="accountId"),
    platform: Optional[Platform] = None,
    direction: Optional[str] = None,
    limit: int = Query(default=20, ge=1, le=100),
) -> List[EvidenceItem]:
    try:
        items = ai_evidence_service.list_evidence(
            generation_id=generation_id,
            workspace_id=workspace_id,
            account_id=account_id,
            platform=platform,
            direction=direction,
            limit=limit,
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    if items is None:
        raise HTTPException(status_code=404, detail="AI generation not found")
    return items


@router.post("/{workflow}", response_model=AgentTask)
def create_ai_task(workflow: str, payload: Dict[str, Any]) -> AgentTask:
    return repository.create_task(workflow, payload)
