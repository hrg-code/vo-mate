from __future__ import annotations

import hashlib
import math
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional, Tuple

from app.core.connections import connection_manager
from app.repositories.content_item_repository import (
    ContentEnrichmentCounts,
    ContentItemRepository,
    ContentItemUpsert,
    ContentKeywordUpsert,
    ContentLifetimeMetricUpsert,
    ContentTagUpsert,
    ContentTextAssetUpsert,
    ContentTrafficSourceUpsert,
    content_item_repository,
)
from app.repositories.memory_store import InMemoryRepository, repository
from app.schemas.common import AgentTask, CollectorImportRequest, CollectorImportResponse, Platform, TaskStatus
from app.services.content_vector_service import content_vector_service


class DouyinRawAdapter:
    platform = "douyin"

    def external_content_id(self, raw: Dict[str, Any]) -> str:
        external_content_id = str(
            self._first_value(
                raw,
                ["_id", "aweme_id", "base_info.aweme_id", "statistics.aweme_id", "raw_list_data.aweme_id"],
                default="",
            )
        )
        if external_content_id:
            return external_content_id
        digest = hashlib.sha1(str(raw).encode("utf-8")).hexdigest()[:12]
        return f"unknown_{digest}"

    def to_standard(
        self,
        raw: Dict[str, Any],
        workspace_id: str,
        raw_collection: str,
        platform_account_id: Optional[str] = None,
    ) -> Tuple[ContentItemUpsert, ContentLifetimeMetricUpsert]:
        external_content_id = self.external_content_id(raw)

        description = self._text(
            self._first_value(
                raw,
                ["base_info.desc", "raw_list_data.desc", "raw_list_data.caption", "raw_list_data.next_info.desc"],
                default="",
            )
        )
        title = self._title_from_description(description) or f"抖音作品 {external_content_id}"
        duration = self._int(
            self._first_value(raw, ["base_info.duration", "raw_list_data.video.duration", "raw_list_data.duration"], default=0)
        )
        duration_seconds = round(duration / 1000) if duration > 1000 else duration
        raw_document_id = str(raw.get("_id") or external_content_id)

        content = ContentItemUpsert(
            id=f"ct_douyin_{external_content_id}",
            workspace_id=workspace_id,
            platform_account_id=platform_account_id,
            platform=self.platform,
            external_content_id=external_content_id,
            title=title[:500],
            description=description or None,
            published_at=self._datetime(
                self._first_value(raw, ["base_info.create_time", "raw_list_data.create_time", "create_time"], default=None)
            ),
            duration_seconds=duration_seconds,
            content_type="video",
            cover_url=self._cover_url(raw),
            video_url=self._first_url(raw, ["raw_list_data.video.play_addr.url_list", "raw_list_data.video.download_addr.url_list"]),
            raw_collection=raw_collection,
            raw_document_id=raw_document_id,
            has_asr=bool(self._first_value(raw, ["has_asr", "asr_text", "asr.transcript"], default=False)),
        )
        metric = self._metric(raw, content.id, raw_document_id)
        return content, metric

    def text_assets(self, raw: Dict[str, Any], content: ContentItemUpsert) -> List[ContentTextAssetUpsert]:
        assets: List[ContentTextAssetUpsert] = []
        candidates = [
            ("title", content.title, "base_info.title"),
            ("description", content.description, "base_info.desc"),
            ("caption", self._text(self._first_value(raw, ["raw_list_data.caption", "raw_list_data.next_info.caption"], default="")), "raw_list_data.caption"),
        ]
        seen = set()
        for asset_type, text, source in candidates:
            if not text or (asset_type, text) in seen:
                continue
            seen.add((asset_type, text))
            assets.append(
                ContentTextAssetUpsert(
                    content_id=content.id,
                    asset_type=asset_type,
                    text=text,
                    language="zh",
                    raw_collection=content.raw_collection,
                    raw_document_id=content.raw_document_id,
                    source=source,
                )
            )
        return assets

    def tags(self, raw: Dict[str, Any], content_id: str) -> List[ContentTagUpsert]:
        tags: List[ContentTagUpsert] = []
        seen = set()
        for item in self._list_path(raw, "raw_list_data.cha_list"):
            tag = self._text(self._first_value(item, ["cha_name", "hashtag_name", "tag_name", "name"], default=""))
            if not tag or tag in seen:
                continue
            seen.add(tag)
            tags.append(
                ContentTagUpsert(
                    content_id=content_id,
                    tag=tag,
                    tag_type="topic",
                    external_tag_id=self._optional_str(self._first_value(item, ["cha_id", "cid", "id"], default=None)),
                    source="raw_list_data.cha_list",
                )
            )
        for path in ["raw_list_data.text_extra", "raw_list_data.next_info.text_extra"]:
            for item in self._list_path(raw, path):
                tag = self._text(self._first_value(item, ["hashtag_name", "cha_name", "tag_name", "name"], default=""))
                if not tag or (path, tag) in seen:
                    continue
                seen.add((path, tag))
                tags.append(
                    ContentTagUpsert(
                        content_id=content_id,
                        tag=tag,
                        tag_type="text_extra",
                        external_tag_id=self._optional_str(self._first_value(item, ["hashtag_id", "cid", "cha_id", "id"], default=None)),
                        source=path,
                        position_start=self._optional_int(self._first_value(item, ["caption_start", "start"], default=None)),
                        position_end=self._optional_int(self._first_value(item, ["caption_end", "end"], default=None)),
                    )
                )
        return tags

    def keywords(self, raw: Dict[str, Any], content_id: str) -> List[ContentKeywordUpsert]:
        keywords: List[ContentKeywordUpsert] = []
        seen = set()
        for item in self._list_path(raw, "analysis.other_data.audience_search_most_keywords"):
            keyword = self._text(self._first_value(item, ["keywords", "keyword", "word"], default=""))
            if not keyword or keyword in seen:
                continue
            seen.add(keyword)
            query_count = self._optional_int(self._first_value(item, ["query_cnt_7d", "query_count_7d"], default=None))
            if query_count is None:
                query_count = sum(self._int(day.get("value")) for day in self._list_path(item, "query_7d_list"))
            keywords.append(
                ContentKeywordUpsert(
                    content_id=content_id,
                    keyword=keyword,
                    keyword_type="audience_search",
                    score=float(query_count or 0),
                    query_count_7d=query_count,
                    source="analysis.other_data.audience_search_most_keywords",
                )
            )
        return keywords

    def traffic_sources(self, raw: Dict[str, Any], content_id: str) -> List[ContentTrafficSourceUpsert]:
        traffic_sources: List[ContentTrafficSourceUpsert] = []
        for path in ["analysis.traffic_sources", "analysis.traffic_source", "creator_stats.traffic_sources", "traffic_sources"]:
            for item in self._list_path(raw, path):
                name = self._text(self._first_value(item, ["source_name", "name", "key", "label"], default=""))
                if not name:
                    continue
                traffic_sources.append(
                    ContentTrafficSourceUpsert(
                        content_id=content_id,
                        source_name=name,
                        source_type=path,
                        ratio=self._optional_float(self._first_value(item, ["ratio", "percent", "value"], default=None)),
                        count=self._optional_int(self._first_value(item, ["count", "play_count", "vv"], default=None)),
                        raw_payload=item,
                    )
                )
        return traffic_sources

    def asr_asset(self, asr: Optional[Dict[str, Any]], content: ContentItemUpsert, asr_collection: str) -> Optional[ContentTextAssetUpsert]:
        if not asr:
            return None
        text = self._text(asr.get("text"))
        if not text:
            return None
        return ContentTextAssetUpsert(
            content_id=content.id,
            asset_type="asr",
            text=text,
            language=self._optional_str(asr.get("language")),
            segments=asr.get("segments") if isinstance(asr.get("segments"), list) else [],
            raw_collection=asr_collection,
            raw_document_id=self._optional_str(asr.get("_id")) or self._optional_str(asr.get("video_id")),
            source=asr_collection,
            duration_seconds=self._optional_float(asr.get("duration_seconds")),
        )

    def _metric(self, raw: Dict[str, Any], content_id: str, raw_document_id: str) -> ContentLifetimeMetricUpsert:
        stats_paths = ["creator_stats", "statistics", "raw_list_data.statistics"]
        play_count = self._metric_int(raw, stats_paths, ["play_count", "playCnt", "view_count"])
        like_count = self._metric_int(raw, stats_paths, ["digg_count", "like_count"])
        comment_count = self._metric_int(raw, stats_paths, ["comment_count"])
        share_count = self._metric_int(raw, stats_paths, ["share_count", "forward_count"])
        collect_count = self._metric_int(raw, stats_paths, ["collect_count", "favorite_count"])
        follow_count = self._metric_int(raw, stats_paths, ["follow_count", "followers_gained", "new_follow_count"])
        finish_rate = self._metric_float(raw, stats_paths, ["finish_rate", "completion_rate", "complete_play_rate"])
        avg_view_duration = self._metric_float(raw, stats_paths, ["avg_view_duration"])
        metric_score = self._metric_float(raw, stats_paths, ["metric_score", "score"])
        if metric_score is None:
            metric_score = self._score(play_count, like_count, comment_count, share_count, collect_count, finish_rate)
        return ContentLifetimeMetricUpsert(
            content_id=content_id,
            play_count=play_count,
            like_count=like_count,
            comment_count=comment_count,
            share_count=share_count,
            collect_count=collect_count,
            follow_count=follow_count,
            avg_view_duration=avg_view_duration,
            finish_rate=finish_rate,
            metric_score=metric_score,
            raw_document_id=raw_document_id,
        )

    def _metric_int(self, raw: Dict[str, Any], roots: Iterable[str], names: Iterable[str]) -> int:
        for root in roots:
            for name in names:
                value = self._get_path(raw, f"{root}.{name}")
                if value is not None:
                    return self._int(value)
        return 0

    def _metric_float(self, raw: Dict[str, Any], roots: Iterable[str], names: Iterable[str]) -> Optional[float]:
        for root in roots:
            for name in names:
                value = self._get_path(raw, f"{root}.{name}")
                if value is not None:
                    return self._float(value)
        return None

    def _score(
        self,
        play_count: int,
        like_count: int,
        comment_count: int,
        share_count: int,
        collect_count: int,
        finish_rate: Optional[float],
    ) -> float:
        engagement = like_count + comment_count + share_count + collect_count
        engagement_rate = engagement / max(play_count, 1)
        finish_bonus = (finish_rate or 0) * 20
        return min(100.0, round(math.log10(max(play_count, 0) + 1) * 12 + engagement_rate * 100 + finish_bonus, 2))

    def _cover_url(self, raw: Dict[str, Any]) -> Optional[str]:
        direct = self._first_value(raw, ["base_info.cover"], default=None)
        if isinstance(direct, str) and direct:
            return direct
        return self._first_url(
            raw,
            [
                "raw_list_data.video.cover.url_list",
                "raw_list_data.video.origin_cover.url_list",
                "raw_list_data.horizontal_cover.url_list",
            ],
        )

    def _first_url(self, raw: Dict[str, Any], paths: Iterable[str]) -> Optional[str]:
        for path in paths:
            value = self._get_path(raw, path)
            if isinstance(value, list) and value:
                return str(value[0])
            if isinstance(value, str) and value:
                return value
        return None

    def _first_value(self, raw: Dict[str, Any], paths: Iterable[str], default: Any) -> Any:
        for path in paths:
            value = self._get_path(raw, path)
            if value not in (None, ""):
                return value
        return default

    def _get_path(self, raw: Dict[str, Any], path: str) -> Any:
        current: Any = raw
        for part in path.split("."):
            if not isinstance(current, dict) or part not in current:
                return None
            current = current[part]
        return current

    def _list_path(self, raw: Dict[str, Any], path: str) -> List[Dict[str, Any]]:
        value = self._get_path(raw, path)
        if not isinstance(value, list):
            return []
        return [item for item in value if isinstance(item, dict)]

    def _datetime(self, value: Any) -> Optional[datetime]:
        if value in (None, ""):
            return None
        if isinstance(value, datetime):
            return value
        try:
            if isinstance(value, (int, float)):
                return datetime.fromtimestamp(value, tz=timezone.utc)
            if isinstance(value, str) and value.isdigit():
                return datetime.fromtimestamp(int(value), tz=timezone.utc)
            if isinstance(value, str):
                return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except (TypeError, ValueError, OSError):
            return None
        return None

    def _int(self, value: Any) -> int:
        try:
            return int(float(value))
        except (TypeError, ValueError):
            return 0

    def _optional_int(self, value: Any) -> Optional[int]:
        if value in (None, ""):
            return None
        return self._int(value)

    def _float(self, value: Any) -> Optional[float]:
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    def _optional_float(self, value: Any) -> Optional[float]:
        return self._float(value)

    def _optional_str(self, value: Any) -> Optional[str]:
        if value in (None, ""):
            return None
        return str(value)

    def _text(self, value: Any) -> str:
        return str(value).strip() if value is not None else ""

    def _title_from_description(self, description: str) -> str:
        first_line = description.splitlines()[0].strip() if description else ""
        return first_line[:80]


