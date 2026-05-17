from __future__ import annotations

from typing import Any, Dict, List

from app.core.config import get_settings
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
        postgres_context = self.evidence_repository.load_workspace_context(request)
        if postgres_context is not None:
            if request.account_ids and not postgres_context.get("accountName"):
                raise RuntimeError("PostgreSQL workspace/account context is required for topic idea generation")
            return postgres_context

        raise RuntimeError("PostgreSQL workspace/account context is required for topic idea generation")

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

    def load_topic_content_evidence(self, request: TopicIdeaGenerateRequest) -> Dict[str, Any]:
        # 下面是把前面筛出来的候选内容，整理成最终返回给选题生成模型的“三层证据包”。
        '''
            {
                "relatedContents": related_contents, # 当前方向相关的正向参考
                "topPerformers": top_performers,   # 账号历史高表现风格参考
                "contrastContents": contrast_contents, # 当前方向相关但表现较弱的避坑反例
                "retrievalDiagnostics": diagnostics,  # 本次召回和过滤过程的调试信息
            }
        '''
        postgres_evidence = self.evidence_repository.load_topic_content_evidence(request)
        if postgres_evidence is not None:
            self.data_source_mode = "postgres"
            diagnostics = postgres_evidence.get("retrievalDiagnostics", {})
            if diagnostics.get("accountFilterFallback"):
                raise RuntimeError("PostgreSQL account-scoped content evidence is required for topic idea generation")
            if not diagnostics.get("candidateCount") and not postgres_evidence.get("topPerformers"):
                raise RuntimeError("PostgreSQL topic content evidence is empty")
            return postgres_evidence

        self.data_source_mode = "postgres_no_vector"
        raise RuntimeError("PostgreSQL topic content evidence is required for topic idea generation")

    def retrieve_topic_memories(self, request: TopicIdeaGenerateRequest) -> List[Dict[str, Any]]:
        search_request = self._memory_search_request(request)
        milvus_hits = []
        # 是否开启向量库
        if self._real_vector_enabled():
            try:
                # 查询的视频内容向量
                milvus_hits = memory_vector_service.search_milvus_hits(search_request)
            except Exception:
                milvus_hits = []
        if milvus_hits:
            postgres_evidence = self.evidence_repository.load_memory_evidence_by_ids(milvus_hits)
            if postgres_evidence:
                self.data_source_mode = "milvus"
                return postgres_evidence

        postgres_memories = self.evidence_repository.retrieve_topic_memories(request)
        if postgres_memories:
            self.data_source_mode = "postgres" if milvus_hits else "postgres_no_vector"
            return postgres_memories

        self.data_source_mode = "postgres_no_vector"
        raise RuntimeError("PostgreSQL agent_memory_records evidence is required for topic idea generation")

    def _real_vector_enabled(self) -> bool:
        settings = get_settings()
        return bool(
            settings.milvus_host
            and settings.embedding_provider == "dashscope"
            and settings.dashscope_api_key
        )

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

    def _memory_content_metric(self, content: Any, reference_type: str) -> Dict[str, Any]:
        return {
            "id": content.id,
            "contentId": content.id,
            "sourceType": "memory_content",
            "sourceId": content.id,
            "title": content.title,
            "description": None,
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
            "tags": [],
            "keywords": [],
            "textAssets": [],
            "referenceType": reference_type,
        }

    def _memory_content_relevance(self, item: Dict[str, Any], terms: List[str]) -> Dict[str, Any]:
        matched_terms = [term for term in terms if term.lower() in (item.get("title") or "").lower()]
        if len(matched_terms) >= 2:
            level = "strong_related"
        elif matched_terms:
            level = "medium_related"
        else:
            level = "unrelated"
        score_by_level = {"strong_related": 0.9, "medium_related": 0.74, "unrelated": 0.0}
        return {
            "relevanceLevel": level,
            "relevanceScore": round(min(score_by_level[level] + min(len(matched_terms), 4) * 0.02, 0.99), 4),
            "matchedTerms": matched_terms,
            "matchFields": ["title"] if matched_terms else [],
            "reason": f"命中当前方向相关词：{', '.join(matched_terms)}" if matched_terms else "未命中当前方向相关词。",
        }

    def _query_terms(self, direction: str) -> List[str]:
        normalized = direction
        for char in ["，", "、", ",", "/", "|", "：", ":", "；", ";", "（", "）", "(", ")"]:
            normalized = normalized.replace(char, " ")
        terms = [term.strip() for term in normalized.split() if len(term.strip()) >= 2]
        compact_direction = direction.strip()
        if len(compact_direction) >= 2:
            terms.append(compact_direction)
        domain_terms = [
            "程序员",
            "副业",
            "接私活",
            "独立产品",
            "变现",
            "职业",
            "成长",
            "转型",
            "简历",
            "外包",
            "AI",
            "人工智能",
            "搜索",
            "完播",
            "涨粉",
        ]
        terms.extend(term for term in domain_terms if term.lower() in compact_direction.lower())
        deduped: List[str] = []
        for term in terms:
            if term not in deduped:
                deduped.append(term)
        return deduped


topic_evidence_service = TopicEvidenceService(repository, topic_evidence_repository)
