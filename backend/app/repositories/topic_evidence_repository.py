from __future__ import annotations

import json
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import desc, func, or_
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.models import AgentMemoryRecord, ContentItem, ContentKeyword, ContentLifetimeMetric, ContentTag, ContentTextAsset, PlatformAccount, Workspace
from app.db.session import get_admin_engine
from app.schemas.common import TopicIdeaGenerateRequest
from app.services.content_vector_service import CREATOR_CONTENT_VECTOR_COLLECTION, content_vector_service
from app.services.topic_content_rerank_service import topic_content_rerank_service


class TopicEvidenceRepository:
    def load_workspace_context(self, request: TopicIdeaGenerateRequest) -> Optional[Dict[str, Any]]:
        with self._session() as session:
            if session is None:
                return None
            try:
                workspace = session.get(Workspace, request.workspace_id)
                if workspace is None:
                    return None

                platforms = [platform.value for platform in request.platforms]
                account_query = session.query(PlatformAccount).filter(
                    PlatformAccount.workspace_id == request.workspace_id,
                    PlatformAccount.status == "active",
                )
                if request.account_ids:
                    account_query = account_query.filter(PlatformAccount.id.in_(request.account_ids))
                if platforms:
                    account_query = account_query.filter(PlatformAccount.platform.in_(platforms))
                accounts = account_query.order_by(PlatformAccount.created_at.desc()).all()

                account_name = accounts[0].account_name if accounts else ""
                platform_scope = [account.platform for account in accounts if account.platform]
                if not platform_scope:
                    platform_scope = platforms

                return {
                    "workspaceId": workspace.id,
                    "workspaceName": workspace.name,
                    "accountName": account_name,
                    "platformScope": platform_scope,
                    "workspaceContextSource": "postgres",
                }
            except SQLAlchemyError:
                session.rollback()
                return None

    def load_content_metrics(self, request: TopicIdeaGenerateRequest, limit: int = 8) -> Optional[List[Dict[str, Any]]]:
        with self._session() as session:
            if session is None:
                return None
            try:
                rows = self._content_rows(session, request, limit=limit)
                enrichment = self._load_enrichment_summary(session, [content.id for content, _metric in rows])
                return [
                    {
                        **self._content_metric(content, metric, enrichment.get(content.id)),
                        "referenceType": "style_reference",
                    }
                    for content, metric in rows
                ]
            except SQLAlchemyError:
                session.rollback()
                return None

    def load_topic_content_evidence(
        self,
        request: TopicIdeaGenerateRequest,
        related_limit: int = 8,
        top_limit: int = 8,
        contrast_limit: int = 3,
    ) -> Optional[Dict[str, Any]]:
        with self._session() as session:
            if session is None:
                return None
            try:
                terms = self._query_terms(request.direction)
                # 根据平台 获取【抖音】库里面的真实video数据 根据播放量 什么相关的 workspace account 等取出来
                # 这里还是有非常大的问题 感觉相关性非常差 仅仅考score评分 和一个 播放量等，这个取内容有很大的问题
                keyword_rows = self._content_rows(session, request, limit=80)
                # 获得条数
                account_filtered_candidate_count = len(keyword_rows)
                # 如果用户传了账号过滤条件 account_ids，但是按关键词没查到结果 keyword_rows，那就启用账号兜底查询。
                # 未发现使用的关键词 查询
                account_filter_fallback = bool(request.account_ids) and not keyword_rows
                null_account_candidate_count = 0
                account_filter_mode = "requested"
                # 兜底账号查询
                if account_filter_fallback:
                    keyword_rows = self._content_rows(session, request, limit=80, account_filter_mode="null")
                    null_account_candidate_count = len(keyword_rows)
                    account_filter_mode = "null"
                keyword_ids = {content.id for content, _metric in keyword_rows}
                # 拼接向量查询条件
                # 程序员 35 岁危机 followers 25-35 岁普通程序员 {"avoidTopics": ["裁员恐慌"], "targetDurationSeconds": 60, "tone": "克制直接", "useHotSignals": true}
                embedding_query = self._embedding_query(request)
                # 目前 embedding里面完全没有数据
                embedding_hits = (
                    # 查询 creator_content_vectors
                    content_vector_service.search_content_hits(request, embedding_query, top_k=24)
                    # 只有真实向量配置齐全才能通
                    # 判断条件 settings.milvus_host settings.embedding_provider == "dashscope" settings.dashscope_api_key
                    if self._real_vector_enabled()
                    else []
                )
                # 获取评分
                embedding_scores = {content_id: score for content_id, score, _vector_id in embedding_hits}
                # 获取内容ids
                embedding_vector_ids = {content_id: vector_id for content_id, _score, vector_id in embedding_hits}
                # 根据ids 去db获取视频内容
                embedding_rows = self._content_rows_by_ids(
                    session,
                    request,
                    [content_id for content_id, _score, _vector_id in embedding_hits],
                    account_filter_mode=account_filter_mode,
                )

                ###################以上就是数据库查询video视频和Mivus查询视频######################

                # 创建空字典
                candidate_by_id: Dict[str, Tuple[ContentItem, Optional[ContentLifetimeMetric]]] = {}
                # 两路召回，合并去重
                for content, metric in keyword_rows + embedding_rows:
                    candidate_by_id[content.id] = (content, metric)
                candidate_rows = list(candidate_by_id.values())
                content_ids = list(candidate_by_id.keys())
                # 查 ContentTag 和 ContentKeyword，返回每条内容的标签和关键词。
                enrichment = self._load_enrichment_summary(session, content_ids)
                # 查 ContentTextAsset，返回每条内容最多 3 段文本素材，每段截断到 500 字
                text_assets = self._load_text_asset_summary(session, content_ids)

                # 建立字典
                related_candidates: List[Dict[str, Any]] = []
                weak_candidate_count = 0
                keyword_candidate_count = 0
                for content, metric in candidate_rows:
                    # 拼装信息 即格式化信息 供后面使用
                    item = self._content_metric(
                        content,
                        metric,
                        enrichment.get(content.id),
                        text_assets.get(content.id, []),
                    )

                    # 核心 判断当前这条内容 与 当前的选题方向有多相关 这个要着重分析下
                    relevance = self._content_relevance(item, terms)
                    # 判断“这条内容是从哪条召回路径来的
                    '''
                        hybrid：这条内容既在 PostgreSQL 候选池里，又命中了方向词，同时也被 Milvus 向量召回。
                        embedding：这条内容是向量召回来的，但关键词没明显命中。
                        keyword：这条内容是普通内容池里通过方向词命中的。
                        performance_pool：它在高表现候选池里，但没有关键词命中，也不是向量命中。
                    '''
                    source = self._retrieval_source(content.id, keyword_ids, embedding_scores, relevance)
                    if source in {"keyword", "hybrid"}:
                        keyword_candidate_count += 1
                    if content.id in embedding_scores:
                        item["embeddingScore"] = embedding_scores[content.id]
                        item["vectorId"] = embedding_vector_ids.get(content.id)
                    if relevance["relevanceLevel"] in {"strong_related", "medium_related"}:
                        related_candidates.append(
                            {
                                **item,
                                **relevance,
                                "referenceType": "topic_related",
                                "retrievalSource": source,
                            }
                        )
                    elif relevance["relevanceLevel"] == "weak_related":
                        weak_candidate_count += 1

                ###############################
                # 下面是把前面筛出来的候选内容，整理成最终返回给选题生成模型的“三层证据包”。
                '''
                    {
                        "relatedContents": related_contents, # 当前方向相关的正向参考
                        "topPerformers": top_performers,   # 账号历史高表现风格参考
                        "contrastContents": contrast_contents, # 当前方向相关但表现较弱的避坑反例
                        "retrievalDiagnostics": diagnostics,  # 本次召回和过滤过程的调试信息
                    }
                '''
                related_candidates.sort(
                    key=lambda item: (
                        item["relevanceScore"],
                        item.get("score") or 0,
                        item.get("views") or 0,
                        item.get("publishedAt") or "",
                    ),
                    reverse=True,
                )
                rerank_result = topic_content_rerank_service.rerank(request, related_candidates)
                reranked_candidates = rerank_result["candidates"]
                related_contents = reranked_candidates[:related_limit]

                top_rows = self._content_rows(session, request, limit=top_limit, account_filter_mode=account_filter_mode)
                top_enrichment = self._load_enrichment_summary(session, [content.id for content, _metric in top_rows])
                top_text_assets = self._load_text_asset_summary(session, [content.id for content, _metric in top_rows])
                top_performers = [
                    {
                        **self._content_metric(
                            content,
                            metric,
                            top_enrichment.get(content.id),
                            top_text_assets.get(content.id, []),
                        ),
                        "referenceType": "style_reference",
                        "reason": "同账号同平台历史高表现内容，仅用于学习账号表达结构。",
                    }
                    for content, metric in top_rows
                ]

                contrast_contents = [
                    {
                        **item,
                        "referenceType": "avoid_pattern",
                        "reason": "与当前方向相关但历史表现较弱，生成时应避开相似表达。",
                    }
                    for item in sorted(
                        reranked_candidates,
                        key=lambda item: (
                            item.get("score") if item.get("score") is not None else 0,
                            item.get("views") or 0,
                        ),
                    )[:contrast_limit]
                ]

                platforms = [platform.value for platform in request.platforms]
                diagnostics = {
                    "strategy": "hybrid_keyword_embedding_gate",
                    "dataSourceMode": "postgres",
                    "direction": request.direction,
                    "matchedTerms": terms,
                    "keywordCandidateCount": keyword_candidate_count,
                    "embeddingCandidateCount": len(embedding_hits),
                    "mergedCandidateCount": len(candidate_rows),
                    "candidateCount": len(candidate_rows),
                    "accountFilterFallback": account_filter_fallback,
                    "accountFilteredCandidateCount": account_filtered_candidate_count,
                    "nullAccountCandidateCount": null_account_candidate_count,
                    "relatedCandidateCount": len(related_candidates),
                    "weakCandidateCount": weak_candidate_count,
                    "relatedCount": len(related_contents),
                    "topPerformerCount": len(top_performers),
                    "contrastCount": len(contrast_contents),
                    "filteredBy": {
                        "workspaceId": request.workspace_id,
                        "accountIds": request.account_ids,
                        "platforms": platforms,
                        "status": "published",
                        "accountFilterMode": account_filter_mode,
                    },
                    "embeddingConfigured": self._real_vector_enabled(),
                    "embeddingCollection": CREATOR_CONTENT_VECTOR_COLLECTION,
                    **rerank_result["diagnostics"],
                }
                if content_vector_service.last_error:
                    diagnostics["embeddingError"] = content_vector_service.last_error
                return {
                    "relatedContents": related_contents,
                    "topPerformers": top_performers,
                    "contrastContents": contrast_contents,
                    "retrievalDiagnostics": diagnostics,
                }
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

    def list_account_memories(
        self,
        workspace_id: str,
        account_id: str,
        platform: str,
        limit: int = 8,
    ) -> Optional[List[Dict[str, Any]]]:
        with self._session() as session:
            if session is None:
                return None
            try:
                rows = (
                    session.query(AgentMemoryRecord)
                    .filter(
                        AgentMemoryRecord.workspace_id == workspace_id,
                        AgentMemoryRecord.account_id == account_id,
                        AgentMemoryRecord.platform == platform,
                        AgentMemoryRecord.status == "active",
                    )
                    .order_by(desc(AgentMemoryRecord.confidence), desc(AgentMemoryRecord.evidence_count))
                    .limit(limit)
                    .all()
                )
                return [self._memory_evidence(row, row.confidence) for row in rows]
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

    def _real_vector_enabled(self) -> bool:
        settings = get_settings()
        return bool(
            settings.milvus_host
            and settings.embedding_provider == "dashscope"
            and settings.dashscope_api_key
        )

    def _content_rows(
        self,
        session: Session,
        request: TopicIdeaGenerateRequest,
        limit: int,
        account_filter_mode: str = "requested",
    ) -> List[Tuple[ContentItem, Optional[ContentLifetimeMetric]]]:
        platforms = [platform.value for platform in request.platforms]
        query = session.query(ContentItem).filter(
            ContentItem.workspace_id == request.workspace_id,
            ContentItem.status == "published",
        )
        if account_filter_mode == "null":
            query = query.filter(ContentItem.platform_account_id.is_(None))
        elif request.account_ids:
            query = query.filter(ContentItem.platform_account_id.in_(request.account_ids))
        if platforms:
            query = query.filter(ContentItem.platform.in_(platforms))
        return (
            query.outerjoin(ContentLifetimeMetric, ContentLifetimeMetric.content_id == ContentItem.id)
            .with_entities(ContentItem, ContentLifetimeMetric)
            .order_by(
                desc(func.coalesce(ContentLifetimeMetric.metric_score, ContentItem.score, 0)),
                desc(func.coalesce(ContentLifetimeMetric.play_count, ContentItem.views, 0)),
                desc(ContentItem.published_at),
            )
            .limit(limit)
            .all()
        )

    def _content_rows_by_ids(
        self,
        session: Session,
        request: TopicIdeaGenerateRequest,
        content_ids: List[str],
        account_filter_mode: str = "requested",
    ) -> List[Tuple[ContentItem, Optional[ContentLifetimeMetric]]]:
        if not content_ids:
            return []
        platforms = [platform.value for platform in request.platforms]
        query = session.query(ContentItem).filter(
            ContentItem.id.in_(content_ids),
            ContentItem.workspace_id == request.workspace_id,
            ContentItem.status == "published",
        )
        if account_filter_mode == "null":
            query = query.filter(ContentItem.platform_account_id.is_(None))
        elif request.account_ids:
            query = query.filter(ContentItem.platform_account_id.in_(request.account_ids))
        if platforms:
            query = query.filter(ContentItem.platform.in_(platforms))
        return (
            query.outerjoin(ContentLifetimeMetric, ContentLifetimeMetric.content_id == ContentItem.id)
            .with_entities(ContentItem, ContentLifetimeMetric)
            .all()
        )

    def _load_enrichment_summary(self, session: Session, content_ids: List[str], limit: int = 5) -> Dict[str, Dict[str, List[str]]]:
        if not content_ids:
            return {}
        summary = {content_id: {"tags": [], "keywords": []} for content_id in content_ids}
        tags = session.query(ContentTag).filter(ContentTag.content_id.in_(content_ids)).all()
        keywords = session.query(ContentKeyword).filter(ContentKeyword.content_id.in_(content_ids)).order_by(desc(ContentKeyword.score)).all()
        for tag in tags:
            values = summary.setdefault(tag.content_id, {"tags": [], "keywords": []})["tags"]
            if tag.tag not in values and len(values) < limit:
                values.append(tag.tag)
        for keyword in keywords:
            values = summary.setdefault(keyword.content_id, {"tags": [], "keywords": []})["keywords"]
            if keyword.keyword not in values and len(values) < limit:
                values.append(keyword.keyword)
        return summary

    def _load_text_asset_summary(self, session: Session, content_ids: List[str], limit: int = 3) -> Dict[str, List[str]]:
        if not content_ids:
            return {}
        summary = {content_id: [] for content_id in content_ids}
        rows = session.query(ContentTextAsset).filter(ContentTextAsset.content_id.in_(content_ids)).all()
        for row in rows:
            values = summary.setdefault(row.content_id, [])
            text = (row.text or "").strip()
            if text and text not in values and len(values) < limit:
                values.append(text[:500])
        return summary

    def _content_metric(
        self,
        row: ContentItem,
        metric: Optional[ContentLifetimeMetric] = None,
        enrichment: Optional[Dict[str, List[str]]] = None,
        text_assets: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        enrichment = enrichment or {"tags": [], "keywords": []}
        return {
            "id": row.id,
            "contentId": row.id,
            "sourceType": "postgres_content",
            "sourceId": row.id,
            "title": row.title,
            "description": getattr(row, "description", None),
            "platformAccountId": getattr(row, "platform_account_id", None),
            "platform": row.platform,
            "publishedAt": row.published_at.isoformat() if row.published_at else None,
            "durationSeconds": row.duration_seconds,
            "views": metric.play_count if metric is not None else row.views,
            "likes": metric.like_count if metric is not None else row.likes,
            "comments": metric.comment_count if metric is not None else row.comments,
            "saves": metric.collect_count if metric is not None else row.saves,
            "shares": metric.share_count if metric is not None else row.shares,
            "completionRate": metric.finish_rate if metric is not None else row.completion_rate,
            "followersGained": metric.follow_count if metric is not None else row.followers_gained,
            "score": metric.metric_score if metric is not None and metric.metric_score is not None else row.score,
            "status": row.status,
            "hasAsr": row.has_asr,
            "reviewed": row.reviewed,
            "topicClusterId": getattr(row, "topic_cluster_id", None),
            "tags": enrichment.get("tags", []),
            "keywords": enrichment.get("keywords", []),
            "textAssets": text_assets or [],
        }

    def _content_relevance(self, item: Dict[str, Any], terms: List[str]) -> Dict[str, Any]:
        fields = {
            "title": [item.get("title") or ""],
            "description": [item.get("description") or ""],
            "tags": item.get("tags") or [],
            "keywords": item.get("keywords") or [],
            "textAssets": item.get("textAssets") or [],
        }
        matched_terms: List[str] = []
        matched_fields: List[str] = []
        for term in terms:
            for field, values in fields.items():
                if any(term.lower() in value.lower() for value in values if value):
                    if term not in matched_terms:
                        matched_terms.append(term)
                    if field not in matched_fields:
                        matched_fields.append(field)

        strong_fields = {"title", "description", "tags", "keywords", "textAssets"}
        has_strong_field = bool(strong_fields.intersection(matched_fields))
        if len(matched_terms) >= 2 and has_strong_field:
            level = "strong_related"
        elif matched_terms and has_strong_field:
            level = "medium_related"
        elif matched_terms:
            level = "weak_related"
        else:
            level = "unrelated"

        score_by_level = {
            "strong_related": 0.9,
            "medium_related": 0.74,
            "weak_related": 0.45,
            "unrelated": 0.0,
        }
        relevance_score = score_by_level[level] + min(len(matched_terms), 4) * 0.02
        return {
            "relevanceLevel": level,
            "relevanceScore": round(min(relevance_score, 0.99), 4),
            "matchedTerms": matched_terms,
            "matchFields": matched_fields,
            "reason": f"命中当前方向相关词：{', '.join(matched_terms)}" if matched_terms else "未命中当前方向相关词。",
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

    def _embedding_query(self, request: TopicIdeaGenerateRequest) -> str:
        parts = [
            request.direction,
            request.goal,
            request.audience or "",
            json.dumps(request.constraints, ensure_ascii=False, sort_keys=True) if request.constraints else "",
        ]
        return " ".join(part for part in parts if part)

    def _retrieval_source(
        self,
        content_id: str,
        keyword_ids: set[str],
        embedding_scores: Dict[str, float],
        relevance: Dict[str, Any],
    ) -> str:
        keyword_hit = bool(relevance.get("matchedTerms")) and content_id in keyword_ids
        embedding_hit = content_id in embedding_scores
        if keyword_hit and embedding_hit:
            return "hybrid"
        if embedding_hit:
            return "embedding"
        if keyword_hit:
            return "keyword"
        return "performance_pool"


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
