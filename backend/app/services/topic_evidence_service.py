from __future__ import annotations

from typing import Any, Dict, List

from app.repositories.memory_store import InMemoryRepository, repository
from app.repositories.topic_evidence_repository import TopicEvidenceRepository, topic_evidence_repository
from app.schemas.agent import MemorySearchRequest
from app.schemas.common import TopicIdeaGenerateRequest
from app.services.memory_record_service import memory_vector_service


class TopicEvidenceService:
    def __init__(self, content_repository: InMemoryRepository, evidence_repository: TopicEvidenceRepository) -> None:
        self.content_repository = content_repository
        self.evidence_repository = evidence_repository
        self.data_source_mode = "memory_fallback"

    def load_workspace_context(self, request: TopicIdeaGenerateRequest) -> Dict[str, Any]:
        workspace = self.content_repository.workspace
        return {
            "workspaceId": request.workspace_id,
            "workspaceName": workspace.workspace_name,
            "accountName": workspace.account_name,
            "platformScope": [platform.value for platform in workspace.platform_scope],
        }

    def load_content_metrics(self, request: TopicIdeaGenerateRequest) -> List[Dict[str, Any]]:
        postgres_metrics = self.evidence_repository.load_content_metrics(request)
        if postgres_metrics:
            self.data_source_mode = "postgres"
            return postgres_metrics

        self.data_source_mode = "memory_fallback"
        platform_values = {platform.value for platform in request.platforms}
        contents = [
            content
            for content in self.content_repository.contents
            if not platform_values or content.platform.value in platform_values
        ]
        return [
            {
                "id": content.id,
                "contentId": content.id,
                "sourceType": "memory_content",
                "sourceId": content.id,
                "title": content.title,
                "platform": content.platform.value,
                "publishedAt": content.published_at,
                "durationSeconds": content.duration_seconds,
                "views": content.views,
                "likes": content.likes,
                "comments": content.comments,
                "saves": content.saves,
                "shares": content.shares,
                "completionRate": content.completion_rate,
                "followersGained": content.followers_gained,
                "score": content.score,
                "status": content.status.value,
                "hasAsr": content.has_asr,
                "reviewed": content.reviewed,
            }
            for content in sorted(contents, key=lambda item: item.score or 0, reverse=True)[:8]
        ]

    def retrieve_topic_memories(self, request: TopicIdeaGenerateRequest) -> List[Dict[str, Any]]:
        search_request = self._memory_search_request(request)
        try:
            milvus_hits = memory_vector_service.search_milvus_hits(search_request)
        except Exception:
            milvus_hits = []
        if milvus_hits:
            postgres_evidence = self.evidence_repository.load_memory_evidence_by_ids(milvus_hits)
            if postgres_evidence:
                self.data_source_mode = "milvus"
                return postgres_evidence

            memory_evidence = memory_vector_service.hydrate_memory_hits(milvus_hits)
            if memory_evidence:
                self.data_source_mode = "milvus"
                return [
                    {
                        **item.model_dump(by_alias=True),
                        "id": item.memory_id,
                        "sourceType": "milvus_memory",
                        "sourceId": item.memory_id,
                    }
                    for item in memory_evidence
                ]

        postgres_memories = self.evidence_repository.retrieve_topic_memories(request)
        if postgres_memories:
            self.data_source_mode = "postgres"
            return postgres_memories

        self.data_source_mode = "memory_fallback"
        return [
            {
                **item.model_dump(by_alias=True),
                "id": item.memory_id,
                "sourceType": "memory_record",
                "sourceId": item.memory_id,
            }
            for item in memory_vector_service.search(search_request)
        ]

    def _memory_search_request(self, request: TopicIdeaGenerateRequest) -> MemorySearchRequest:
        account_id = request.account_ids[0]
        platform = request.platforms[0].value if request.platforms else "douyin"
        return MemorySearchRequest(
            query=f"{request.direction} {request.goal} 选题 搜索 完播 涨粉",
            workspace_id=request.workspace_id,
            account_id=account_id,
            platform=platform,
            memory_types=["content_case", "persona_profile", "search_intent", "success_pattern", "failure_pattern"],
            status="active",
            top_k=8,
        )


topic_evidence_service = TopicEvidenceService(repository, topic_evidence_repository)
