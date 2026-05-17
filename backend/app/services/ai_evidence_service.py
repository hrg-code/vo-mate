from __future__ import annotations

from typing import Any, Dict, List, Optional

from app.repositories.topic_evidence_repository import TopicEvidenceRepository, topic_evidence_repository
from app.repositories.topic_idea_repository import TopicIdeaRepository, topic_idea_repository
from app.schemas.common import EvidenceItem, Platform, TopicIdeaGenerateRequest
from app.services.topic_evidence_service import TopicEvidenceService, topic_evidence_service


DEFAULT_WORKSPACE_ID = "ws_northstar"
DEFAULT_ACCOUNT_ID = "douyin_demo"
DEFAULT_PLATFORM = Platform.douyin
DEFAULT_DIRECTION = "程序员职业成长"


class AiEvidenceService:
    def __init__(
        self,
        topic_repository: TopicIdeaRepository,
        evidence_repository: TopicEvidenceRepository,
        evidence_service: TopicEvidenceService,
    ) -> None:
        self.topic_repository = topic_repository
        self.evidence_repository = evidence_repository
        self.evidence_service = evidence_service

    def list_evidence(
        self,
        *,
        generation_id: Optional[str] = None,
        workspace_id: Optional[str] = None,
        account_id: Optional[str] = None,
        platform: Optional[Platform] = None,
        direction: Optional[str] = None,
        limit: int = 20,
    ) -> Optional[List[EvidenceItem]]:
        if generation_id:
            generation = self.topic_repository.get_generation(generation_id)
            if generation is None:
                return None
            return self._generation_evidence(generation, limit)

        normalized_direction = (direction or DEFAULT_DIRECTION).strip() or DEFAULT_DIRECTION
        request = TopicIdeaGenerateRequest(
            workspaceId=workspace_id or DEFAULT_WORKSPACE_ID,
            accountIds=[account_id or DEFAULT_ACCOUNT_ID],
            direction=normalized_direction,
            platforms=[platform or DEFAULT_PLATFORM],
            count=min(max(limit, 1), 20),
            includeEvidence=True,
        )
        items = self._postgres_preview_evidence(request, limit)
        if not items:
            raise RuntimeError("PostgreSQL evidence is empty")
        return items

    def _generation_evidence(self, generation: Dict[str, Any], limit: int) -> List[EvidenceItem]:
        items: List[EvidenceItem] = []
        output_payload = generation.get("outputPayload") or generation.get("output_payload") or {}
        topic_ideas = output_payload.get("topicIdeas") or []
        for idea in topic_ideas:
            if not isinstance(idea, dict):
                continue
            for evidence in idea.get("evidence") or []:
                if isinstance(evidence, dict):
                    items.append(self._memory_item(evidence, source_override=evidence.get("sourceType")))

        input_payload = generation.get("inputPayload") or generation.get("input_payload") or {}
        topic_idea_id = input_payload.get("topicIdeaId") or input_payload.get("topic_idea_id")
        if topic_idea_id:
            topic_idea = self.topic_repository.get_topic_idea(str(topic_idea_id))
            if topic_idea is not None:
                for evidence in topic_idea.evidence:
                    if isinstance(evidence, dict):
                        items.append(self._memory_item(evidence, source_override=evidence.get("sourceType")))

        if not items:
            evidence_ids = generation.get("evidenceIds") or generation.get("evidence_ids") or []
            hits = [(str(evidence_id), 1.0) for evidence_id in evidence_ids if evidence_id]
            memory_evidence = self.evidence_repository.load_memory_evidence_by_ids(hits)
            if memory_evidence:
                items.extend(self._memory_item(item, source_override=item.get("sourceType")) for item in memory_evidence)

        diagnostics = input_payload.get("contentRetrievalDiagnostics") or {}
        if diagnostics:
            items.append(self._diagnostic_item(generation, diagnostics))

        return self._dedupe(items)[:limit]

    def _postgres_preview_evidence(self, request: TopicIdeaGenerateRequest, limit: int) -> List[EvidenceItem]:
        items: List[EvidenceItem] = []
        content_evidence = self.evidence_service.load_topic_content_evidence(request)
        items.extend(self._content_items(content_evidence.get("relatedContents", []), "content", "当前方向相关历史内容"))
        items.extend(self._content_items(content_evidence.get("topPerformers", []), "metric", "账号高表现参考"))
        items.extend(self._content_items(content_evidence.get("contrastContents", []), "constraint", "避坑反例"))
        diagnostics = content_evidence.get("retrievalDiagnostics")
        if diagnostics:
            items.append(self._diagnostic_item({"id": "preview"}, diagnostics))

        memories = self.evidence_service.retrieve_topic_memories(request)
        items.extend(self._memory_item(item, source_override=item.get("sourceType")) for item in memories or [])
        return self._dedupe(items)[:limit]

    def _content_items(self, rows: List[Dict[str, Any]], item_type: str, action: str) -> List[EvidenceItem]:
        return [self._content_item(row, item_type, action) for row in rows if isinstance(row, dict)]

    def _content_item(self, row: Dict[str, Any], item_type: str, action: str) -> EvidenceItem:
        metrics = []
        for label, key in [
            ("播放", "views"),
            ("点赞", "likes"),
            ("评论", "comments"),
            ("收藏", "saves"),
            ("分享", "shares"),
            ("涨粉", "followersGained"),
        ]:
            value = row.get(key)
            if isinstance(value, (int, float)) and value:
                metrics.append(f"{label} {round(value, 2)}")
        completion_rate = row.get("completionRate")
        if isinstance(completion_rate, (int, float)):
            metrics.append(f"完播率 {round(completion_rate * 100)}%")
        return EvidenceItem(
            id=str(row.get("contentId") or row.get("id") or "content_evidence"),
            type=item_type,
            title=str(row.get("title") or "历史内容证据"),
            description=str(row.get("reason") or row.get("description") or "来自 PostgreSQL 内容证据池。"),
            source=str(row.get("sourceType") or row.get("retrievalSource") or "postgres_content"),
            score=self._int_score(row.get("score") or row.get("relevanceScore")),
            metrics=metrics,
            action=action,
        )

    def _memory_item(self, row: Dict[str, Any], source_override: Any = None) -> EvidenceItem:
        return EvidenceItem(
            id=str(row.get("memoryId") or row.get("id") or row.get("sourceId") or "memory_evidence"),
            type="memory",
            title=str(row.get("title") or "长期记忆证据"),
            description=str(row.get("summary") or row.get("reason") or "来自 PostgreSQL 长期记忆。"),
            source=str(source_override or row.get("sourceType") or "postgres_memory"),
            score=self._int_score(row.get("score")),
            metrics=[str(row.get("reason"))] if row.get("reason") else [],
            action="用于解释选题角度、风险和推荐理由",
        )

    def _diagnostic_item(self, generation: Dict[str, Any], diagnostics: Dict[str, Any]) -> EvidenceItem:
        metrics = []
        for label, key in [
            ("候选", "candidateCount"),
            ("相关", "relatedCount"),
            ("高表现", "topPerformerCount"),
            ("反例", "contrastCount"),
            ("记忆", "evidenceCount"),
        ]:
            value = diagnostics.get(key)
            if isinstance(value, (int, float)):
                metrics.append(f"{label} {round(value)}")
        return EvidenceItem(
            id=f"{generation.get('id', 'preview')}_retrieval_diagnostics",
            type="raw",
            title="证据召回诊断",
            description=f"数据源 {diagnostics.get('dataSourceMode') or diagnostics.get('strategy') or 'postgres'}，策略 {diagnostics.get('strategy') or 'default'}。",
            source="retrievalDiagnostics",
            score=None,
            metrics=metrics,
            action="用于说明本次依据来自哪些召回池",
        )

    def _dedupe(self, items: List[EvidenceItem]) -> List[EvidenceItem]:
        seen = set()
        deduped: List[EvidenceItem] = []
        for item in items:
            key = (item.type, item.id, item.source)
            if key in seen:
                continue
            seen.add(key)
            deduped.append(item)
        return deduped

    def _int_score(self, value: Any) -> Optional[int]:
        if isinstance(value, (int, float)):
            score = float(value)
            if 0 <= score <= 1:
                score *= 100
            return round(max(0, min(100, score)))
        return None


ai_evidence_service = AiEvidenceService(topic_idea_repository, topic_evidence_repository, topic_evidence_service)
