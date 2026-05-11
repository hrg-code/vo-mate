from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import desc, func, or_
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.models import AgentMemoryRecord, ContentItem
from app.db.session import get_admin_engine
from app.schemas.common import TopicIdeaGenerateRequest


class TopicEvidenceRepository:
    def load_content_metrics(self, request: TopicIdeaGenerateRequest, limit: int = 8) -> Optional[List[Dict[str, Any]]]:
        with self._session() as session:
            if session is None:
                return None
            try:
                platforms = [platform.value for platform in request.platforms]
                query = session.query(ContentItem).filter(ContentItem.workspace_id == request.workspace_id)
                if platforms:
                    query = query.filter(ContentItem.platform.in_(platforms))
                rows = (
                    query.order_by(
                        desc(func.coalesce(ContentItem.score, 0)),
                        desc(ContentItem.views),
                        desc(ContentItem.published_at),
                    )
                    .limit(limit)
                    .all()
                )
                return [self._content_metric(row) for row in rows]
            except SQLAlchemyError:
                session.rollback()
                return None

    def retrieve_topic_memories(self, request: TopicIdeaGenerateRequest, limit: int = 8) -> Optional[List[Dict[str, Any]]]:
        with self._session() as session:
            if session is None:
                return None
            try:
                account_id = request.account_ids[0]
                platform = request.platforms[0].value if request.platforms else "douyin"
                memory_types = ["content_case", "persona_profile", "search_intent", "success_pattern", "failure_pattern"]
                terms = self._query_terms(request.direction)
                query = session.query(AgentMemoryRecord).filter(
                    AgentMemoryRecord.workspace_id == request.workspace_id,
                    AgentMemoryRecord.account_id == account_id,
                    AgentMemoryRecord.platform == platform,
                    AgentMemoryRecord.status == "active",
                    AgentMemoryRecord.memory_type.in_(memory_types),
                )
                if terms:
                    query = query.filter(
                        or_(
                            *[
                                or_(
                                    AgentMemoryRecord.title.ilike(f"%{term}%"),
                                    AgentMemoryRecord.summary.ilike(f"%{term}%"),
                                    AgentMemoryRecord.content.ilike(f"%{term}%"),
                                )
                                for term in terms
                            ]
                        )
                    )
                rows = query.limit(50).all()
                scored = [(self._memory_score(row, terms), row) for row in rows]
                scored.sort(key=lambda item: item[0], reverse=True)
                return [self._memory_evidence(row, score) for score, row in scored[:limit]]
            except SQLAlchemyError:
                session.rollback()
                return None

    def load_memory_evidence_by_ids(self, hits: List[Tuple[str, float]]) -> Optional[List[Dict[str, Any]]]:
        if not hits:
            return []
        with self._session() as session:
            if session is None:
                return None
            try:
                ids = [memory_id for memory_id, _score in hits]
                scores = {memory_id: score for memory_id, score in hits}
                rows = session.query(AgentMemoryRecord).filter(AgentMemoryRecord.id.in_(ids)).all()
                rows_by_id = {row.id: row for row in rows}
                return [
                    self._memory_evidence(rows_by_id[memory_id], scores[memory_id], source_type="milvus_memory")
                    for memory_id in ids
                    if memory_id in rows_by_id
                ]
            except SQLAlchemyError:
                session.rollback()
                return None

    def _session(self):
        return _OptionalSession()

    def _content_metric(self, row: ContentItem) -> Dict[str, Any]:
        return {
            "id": row.id,
            "contentId": row.id,
            "sourceType": "postgres_content",
            "sourceId": row.id,
            "title": row.title,
            "platform": row.platform,
            "publishedAt": row.published_at.isoformat() if row.published_at else None,
            "durationSeconds": row.duration_seconds,
            "views": row.views,
            "likes": row.likes,
            "comments": row.comments,
            "saves": row.saves,
            "shares": row.shares,
            "completionRate": row.completion_rate,
            "followersGained": row.followers_gained,
            "score": row.score,
            "status": row.status,
            "hasAsr": row.has_asr,
            "reviewed": row.reviewed,
        }

    def _memory_evidence(self, row: AgentMemoryRecord, score: float, source_type: str = "postgres_memory") -> Dict[str, Any]:
        return {
            "id": row.id,
            "memoryId": row.id,
            "sourceType": source_type,
            "sourceId": row.id,
            "memoryType": row.memory_type,
            "title": row.title,
            "summary": row.summary,
            "score": round(score, 4),
            "reason": f"命中 {row.memory_type} 记忆，置信度 {row.confidence:.2f}，证据 {row.evidence_count} 条",
        }

    def _memory_score(self, row: AgentMemoryRecord, terms: List[str]) -> float:
        haystack = f"{row.title} {row.summary} {row.content}"
        overlap = sum(1 for term in terms if term in haystack)
        return min(0.99, 0.55 + overlap * 0.08 + row.confidence * 0.2 + min(row.evidence_count, 5) * 0.02)

    def _query_terms(self, direction: str) -> List[str]:
        return [term for term in direction.replace("，", " ").replace("、", " ").split() if term]


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
        if exc_type is not None:
            self.session.rollback()
        self.session.close()


topic_evidence_repository = TopicEvidenceRepository()
