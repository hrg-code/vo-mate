from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class AgentWorkbenchRequest(BaseModel):
    thread_id: str = Field(serialization_alias="threadId", validation_alias="threadId")
    workspace_id: str = Field(serialization_alias="workspaceId", validation_alias="workspaceId")
    member_id: str = Field(serialization_alias="memberId", validation_alias="memberId")
    account_id: str = Field(serialization_alias="accountId", validation_alias="accountId")
    platform: str = "douyin"
    task_type: str = Field(default="topic_to_qa", serialization_alias="taskType", validation_alias="taskType")
    topic: str
    target_duration_seconds: int = Field(default=45, serialization_alias="targetDurationSeconds", validation_alias="targetDurationSeconds")
    constraints: Dict[str, Any] = Field(default_factory=dict)

    model_config = {"populate_by_name": True}


class AgentEvidence(BaseModel):
    memory_id: str = Field(serialization_alias="memoryId")
    memory_type: str = Field(serialization_alias="memoryType")
    title: str
    summary: str
    score: float
    reason: str

    model_config = {"populate_by_name": True}


class AgentInference(BaseModel):
    claim: str
    reason: str


class TopicScores(BaseModel):
    persona_fit: int = Field(serialization_alias="personaFit")
    search_intent_score: int = Field(serialization_alias="searchIntentScore")
    historical_similarity_score: int = Field(serialization_alias="historicalSimilarityScore")
    retention_potential: int = Field(serialization_alias="retentionPotential")
    risk_penalty: int = Field(serialization_alias="riskPenalty")
    topic_score: int = Field(serialization_alias="topicScore")

    model_config = {"populate_by_name": True}


class AgentWorkbenchResponse(BaseModel):
    run_id: str = Field(serialization_alias="runId")
    thread_id: str = Field(serialization_alias="threadId")
    status: str
    topic_score: int = Field(serialization_alias="topicScore")
    scores: TopicScores
    strategy: Dict[str, Any]
    drafts: Dict[str, Any]
    qa_report: Dict[str, Any] = Field(serialization_alias="qaReport")
    evidence: List[AgentEvidence]
    inferences: List[AgentInference]

    model_config = {"populate_by_name": True}


class MemoryRecordCreate(BaseModel):
    workspace_id: str = Field(default="ws_northstar", serialization_alias="workspaceId", validation_alias="workspaceId")
    account_id: str = Field(default="douyin_demo", serialization_alias="accountId", validation_alias="accountId")
    platform: str = "douyin"
    memory_type: str = Field(serialization_alias="memoryType", validation_alias="memoryType")
    title: str
    content: str
    summary: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    source_type: str = Field(default="manual", serialization_alias="sourceType", validation_alias="sourceType")
    source_ids: List[str] = Field(default_factory=list, serialization_alias="sourceIds", validation_alias="sourceIds")
    confidence: float = 0.5
    evidence_count: int = Field(default=1, serialization_alias="evidenceCount", validation_alias="evidenceCount")
    status: str = "candidate"

    model_config = {"populate_by_name": True}


class MemoryRecordUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    summary: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    confidence: Optional[float] = None
    evidence_count: Optional[int] = Field(default=None, serialization_alias="evidenceCount", validation_alias="evidenceCount")
    status: Optional[str] = None

    model_config = {"populate_by_name": True}


class MemoryRecord(BaseModel):
    id: str
    workspace_id: str = Field(serialization_alias="workspaceId")
    account_id: str = Field(serialization_alias="accountId")
    platform: str
    memory_type: str = Field(serialization_alias="memoryType")
    title: str
    content: str
    summary: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    source_type: str = Field(serialization_alias="sourceType")
    source_ids: List[str] = Field(serialization_alias="sourceIds")
    confidence: float
    evidence_count: int = Field(serialization_alias="evidenceCount")
    status: str
    created_at: str = Field(serialization_alias="createdAt")
    updated_at: str = Field(serialization_alias="updatedAt")

    model_config = {"populate_by_name": True}


class MemorySearchRequest(BaseModel):
    query: str
    workspace_id: str = Field(default="ws_northstar", serialization_alias="workspaceId", validation_alias="workspaceId")
    account_id: str = Field(default="douyin_demo", serialization_alias="accountId", validation_alias="accountId")
    platform: str = "douyin"
    memory_types: List[str] = Field(default_factory=list, serialization_alias="memoryTypes", validation_alias="memoryTypes")
    status: str = "active"
    top_k: int = Field(default=8, serialization_alias="topK", validation_alias="topK")

    model_config = {"populate_by_name": True}


class MemorySearchResponse(BaseModel):
    query: str
    results: List[AgentEvidence]


class AgentRunRecord(BaseModel):
    id: str
    thread_id: str = Field(serialization_alias="threadId")
    workflow: str
    status: str
    graph_version: str = Field(serialization_alias="graphVersion")
    input: Dict[str, Any]
    output: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

    model_config = {"populate_by_name": True}


class AgentRunStepRecord(BaseModel):
    id: int
    run_id: str = Field(serialization_alias="runId")
    node_name: str = Field(serialization_alias="nodeName")
    input_snapshot: Dict[str, Any] = Field(serialization_alias="inputSnapshot")
    output_snapshot: Dict[str, Any] = Field(serialization_alias="outputSnapshot")

    model_config = {"populate_by_name": True}


class AgentRetrievalTraceRecord(BaseModel):
    id: int
    run_id: str = Field(serialization_alias="runId")
    query: str
    memory_types: List[str] = Field(serialization_alias="memoryTypes")
    filters: Dict[str, Any]
    top_k: int = Field(serialization_alias="topK")
    results: List[Dict[str, Any]]

    model_config = {"populate_by_name": True}


class AgentThreadSummaryRecord(BaseModel):
    thread_id: str = Field(serialization_alias="threadId")
    workspace_id: str = Field(serialization_alias="workspaceId")
    member_id: str = Field(serialization_alias="memberId")
    account_id: str = Field(serialization_alias="accountId")
    summary: str
    decisions: List[Any]
    rejected_ideas: List[Any] = Field(serialization_alias="rejectedIdeas")
    pending_tasks: List[Any] = Field(serialization_alias="pendingTasks")

    model_config = {"populate_by_name": True}

