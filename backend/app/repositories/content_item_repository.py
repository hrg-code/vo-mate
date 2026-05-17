from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import desc, func
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.models import ContentItem as ContentItemModel
from app.db.models import ContentKeyword, ContentTag, ContentTextAsset, ContentTrafficSource
from app.db.models import ContentLifetimeMetric
from app.db.session import get_admin_engine
from app.schemas.common import ContentItem, ContentStatus, Platform


@dataclass
class ContentItemUpsert:
    id: str
    workspace_id: str
    platform: str
    external_content_id: str
    title: str
    platform_account_id: Optional[str] = None
    description: Optional[str] = None
    status: str = "published"
    published_at: Optional[datetime] = None
    duration_seconds: Optional[int] = None
    content_type: Optional[str] = None
    cover_url: Optional[str] = None
    video_url: Optional[str] = None
    topic_cluster_id: Optional[str] = None
    raw_collection: Optional[str] = None
    raw_document_id: Optional[str] = None
    has_asr: bool = False
    reviewed: bool = False


@dataclass
class ContentLifetimeMetricUpsert:
    content_id: str
    play_count: int = 0
    like_count: int = 0
    comment_count: int = 0
    share_count: int = 0
    collect_count: int = 0
    follow_count: int = 0
    profile_visit_count: int = 0
    avg_view_duration: Optional[float] = None
    avg_view_percent: Optional[float] = None
    finish_rate: Optional[float] = None
    five_second_retention: Optional[float] = None
    bounce_rate: Optional[float] = None
    negative_feedback_count: int = 0
    metric_score: Optional[float] = None
    raw_document_id: Optional[str] = None


@dataclass
class ContentTextAssetUpsert:
    content_id: str
    asset_type: str
    text: str
    language: Optional[str] = None
    segments: Optional[List[Dict[str, Any]]] = None
    raw_collection: Optional[str] = None
    raw_document_id: Optional[str] = None
    source: Optional[str] = None
    duration_seconds: Optional[float] = None


@dataclass
class ContentTagUpsert:
    content_id: str
    tag: str
    tag_type: str = "topic"
    external_tag_id: Optional[str] = None
    source: Optional[str] = None
    position_start: Optional[int] = None
    position_end: Optional[int] = None


@dataclass
class ContentKeywordUpsert:
    content_id: str
    keyword: str
    keyword_type: str = "search"
    score: Optional[float] = None
    query_count_7d: Optional[int] = None
    source: Optional[str] = None


@dataclass
class ContentTrafficSourceUpsert:
    content_id: str
    source_name: str
    source_type: str = "traffic"
    ratio: Optional[float] = None
    count: Optional[int] = None
    raw_payload: Optional[Dict[str, Any]] = None


@dataclass
class ContentEnrichmentCounts:
    text_asset_count: int = 0
    tag_count: int = 0
    keyword_count: int = 0
    traffic_source_count: int = 0
    asr_count: int = 0


