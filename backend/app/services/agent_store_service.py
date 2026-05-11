from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

from app.schemas.agent import (
    AgentRunRecord,
    AgentRunStepRecord,
    AgentThreadSummaryRecord,
    MemoryRecord,
    MemoryRecordCreate,
    MemoryRecordUpdate,
)


class AgentStoreService:
    def __init__(self) -> None:
        self.memories: List[MemoryRecord] = [
            MemoryRecord(
                id="mem_persona_demo",
                workspace_id="ws_northstar",
                account_id="douyin_demo",
                platform="douyin",
                memory_type="persona_profile",
                title="纯野生程序员老韩人设",
                content="15 年野生程序员，高中学历，农村土著，被裁后自由职业，用 AI 寻找普通人的出路。",
                summary="普通人视角、野生程序员、AI 自救，不使用大厂精英口吻。",
                metadata={"topicCluster": "persona"},
                source_type="seed",
                source_ids=[],
                confidence=0.86,
                evidence_count=3,
                status="active",
                created_at=self._now_iso(),
                updated_at=self._now_iso(),
            ),
            MemoryRecord(
                id="mem_case_demo",
                workspace_id="ws_northstar",
                account_id="douyin_demo",
                platform="douyin",
                memory_type="content_case",
                title="程序员可以干一辈子吗",
                content="职业危机类内容，播放 34599，完播 11.3%，5 秒留存 44.8%，评论率高，涨粉 25。",
                summary="大龄程序员职业危机选题评论强，开头有效，但完播偏弱。",
                metadata={"topicCluster": "大龄程序员职业危机", "finishRate": 0.113454},
                source_type="seed",
                source_ids=["7585913482206383412"],
                confidence=0.78,
                evidence_count=1,
                status="active",
                created_at=self._now_iso(),
                updated_at=self._now_iso(),
            ),
            MemoryRecord(
                id="mem_search_demo",
                workspace_id="ws_northstar",
                account_id="douyin_demo",
                platform="douyin",
                memory_type="search_intent",
                title="程序员三条职业发展路线",
                content="用户搜索意图偏职业规划、转型路线、AI 替代焦虑，适合清单式和路线图表达。",
                summary="围绕普通程序员、AI 替代、职业路线组织标题和简介。",
                metadata={"topicCluster": "职业规划"},
                source_type="seed",
                source_ids=[],
                confidence=0.82,
                evidence_count=2,
                status="active",
                created_at=self._now_iso(),
                updated_at=self._now_iso(),
            ),
        ]
        self.runs: Dict[str, AgentRunRecord] = {}
        self.steps: List[AgentRunStepRecord] = []
        self.traces: List[Dict[str, Any]] = []
        self.summaries: Dict[str, AgentThreadSummaryRecord] = {}
        self._step_id = 1
        self._trace_id = 1

    def _now_iso(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def create_memory(self, payload: MemoryRecordCreate) -> MemoryRecord:
        timestamp = self._now_iso()
        record = MemoryRecord(
            id=f"mem_{uuid4().hex[:10]}",
            workspace_id=payload.workspace_id,
            account_id=payload.account_id,
            platform=payload.platform,
            memory_type=payload.memory_type,
            title=payload.title,
            content=payload.content,
            summary=payload.summary,
            metadata=payload.metadata,
            source_type=payload.source_type,
            source_ids=payload.source_ids,
            confidence=payload.confidence,
            evidence_count=payload.evidence_count,
            status=payload.status,
            created_at=timestamp,
            updated_at=timestamp,
        )
        self.memories.insert(0, record)
        return record

    def list_memories(self) -> List[MemoryRecord]:
        return self.memories

    def update_memory(self, memory_id: str, payload: MemoryRecordUpdate) -> Optional[MemoryRecord]:
        for index, record in enumerate(self.memories):
            if record.id == memory_id:
                data = record.model_dump(by_alias=False)
                updates = payload.model_dump(exclude_unset=True, by_alias=False)
                data.update(updates)
                data["updated_at"] = self._now_iso()
                updated = MemoryRecord(**data)
                self.memories[index] = updated
                return updated
        return None

    def transition_memory(self, memory_id: str, status: str) -> Optional[MemoryRecord]:
        return self.update_memory(memory_id, MemoryRecordUpdate(status=status))

    def create_run(self, thread_id: str, workflow: str, input_payload: Dict[str, Any]) -> AgentRunRecord:
        run = AgentRunRecord(
            id=f"run_{uuid4().hex[:10]}",
            thread_id=thread_id,
            workflow=workflow,
            status="running",
            graph_version="v0.1",
            input=input_payload,
            output=None,
            error=None,
        )
        self.runs[run.id] = run
        return run

    def finish_run(self, run_id: str, output: Dict[str, Any]) -> AgentRunRecord:
        run = self.runs[run_id]
        updated = AgentRunRecord(**{**run.model_dump(by_alias=False), "status": "succeeded", "output": output})
        self.runs[run_id] = updated
        return updated

    def fail_run(self, run_id: str, error: str) -> AgentRunRecord:
        run = self.runs[run_id]
        updated = AgentRunRecord(**{**run.model_dump(by_alias=False), "status": "failed", "error": error})
        self.runs[run_id] = updated
        return updated

    def add_step(self, run_id: str, node_name: str, input_snapshot: Dict[str, Any], output_snapshot: Dict[str, Any]) -> AgentRunStepRecord:
        step = AgentRunStepRecord(
            id=self._step_id,
            run_id=run_id,
            node_name=node_name,
            input_snapshot=input_snapshot,
            output_snapshot=output_snapshot,
        )
        self._step_id += 1
        self.steps.append(step)
        return step

    def add_trace(self, run_id: str, query: str, memory_types: List[str], filters: Dict[str, Any], top_k: int, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        trace = {
            "id": self._trace_id,
            "runId": run_id,
            "query": query,
            "memoryTypes": memory_types,
            "filters": filters,
            "topK": top_k,
            "results": results,
        }
        self._trace_id += 1
        self.traces.append(trace)
        return trace

    def get_run(self, run_id: str) -> Optional[AgentRunRecord]:
        return self.runs.get(run_id)

    def get_steps(self, run_id: str) -> List[AgentRunStepRecord]:
        return [step for step in self.steps if step.run_id == run_id]

    def get_traces(self, run_id: str) -> List[Dict[str, Any]]:
        return [trace for trace in self.traces if trace["runId"] == run_id]

    def get_summary(self, thread_id: str) -> Optional[AgentThreadSummaryRecord]:
        return self.summaries.get(thread_id)

    def save_summary(self, thread_id: str, workspace_id: str, member_id: str, account_id: str, summary: str, decisions: List[Any], rejected_ideas: List[Any], pending_tasks: List[Any]) -> AgentThreadSummaryRecord:
        record = AgentThreadSummaryRecord(
            thread_id=thread_id,
            workspace_id=workspace_id,
            member_id=member_id,
            account_id=account_id,
            summary=summary,
            decisions=decisions,
            rejected_ideas=rejected_ideas,
            pending_tasks=pending_tasks,
        )
        self.summaries[thread_id] = record
        return record


agent_store = AgentStoreService()
