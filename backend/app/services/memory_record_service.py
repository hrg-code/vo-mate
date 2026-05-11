from __future__ import annotations

from typing import Any, Dict, List, Tuple

from fastapi import HTTPException

from app.core.config import get_settings
from app.schemas.agent import AgentEvidence, MemoryRecord, MemoryRecordCreate, MemorySearchRequest
from app.services.agent_store_service import agent_store
from app.services.ai_provider_service import ai_provider_service


MILVUS_MEMORY_COLLECTION = "vo_mate_agent_memories"


class MemoryRecordService:
    def list_records(self) -> List[MemoryRecord]:
        return agent_store.list_memories()

    def create_record(self, payload: MemoryRecordCreate) -> MemoryRecord:
        return agent_store.create_memory(payload)

    def transition(self, memory_id: str, status: str) -> MemoryRecord:
        record = agent_store.transition_memory(memory_id, status)
        if record is None:
            raise HTTPException(status_code=404, detail="Memory record not found")
        return record


class MemoryVectorService:
    # L3/L4 记忆服务边界：
    # - PostgreSQL 是记忆正文、状态、置信度、证据数量、来源 ID 和审计字段的事实来源。
    # - Milvus 只保存文本向量和可过滤元数据，召回后返回记忆 ID 供 PostgreSQL 回查。
    # - 当前 MVP 使用内存版 `agent_store`；保留这个接口，便于后续平滑替换为 PostgreSQL/Milvus。
    def __init__(self) -> None:
        self.embedding_provider = ai_provider_service.get_embedding_provider()

    def searchable_text(self, record: MemoryRecord) -> str:
        # 这是单条长期记忆的标准向量化输入。保持简洁：向量检索用于找到证据，
        # 不应替代 PostgreSQL 中的结构化记忆记录。
        return "\n".join(
            [
                f"类型：{record.memory_type}",
                f"标题：{record.title}",
                f"摘要：{record.summary}",
                f"正文：{record.content}",
                f"标签：{record.metadata}",
            ]
        )

    def upsert_memory(self, payload: MemoryRecordCreate) -> MemoryRecord:
        # 长期记忆写入应先创建可审计记录，再索引可搜索投影。
        record = agent_store.create_memory(payload)
        try:
            embedding = self.embedding_provider.embed_documents([self.searchable_text(record)])[0]
            self._upsert_milvus_record(record, embedding)
        except Exception:
            # 向量索引是召回加速层，不应影响记忆事实写入。
            pass
        return record

    def search(self, request: MemorySearchRequest, run_id: str | None = None) -> List[AgentEvidence]:
        # 召回结果只返回热路径需要的小型证据包。不要把命中的所有字段都传入提示词；
        # 调试和追溯使用记忆 ID 关联完整记录。
        results = self.search_milvus(request)
        if not results:
            results = self._search_memory_store(request)

        if run_id is not None:
            self._record_trace(request, run_id, results)
        return results

    def search_milvus(self, request: MemorySearchRequest) -> List[AgentEvidence]:
        hits = self.search_milvus_hits(request)
        return self.hydrate_memory_hits(hits)

    def search_milvus_hits(self, request: MemorySearchRequest) -> List[Tuple[str, float]]:
        settings = get_settings()
        if not settings.milvus_host:
            return []

        try:
            query_embedding = self.embedding_provider.embed_query(request.query)
            return self._search_milvus_ids(request, query_embedding)
        except Exception:
            return []

    def _search_memory_store(self, request: MemorySearchRequest) -> List[AgentEvidence]:
        try:
            self.embedding_provider.embed_query(request.query)
        except Exception:
            pass
        query_terms = {term for term in request.query.replace("，", " ").replace("、", " ").split() if term}
        records = [
            record
            for record in agent_store.memories
            if record.workspace_id == request.workspace_id
            and record.account_id == request.account_id
            and record.platform == request.platform
            and record.status == request.status
            and (not request.memory_types or record.memory_type in request.memory_types)
        ]

        scored: List[tuple[float, MemoryRecord]] = []
        for record in records:
            haystack = f"{record.title} {record.summary} {record.content}"
            overlap = sum(1 for term in query_terms if term in haystack)
            score = min(0.99, 0.62 + overlap * 0.08 + record.confidence * 0.12)
            scored.append((round(score, 4), record))
        scored.sort(key=lambda item: item[0], reverse=True)

        results = [
            AgentEvidence(
                memory_id=record.id,
                memory_type=record.memory_type,
                title=record.title,
                summary=record.summary,
                score=score,
                reason=f"命中 {record.memory_type} 记忆，置信度 {record.confidence:.2f}",
            )
            for score, record in scored[: request.top_k]
        ]
        return results

    def hydrate_memory_hits(self, hits: List[Tuple[str, float]]) -> List[AgentEvidence]:
        records_by_id = {record.id: record for record in agent_store.memories}
        results: List[AgentEvidence] = []
        for memory_id, score in hits:
            record = records_by_id.get(memory_id)
            if record is None:
                continue
            results.append(
                AgentEvidence(
                    memory_id=record.id,
                    memory_type=record.memory_type,
                    title=record.title,
                    summary=record.summary,
                    score=score,
                    reason=f"向量召回 {record.memory_type} 记忆，置信度 {record.confidence:.2f}",
                )
            )
        return results

    def _record_trace(self, request: MemorySearchRequest, run_id: str, results: List[AgentEvidence]) -> None:
        filters: Dict[str, Any] = {
            "workspaceId": request.workspace_id,
            "accountId": request.account_id,
            "platform": request.platform,
            "status": request.status,
        }
        agent_store.add_trace(
            run_id=run_id,
            query=request.query,
            memory_types=request.memory_types,
            filters=filters,
            top_k=request.top_k,
            results=[result.model_dump(by_alias=True) for result in results],
        )

    def _upsert_milvus_record(self, record: MemoryRecord, embedding: List[float]) -> None:
        collection = self._get_milvus_collection()
        collection.upsert(
            [
                [record.id],
                [embedding],
                [record.workspace_id],
                [record.account_id],
                [record.platform],
                [record.memory_type],
                [record.status],
            ]
        )
        collection.flush()

    def _search_milvus_ids(self, request: MemorySearchRequest, query_embedding: List[float]) -> List[Tuple[str, float]]:
        collection = self._get_milvus_collection()
        collection.load()
        search_results = collection.search(
            data=[query_embedding],
            anns_field="embedding",
            param={"metric_type": "COSINE", "params": {"nprobe": 10}},
            limit=request.top_k,
            expr=self._milvus_filter_expr(request),
            output_fields=["memory_id"],
        )
        hits: List[Tuple[str, float]] = []
        for hit in search_results[0]:
            memory_id = hit.entity.get("memory_id")
            hits.append((str(memory_id), round(float(hit.score), 4)))
        return hits

    def _get_milvus_collection(self):
        from pymilvus import Collection, CollectionSchema, DataType, FieldSchema, utility

        settings = get_settings()
        collection_name = MILVUS_MEMORY_COLLECTION
        if not utility.has_collection(collection_name, using="default"):
            fields = [
                FieldSchema(name="memory_id", dtype=DataType.VARCHAR, is_primary=True, max_length=64),
                FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=settings.dashscope_embedding_dimension),
                FieldSchema(name="workspace_id", dtype=DataType.VARCHAR, max_length=64),
                FieldSchema(name="account_id", dtype=DataType.VARCHAR, max_length=128),
                FieldSchema(name="platform", dtype=DataType.VARCHAR, max_length=32),
                FieldSchema(name="memory_type", dtype=DataType.VARCHAR, max_length=64),
                FieldSchema(name="status", dtype=DataType.VARCHAR, max_length=32),
            ]
            schema = CollectionSchema(fields=fields, description="VO Mate agent memory vector index")
            collection = Collection(name=collection_name, schema=schema, using="default")
            collection.create_index(
                field_name="embedding",
                index_params={"metric_type": "COSINE", "index_type": "AUTOINDEX", "params": {}},
            )
            return collection
        return Collection(name=collection_name, using="default")

    def _milvus_filter_expr(self, request: MemorySearchRequest) -> str:
        conditions = [
            f'workspace_id == "{self._escape_milvus_string(request.workspace_id)}"',
            f'account_id == "{self._escape_milvus_string(request.account_id)}"',
            f'platform == "{self._escape_milvus_string(request.platform)}"',
            f'status == "{self._escape_milvus_string(request.status)}"',
        ]
        if request.memory_types:
            values = ", ".join(f'"{self._escape_milvus_string(memory_type)}"' for memory_type in request.memory_types)
            conditions.append(f"memory_type in [{values}]")
        return " and ".join(conditions)

    def _escape_milvus_string(self, value: str) -> str:
        return value.replace("\\", "\\\\").replace('"', '\\"')


memory_record_service = MemoryRecordService()
memory_vector_service = MemoryVectorService()