class ContentItemRepository:
    def list_contents(self, limit: int = 100) -> Optional[List[ContentItem]]:
        with self._session() as session:
            if session is None:
                return None
            try:
                rows = (
                    session.query(ContentItemModel, ContentLifetimeMetric)
                    .outerjoin(ContentLifetimeMetric, ContentLifetimeMetric.content_id == ContentItemModel.id)
                    .order_by(
                        desc(func.coalesce(ContentLifetimeMetric.metric_score, ContentItemModel.score, 0)),
                        desc(func.coalesce(ContentLifetimeMetric.play_count, ContentItemModel.views, 0)),
                        desc(ContentItemModel.published_at),
                    )
                    .limit(limit)
                    .all()
                )
                if not rows:
                    return []
                return [self._to_schema(content, metric) for content, metric in rows]
            except SQLAlchemyError:
                session.rollback()
                return None

    def get_content(self, content_id: str) -> Optional[ContentItem]:
        with self._session() as session:
            if session is None:
                return None
            try:
                row = (
                    session.query(ContentItemModel, ContentLifetimeMetric)
                    .outerjoin(ContentLifetimeMetric, ContentLifetimeMetric.content_id == ContentItemModel.id)
                    .filter(ContentItemModel.id == content_id)
                    .first()
                )
                if row is None:
                    return None
                content, metric = row
                return self._to_schema(content, metric)
            except SQLAlchemyError:
                session.rollback()
                return None

    def upsert_content(self, content: ContentItemUpsert, metric: ContentLifetimeMetricUpsert) -> bool:
        with self._session() as session:
            if session is None:
                return False
            try:
                row = (
                    session.query(ContentItemModel)
                    .filter(
                        ContentItemModel.workspace_id == content.workspace_id,
                        ContentItemModel.platform == content.platform,
                        ContentItemModel.external_content_id == content.external_content_id,
                    )
                    .one_or_none()
                )
                if row is None:
                    row = ContentItemModel(id=content.id)
                    session.add(row)

                self._apply_content(row, content)
                metric_row = session.get(ContentLifetimeMetric, row.id)
                if metric_row is None:
                    metric_row = ContentLifetimeMetric(content_id=row.id)
                    session.add(metric_row)
                metric.content_id = row.id
                self._apply_metric(metric_row, metric)
                self._mirror_metric_columns(row, metric)
                session.commit()
                return True
            except SQLAlchemyError:
                session.rollback()
                return False

    def upsert_enrichment(
        self,
        content_id: str,
        text_assets: List[ContentTextAssetUpsert],
        tags: List[ContentTagUpsert],
        keywords: List[ContentKeywordUpsert],
        traffic_sources: List[ContentTrafficSourceUpsert],
        asr_asset: Optional[ContentTextAssetUpsert] = None,
    ) -> Optional[ContentEnrichmentCounts]:
        with self._session() as session:
            if session is None:
                return None
            try:
                self._replace_content_rows(session, ContentTextAsset, content_id, excluded_asset_types=["asr"])
                self._replace_content_rows(session, ContentTag, content_id)
                self._replace_content_rows(session, ContentKeyword, content_id)
                self._replace_content_rows(session, ContentTrafficSource, content_id)

                for asset in text_assets:
                    session.add(self._text_asset_model(asset))
                for tag in tags:
                    session.add(self._tag_model(tag))
                for keyword in keywords:
                    session.add(self._keyword_model(keyword))
                for traffic_source in traffic_sources:
                    session.add(self._traffic_source_model(traffic_source))

                asr_count = 0
                if asr_asset is not None and asr_asset.text:
                    self._replace_content_rows(session, ContentTextAsset, content_id, only_asset_types=["asr"])
                    session.add(self._text_asset_model(asr_asset))
                    row = session.get(ContentItemModel, content_id)
                    if row is not None:
                        row.has_asr = True
                    asr_count = 1

                session.commit()
                return ContentEnrichmentCounts(
                    text_asset_count=len(text_assets),
                    tag_count=len(tags),
                    keyword_count=len(keywords),
                    traffic_source_count=len(traffic_sources),
                    asr_count=asr_count,
                )
            except SQLAlchemyError:
                session.rollback()
                return None

    def get_asr(self, content_id: str) -> Optional[Dict[str, Any]]:
        with self._session() as session:
            if session is None:
                return None
            try:
                row = (
                    session.query(ContentTextAsset)
                    .filter(ContentTextAsset.content_id == content_id, ContentTextAsset.asset_type == "asr")
                    .order_by(ContentTextAsset.updated_at.desc())
                    .first()
                )
                if row is None:
                    return None
                duration = None
                if isinstance(row.segments, list) and row.segments:
                    last_segment = row.segments[-1]
                    if isinstance(last_segment, dict):
                        duration = last_segment.get("end")
                return {
                    "contentId": row.content_id,
                    "text": row.text,
                    "language": row.language,
                    "durationSeconds": duration,
                    "segments": row.segments or [],
                }
            except SQLAlchemyError:
                session.rollback()
                return None

    def load_enrichment_summary(self, content_ids: List[str], limit: int = 5) -> Dict[str, Dict[str, List[str]]]:
        if not content_ids:
            return {}
        with self._session() as session:
            if session is None:
                return {}
            try:
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
            except SQLAlchemyError:
                session.rollback()
                return {}

    def _session(self):
        return _OptionalSession()

    def _apply_content(self, row: ContentItemModel, content: ContentItemUpsert) -> None:
        row.workspace_id = content.workspace_id
        row.platform_account_id = content.platform_account_id
        row.platform = content.platform
        row.external_content_id = content.external_content_id
        row.title = content.title
        row.description = content.description
        row.status = content.status
        row.published_at = content.published_at
        row.duration_seconds = content.duration_seconds
        row.content_type = content.content_type
        row.cover_url = content.cover_url
        row.video_url = content.video_url
        row.topic_cluster_id = content.topic_cluster_id
        row.raw_collection = content.raw_collection
        row.raw_document_id = content.raw_document_id
        row.has_asr = content.has_asr
        row.reviewed = content.reviewed

    def _apply_metric(self, row: ContentLifetimeMetric, metric: ContentLifetimeMetricUpsert) -> None:
        row.play_count = metric.play_count
        row.like_count = metric.like_count
        row.comment_count = metric.comment_count
        row.share_count = metric.share_count
        row.collect_count = metric.collect_count
        row.follow_count = metric.follow_count
        row.profile_visit_count = metric.profile_visit_count
        row.avg_view_duration = metric.avg_view_duration
        row.avg_view_percent = metric.avg_view_percent
        row.finish_rate = metric.finish_rate
        row.five_second_retention = metric.five_second_retention
        row.bounce_rate = metric.bounce_rate
        row.negative_feedback_count = metric.negative_feedback_count
        row.metric_score = metric.metric_score
        row.raw_document_id = metric.raw_document_id

    def _replace_content_rows(
        self,
        session: Session,
        model,
        content_id: str,
        only_asset_types: Optional[List[str]] = None,
        excluded_asset_types: Optional[List[str]] = None,
    ) -> None:
        query = session.query(model).filter(model.content_id == content_id)
        if model is ContentTextAsset and only_asset_types:
            query = query.filter(ContentTextAsset.asset_type.in_(only_asset_types))
        if model is ContentTextAsset and excluded_asset_types:
            query = query.filter(~ContentTextAsset.asset_type.in_(excluded_asset_types))
        query.delete(synchronize_session=False)

    def _text_asset_model(self, asset: ContentTextAssetUpsert) -> ContentTextAsset:
        segments = asset.segments or []
        if asset.duration_seconds is not None and not segments:
            segments = [{"start": 0.0, "end": asset.duration_seconds, "text": asset.text}]
        return ContentTextAsset(
            content_id=asset.content_id,
            asset_type=asset.asset_type,
            text=asset.text,
            language=asset.language,
            segments=segments,
            raw_collection=asset.raw_collection,
            raw_document_id=asset.raw_document_id,
            source=asset.source or asset.asset_type,
        )

    def _tag_model(self, tag: ContentTagUpsert) -> ContentTag:
        return ContentTag(
            content_id=tag.content_id,
            tag=tag.tag,
            tag_type=tag.tag_type,
            external_tag_id=tag.external_tag_id,
            source=tag.source,
            position_start=tag.position_start,
            position_end=tag.position_end,
        )

    def _keyword_model(self, keyword: ContentKeywordUpsert) -> ContentKeyword:
        return ContentKeyword(
            content_id=keyword.content_id,
            keyword=keyword.keyword,
            keyword_type=keyword.keyword_type,
            score=keyword.score,
            query_count_7d=keyword.query_count_7d,
            source=keyword.source,
        )

    def _traffic_source_model(self, traffic_source: ContentTrafficSourceUpsert) -> ContentTrafficSource:
        return ContentTrafficSource(
            content_id=traffic_source.content_id,
            source_name=traffic_source.source_name,
            source_type=traffic_source.source_type,
            ratio=traffic_source.ratio,
            count=traffic_source.count,
            raw_payload=traffic_source.raw_payload or {},
        )

    def _mirror_metric_columns(self, row: ContentItemModel, metric: ContentLifetimeMetricUpsert) -> None:
        row.views = metric.play_count
        row.likes = metric.like_count
        row.comments = metric.comment_count
        row.saves = metric.collect_count
        row.shares = metric.share_count
        row.completion_rate = metric.finish_rate
        row.followers_gained = metric.follow_count
        row.score = metric.metric_score

    def _to_schema(self, content: ContentItemModel, metric: Optional[ContentLifetimeMetric]) -> ContentItem:
        views = metric.play_count if metric is not None else content.views
        likes = metric.like_count if metric is not None else content.likes
        comments = metric.comment_count if metric is not None else content.comments
        saves = metric.collect_count if metric is not None else content.saves
        shares = metric.share_count if metric is not None else content.shares
        completion_rate = self._float_or_zero(metric.finish_rate if metric is not None else content.completion_rate)
        followers_gained = metric.follow_count if metric is not None else content.followers_gained
        score = metric.metric_score if metric is not None and metric.metric_score is not None else content.score
        return ContentItem(
            id=content.id,
            title=content.title,
            platform=Platform(content.platform) if content.platform in Platform._value2member_map_ else Platform.douyin,
            published_at=content.published_at.date().isoformat() if content.published_at else "",
            duration_seconds=content.duration_seconds or 0,
            views=views or 0,
            likes=likes or 0,
            comments=comments or 0,
            saves=saves or 0,
            shares=shares or 0,
            completion_rate=completion_rate,
            followers_gained=followers_gained or 0,
            score=round(score or 0),
            status=ContentStatus(content.status) if content.status in ContentStatus._value2member_map_ else ContentStatus.published,
            has_asr=content.has_asr,
            reviewed=content.reviewed,
        )

    def _float_or_zero(self, value: Optional[float]) -> float:
        return float(value) if value is not None else 0.0


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


content_item_repository = ContentItemRepository()
