from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.models import ContentItem, ContentKeyword, ContentLifetimeMetric, ContentTag, ContentTextAsset
from app.db.session import get_admin_engine
from app.schemas.common import TopicIdeaGenerateRequest
from app.services.ai_provider_service import ai_provider_service


CREATOR_CONTENT_VECTOR_COLLECTION = "creator_content_vectors"


class ContentVectorService:
    def __init__(self) -> None:
        self.embedding_provider = ai_provider_service.get_embedding_provider()
        self.last_error: Optional[str] = None

    def searchable_text(
        self,
        content: Any,
        enrichment: Optional[Dict[str, List[str]]] = None,
        text_assets: Optional[List[str]] = None,
        metric: Optional[Any] = None,
    ) -> str:
        enrichment = enrichment or {"tags": [], "keywords": []}
        text_assets = text_assets or []
        metric_score = getattr(metric, "metric_score", None)
        play_count = getattr(metric, "play_count", None)
        finish_rate = getattr(metric, "finish_rate", None)
        return "\n".join(
            [
                f"标题：{getattr(content, 'title', '') or ''}",
                f"描述：{getattr(content, 'description', '') or ''}",
                f"标签：{' '.join(enrichment.get('tags', []))}",
                f"关键词：{' '.join(enrichment.get('keywords', []))}",
                f"文本素材：{' '.join(text_assets)}",
                f"表现摘要：score={metric_score if metric_score is not None else getattr(content, 'score', '')}; "
                f"views={play_count if play_count is not None else getattr(content, 'views', '')}; "
                f"finishRate={finish_rate if finish_rate is not None else getattr(content, 'completion_rate', '')}",
            ]
        )

    def upsert_content_vector(self, content_id: str) -> bool:
        self.last_error = None
        try:
            with self._session() as session:
                if session is None:
                    return False
                row = (
                    session.query(ContentItem, ContentLifetimeMetric)
                    .outerjoin(ContentLifetimeMetric, ContentLifetimeMetric.content_id == ContentItem.id)
                    .filter(ContentItem.id == content_id, ContentItem.status == "published")
                    .first()
                )
                if row is None:
                    return False
                content, metric = row
                enrichment = self._load_enrichment_summary(session, [content.id]).get(content.id, {"tags": [], "keywords": []})
                text_assets = self._load_text_asset_summary(session, [content.id]).get(content.id, [])
                embedding = self.embedding_provider.embed_documents([self.searchable_text(content, enrichment, text_assets, metric)])[0]
                self._upsert_milvus_content(content, metric, embedding)
                return True
        except Exception as exc:
            self.last_error = f"{exc.__class__.__name__}: {exc}"
            return False

    def search_content_hits(self, request: TopicIdeaGenerateRequest, query: str, top_k: int = 24) -> List[Tuple[str, float, str]]:
        self.last_error = None
        settings = get_settings()
        if not settings.milvus_host:
            return []
        try:
            query_embedding = self.embedding_provider.embed_query(query)
            return self._search_milvus_content_ids(request, query_embedding, top_k)
        except Exception as exc:
            self.last_error = f"{exc.__class__.__name__}: {exc}"
            return []

    def _session(self):
        return _OptionalSession()

    def _load_enrichment_summary(self, session: Session, content_ids: List[str], limit: int = 5) -> Dict[str, Dict[str, List[str]]]:
        if not content_ids:
            return {}
        summary = {content_id: {"tags": [], "keywords": []} for content_id in content_ids}
        tags = session.query(ContentTag).filter(ContentTag.content_id.in_(content_ids)).all()
        keywords = session.query(ContentKeyword).filter(ContentKeyword.content_id.in_(content_ids)).all()
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

    def _upsert_milvus_content(self, content: ContentItem, metric: Optional[ContentLifetimeMetric], embedding: List[float]) -> None:
        collection = self._get_milvus_collection()
        vector_id = self._vector_id(content.id)
        collection.upsert(
            [
                [vector_id],
                [embedding],
                [content.workspace_id],
                [content.platform_account_id or ""],
                [content.platform],
                [content.id],
                [content.external_content_id or ""],
                ["summary"],
                [content.status],
                [self._published_at_ts(content.published_at)],
                [float(metric.metric_score if metric is not None and metric.metric_score is not None else content.score or 0)],
                [int(metric.play_count if metric is not None else content.views or 0)],
            ]
        )
        collection.flush()

    def _search_milvus_content_ids(self, request: TopicIdeaGenerateRequest, query_embedding: List[float], top_k: int) -> List[Tuple[str, float, str]]:
        collection = self._get_milvus_collection()
        collection.load()
        search_results = collection.search(
            data=[query_embedding],
            anns_field="embedding",
            param={"metric_type": "COSINE", "params": {"nprobe": 10}},
            limit=top_k,
            expr=self._milvus_filter_expr(request),
            output_fields=["content_id", "vector_id"],
        )
        hits: List[Tuple[str, float, str]] = []
        for hit in search_results[0]:
            content_id = hit.entity.get("content_id")
            vector_id = hit.entity.get("vector_id")
            if content_id is not None:
                hits.append((str(content_id), round(float(hit.score), 4), str(vector_id)))
        return hits

    def _get_milvus_collection(self):
        from pymilvus import Collection, CollectionSchema, DataType, FieldSchema, utility

        settings = get_settings()
        collection_name = CREATOR_CONTENT_VECTOR_COLLECTION
        if not utility.has_collection(collection_name, using="default"):
            fields = [
                FieldSchema(name="vector_id", dtype=DataType.VARCHAR, is_primary=True, max_length=128),
                FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=settings.dashscope_embedding_dimension),
                FieldSchema(name="workspace_id", dtype=DataType.VARCHAR, max_length=64),
                FieldSchema(name="account_id", dtype=DataType.VARCHAR, max_length=128),
                FieldSchema(name="platform", dtype=DataType.VARCHAR, max_length=32),
                FieldSchema(name="content_id", dtype=DataType.VARCHAR, max_length=64),
                FieldSchema(name="external_content_id", dtype=DataType.VARCHAR, max_length=255),
                FieldSchema(name="chunk_type", dtype=DataType.VARCHAR, max_length=64),
                FieldSchema(name="status", dtype=DataType.VARCHAR, max_length=32),
                FieldSchema(name="published_at_ts", dtype=DataType.INT64),
                FieldSchema(name="metric_score", dtype=DataType.FLOAT),
                FieldSchema(name="views", dtype=DataType.INT64),
            ]
            schema = CollectionSchema(fields=fields, description="VO Mate creator content vector index")
            collection = Collection(name=collection_name, schema=schema, using="default")
            collection.create_index(
                field_name="embedding",
                index_params={"metric_type": "COSINE", "index_type": "AUTOINDEX", "params": {}},
            )
            return collection
        return Collection(name=collection_name, using="default")

    def _milvus_filter_expr(self, request: TopicIdeaGenerateRequest) -> str:
        platforms = [platform.value for platform in request.platforms]
        account_values = ", ".join(f'"{self._escape_milvus_string(account_id)}"' for account_id in request.account_ids)
        platform_values = ", ".join(f'"{self._escape_milvus_string(platform)}"' for platform in platforms)
        return " and ".join(
            [
                f'workspace_id == "{self._escape_milvus_string(request.workspace_id)}"',
                f"account_id in [{account_values}]",
                f"platform in [{platform_values}]",
                'status == "published"',
            ]
        )

    def _vector_id(self, content_id: str) -> str:
        return f"content:{content_id}:summary"

    def _published_at_ts(self, value: Any) -> int:
        if isinstance(value, datetime):
            return int(value.timestamp())
        return 0

    def _escape_milvus_string(self, value: str) -> str:
        return value.replace("\\", "\\\\").replace('"', '\\"')


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


content_vector_service = ContentVectorService()