class ContentIngestionService:
    def __init__(self, content_repository: ContentItemRepository, memory_repository: InMemoryRepository) -> None:
        self.content_repository = content_repository
        self.memory_repository = memory_repository
        self.douyin_adapter = DouyinRawAdapter()

    async def upload_raw(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        raw = self.memory_repository.add_raw_upload(payload)
        mongo_database = connection_manager.mongo_database
        if mongo_database is None:
            return raw

        platform = str(payload.get("platform") or "unknown")
        collection_name = str(payload.get("collection") or f"{platform}_raw_events")
        document = {
            "platform": platform,
            "sourceUrl": payload.get("sourceUrl"),
            "payload": payload.get("payload", payload),
            "meta": payload.get("meta", {}),
            "receivedAt": datetime.now(timezone.utc),
        }
        result = await mongo_database[collection_name].insert_one(document)
        raw["id"] = str(result.inserted_id)
        raw["collection"] = collection_name
        return raw

    async def import_raw_data(self, request: CollectorImportRequest) -> CollectorImportResponse:
        task = self.memory_repository.create_task(
            "raw-import",
            request.model_dump(by_alias=True),
        )
        if request.platform != Platform.douyin:
            self._finish_task(task, TaskStatus.failed, "仅支持 douyin 导入")
            return self._response(task.id, "failed", 0, 0, 0)

        documents = await self._load_raw_documents(request.collection, request.limit)
        if documents is None:
            self._finish_task(task, TaskStatus.failed, "MongoDB 未配置或不可用")
            return self._response(task.id, "failed", 0, 0, 0)

        asr_by_video_id = {}
        if request.include_asr:
            external_ids = [self.douyin_adapter.external_content_id(raw) for raw in documents]
            asr_by_video_id = await self._load_asr_documents(request.asr_collection, external_ids) or {}

        processed_count = 0
        upserted_count = 0
        failed_count = 0
        enrichment_counts = ContentEnrichmentCounts()
        for raw in documents:
            processed_count += 1
            try:
                content, metric = self.douyin_adapter.to_standard(
                    raw=raw,
                    workspace_id=request.workspace_id,
                    raw_collection=request.collection,
                    platform_account_id=request.account_id,
                )
                if self.content_repository.upsert_content(content, metric):
                    upserted_count += 1
                    asr = asr_by_video_id.get(content.external_content_id)
                    counts = self.content_repository.upsert_enrichment(
                        content_id=content.id,
                        text_assets=self.douyin_adapter.text_assets(raw, content),
                        tags=self.douyin_adapter.tags(raw, content.id),
                        keywords=self.douyin_adapter.keywords(raw, content.id),
                        traffic_sources=self.douyin_adapter.traffic_sources(raw, content.id),
                        asr_asset=self.douyin_adapter.asr_asset(asr, content, request.asr_collection),
                    )
                    if counts is not None:
                        enrichment_counts.text_asset_count += counts.text_asset_count
                        enrichment_counts.tag_count += counts.tag_count
                        enrichment_counts.keyword_count += counts.keyword_count
                        enrichment_counts.traffic_source_count += counts.traffic_source_count
                        enrichment_counts.asr_count += counts.asr_count
                    content_vector_service.upsert_content_vector(content.id)
                else:
                    failed_count += 1
            except Exception:
                failed_count += 1

        status = TaskStatus.succeeded if failed_count == 0 else TaskStatus.failed
        self._finish_task(task, status, "已完成" if status == TaskStatus.succeeded else "部分或全部导入失败")
        return self._response(task.id, status.value, processed_count, upserted_count, failed_count, enrichment_counts)

    async def _load_raw_documents(self, collection: str, limit: int) -> Optional[List[Dict[str, Any]]]:
        mongo_database = connection_manager.mongo_database
        if mongo_database is None:
            return None
        cursor = mongo_database[collection].find({}).limit(limit)
        return [document async for document in cursor]

    async def _load_asr_documents(self, collection: str, video_ids: List[str]) -> Optional[Dict[str, Dict[str, Any]]]:
        mongo_database = connection_manager.mongo_database
        if mongo_database is None or not video_ids:
            return None
        cursor = mongo_database[collection].find({"video_id": {"$in": video_ids}})
        rows = [document async for document in cursor]
        return {str(row.get("video_id")): row for row in rows if row.get("video_id") is not None}

    def _finish_task(self, task: AgentTask, status: TaskStatus, current_step: str) -> None:
        task.status = status
        task.progress = 100
        task.current_step = current_step

    def _response(
        self,
        task_id: str,
        status: str,
        processed_count: int,
        upserted_count: int,
        failed_count: int,
        enrichment_counts: Optional[ContentEnrichmentCounts] = None,
    ) -> CollectorImportResponse:
        enrichment_counts = enrichment_counts or ContentEnrichmentCounts()
        return CollectorImportResponse(
            task_id=task_id,
            status=status,
            processed_count=processed_count,
            upserted_count=upserted_count,
            failed_count=failed_count,
            text_asset_count=enrichment_counts.text_asset_count,
            tag_count=enrichment_counts.tag_count,
            keyword_count=enrichment_counts.keyword_count,
            traffic_source_count=enrichment_counts.traffic_source_count,
            asr_count=enrichment_counts.asr_count,
        )


content_ingestion_service = ContentIngestionService(content_item_repository, repository)
