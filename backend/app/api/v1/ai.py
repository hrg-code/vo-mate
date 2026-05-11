from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException
from starlette.responses import StreamingResponse

from app.repositories.memory_store import repository
from app.repositories.topic_idea_repository import topic_idea_repository
from app.schemas.common import AgentTask, AIGenerationRecord, EvidenceItem, TopicIdea, TopicIdeaGenerateRequest
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
def list_evidence() -> List[EvidenceItem]:
    return repository.evidence


@router.post("/{workflow}", response_model=AgentTask)
def create_ai_task(workflow: str, payload: Dict[str, Any]) -> AgentTask:
    return repository.create_task(workflow, payload)
