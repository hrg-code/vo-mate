from __future__ import annotations

from typing import Any, Dict, List, Optional

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.models import AIGeneration as AIGenerationModel
from app.db.models import TopicIdea as TopicIdeaModel
from app.db.session import get_admin_engine
from app.repositories.memory_store import InMemoryRepository, repository
from app.schemas.common import Platform, TopicIdea


class TopicIdeaRepository:
    def __init__(self, topic_repository: InMemoryRepository) -> None:
        self.topic_repository = topic_repository
        self.memory_generations: Dict[str, Dict[str, Any]] = {}

    def list_topic_ideas(self) -> List[TopicIdea]:
        with self._session() as session:
            if session is not None:
                try:
                    rows = session.query(TopicIdeaModel).order_by(TopicIdeaModel.created_at.desc()).limit(100).all()
                    return [self._from_model(row) for row in rows]
                except SQLAlchemyError:
                    session.rollback()
        return self.topic_repository.topic_ideas

    def save_generated_ideas(self, ideas: List[TopicIdea], source_payload: Optional[Dict[str, Any]] = None) -> List[TopicIdea]:
        with self._session() as session:
            if session is not None:
                try:
                    for idea in ideas:
                        session.merge(self._to_model(idea, source_payload or {}))
                    session.commit()
                    return ideas
                except SQLAlchemyError:
                    session.rollback()

        existing_by_id = {idea.id: idea for idea in self.topic_repository.topic_ideas}
        for idea in ideas:
            existing_by_id[idea.id] = idea
        self.topic_repository.topic_ideas = list(existing_by_id.values())
        return ideas

    def record_generation_started(
        self,
        generation_id: str,
        workspace_id: str,
        provider: str,
        model: Optional[str],
        prompt_version: str,
        input_payload: Dict[str, Any],
    ) -> None:
        record = {
            "id": generation_id,
            "workspaceId": workspace_id,
            "workflow": "topic-ideas",
            "provider": provider,
            "model": model,
            "promptVersion": prompt_version,
            "inputPayload": input_payload,
            "evidenceIds": [],
            "outputPayload": None,
            "error": None,
            "status": "running",
        }
        with self._session() as session:
            if session is not None:
                try:
                    session.merge(self._generation_model(record))
                    session.commit()
                    return
                except SQLAlchemyError:
                    session.rollback()
        self.memory_generations[generation_id] = record

    def record_generation_succeeded(self, generation_id: str, evidence_ids: List[str], output_payload: Dict[str, Any]) -> None:
        self._finish_generation(
            generation_id=generation_id,
            status="succeeded",
            evidence_ids=evidence_ids,
            output_payload=output_payload,
            error=None,
        )

    def update_generation_input(self, generation_id: str, input_payload: Dict[str, Any]) -> None:
        with self._session() as session:
            if session is not None:
                try:
                    row = session.get(AIGenerationModel, generation_id)
                    if row is not None:
                        row.input_payload = input_payload
                        session.commit()
                        return
                except SQLAlchemyError:
                    session.rollback()

        record = self.memory_generations.get(generation_id)
        if record is not None:
            record["inputPayload"] = input_payload

    def record_generation_failed(self, generation_id: str, error: str) -> None:
        self._finish_generation(
            generation_id=generation_id,
            status="failed",
            evidence_ids=[],
            output_payload=None,
            error=error,
        )

    def get_generation(self, generation_id: str) -> Optional[Dict[str, Any]]:
        with self._session() as session:
            if session is not None:
                try:
                    row = session.get(AIGenerationModel, generation_id)
                    return self._generation_dict(row) if row is not None else None
                except SQLAlchemyError:
                    session.rollback()
        return self.memory_generations.get(generation_id)

    def _finish_generation(
        self,
        generation_id: str,
        status: str,
        evidence_ids: List[str],
        output_payload: Optional[Dict[str, Any]],
        error: Optional[str],
    ) -> None:
        with self._session() as session:
            if session is not None:
                try:
                    row = session.get(AIGenerationModel, generation_id)
                    if row is not None:
                        row.status = status
                        row.evidence_ids = evidence_ids
                        row.output_payload = output_payload
                        row.error = error
                        session.commit()
                        return
                except SQLAlchemyError:
                    session.rollback()

        record = self.memory_generations.get(generation_id)
        if record is not None:
            record.update(
                {
                    "status": status,
                    "evidenceIds": evidence_ids,
                    "outputPayload": output_payload,
                    "error": error,
                }
            )

    def _session(self):
        return _OptionalSession()

    def _from_model(self, row: TopicIdeaModel) -> TopicIdea:
        platforms = row.platforms or []
        return TopicIdea(
            id=row.id,
            title=row.title,
            topic=row.topic,
            angle=row.angle or "",
            category=row.category,
            target_audience=row.target_audience,
            predicted_score=round(row.predicted_score or 0),
            seo_score=round(row.seo_score or 0),
            audience_score=round(row.audience_score or 0),
            difficulty_score=round(row.difficulty_score or 0),
            risk=row.risk or "",
            recommend_reason=row.recommend_reason,
            evidence_count=len(row.evidence or []),
            target_platforms=[Platform(platform) for platform in platforms if platform in Platform._value2member_map_],
            evidence=row.evidence or [],
            suggested_titles=row.suggested_titles or [],
            suggested_hooks=row.suggested_hooks or [],
            suggested_tags=row.suggested_tags or [],
            next_actions=row.next_actions or [],
            generation_id=row.generation_id,
        )

    def _to_model(self, idea: TopicIdea, source_payload: Dict[str, Any]) -> TopicIdeaModel:
        return TopicIdeaModel(
            id=idea.id,
            workspace_id=source_payload.get("workspaceId") or source_payload.get("workspace_id") or "ws_northstar",
            title=idea.title,
            topic=idea.topic,
            angle=idea.angle,
            category=idea.category,
            target_audience=idea.target_audience,
            platforms=[platform.value for platform in idea.target_platforms],
            predicted_score=idea.predicted_score,
            seo_score=idea.seo_score,
            audience_score=idea.audience_score,
            difficulty_score=idea.difficulty_score,
            risk=idea.risk,
            recommend_reason=idea.recommend_reason,
            evidence=idea.evidence,
            suggested_titles=idea.suggested_titles,
            suggested_hooks=idea.suggested_hooks,
            suggested_tags=idea.suggested_tags,
            next_actions=idea.next_actions,
            generation_id=idea.generation_id,
            source_payload=source_payload,
            status="idea",
        )

    def _generation_model(self, record: Dict[str, Any]) -> AIGenerationModel:
        return AIGenerationModel(
            id=record["id"],
            workspace_id=record["workspaceId"],
            workflow=record["workflow"],
            provider=record["provider"],
            model=record["model"],
            prompt_version=record["promptVersion"],
            input_payload=record["inputPayload"],
            evidence_ids=record["evidenceIds"],
            output_payload=record["outputPayload"],
            error=record["error"],
            status=record["status"],
        )

    def _generation_dict(self, row: AIGenerationModel) -> Dict[str, Any]:
        return {
            "id": row.id,
            "workspaceId": row.workspace_id,
            "workflow": row.workflow,
            "provider": row.provider,
            "model": row.model,
            "promptVersion": row.prompt_version,
            "inputPayload": row.input_payload,
            "evidenceIds": row.evidence_ids,
            "outputPayload": row.output_payload,
            "error": row.error,
            "status": row.status,
        }


class _OptionalSession:
    def __enter__(self) -> Optional[Session]:
        self.session: Optional[Session] = None
        if not get_settings().postgres_host:
            return None
        engine = get_admin_engine()
        if engine is None:
            return None
        self.session = Session(engine)
        return self.session

    def __exit__(self, exc_type, exc, traceback) -> None:
        if self.session is None:
            return
        if exc_type is not None or isinstance(exc, SQLAlchemyError):
            self.session.rollback()
        self.session.close()


topic_idea_repository = TopicIdeaRepository(repository)
