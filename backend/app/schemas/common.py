from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


class Platform(str, Enum):
    douyin = "douyin"
    kuaishou = "kuaishou"
    xiaohongshu = "xiaohongshu"
    youtube = "youtube"
    wechat = "wechat"


class TaskStatus(str, Enum):
    pending = "pending"
    running = "running"
    requires_action = "requires_action"
    succeeded = "succeeded"
    failed = "failed"
    cancelled = "cancelled"


class ContentStatus(str, Enum):
    published = "published"
    needs_review = "needs_review"
    script_reusable = "script_reusable"
    seo_opportunity = "seo_opportunity"


class WorkspaceContext(BaseModel):
    workspace_id: str = Field(serialization_alias="workspaceId")
    workspace_name: str = Field(serialization_alias="workspaceName")
    account_name: str = Field(serialization_alias="accountName")
    platform_scope: List[Platform] = Field(serialization_alias="platformScope")

    model_config = {"populate_by_name": True}


class MetricSummary(BaseModel):
    label: str
    value: str
    delta: str
    direction: str
    description: str


class ContentItem(BaseModel):
    id: str
    title: str
    platform: Platform
    published_at: str = Field(serialization_alias="publishedAt")
    duration_seconds: int = Field(serialization_alias="durationSeconds")
    views: int
    likes: int
    comments: int
    saves: int
    shares: int
    completion_rate: float = Field(serialization_alias="completionRate")
    followers_gained: int = Field(serialization_alias="followersGained")
    score: int
    status: ContentStatus
    has_asr: bool = Field(serialization_alias="hasAsr")
    reviewed: bool

    model_config = {"populate_by_name": True}


class TopicIdea(BaseModel):
    id: str
    title: str
    angle: str
    topic: Optional[str] = None
    category: Optional[str] = None
    target_audience: Optional[str] = Field(default=None, serialization_alias="targetAudience", validation_alias="targetAudience")
    predicted_score: int = Field(serialization_alias="predictedScore", validation_alias="predictedScore")
    seo_score: int = Field(serialization_alias="seoScore", validation_alias="seoScore")
    audience_score: int = Field(serialization_alias="audienceScore", validation_alias="audienceScore")
    difficulty_score: int = Field(serialization_alias="difficultyScore", validation_alias="difficultyScore")
    risk: str
    recommend_reason: Optional[str] = Field(default=None, serialization_alias="recommendReason", validation_alias="recommendReason")
    evidence_count: int = Field(serialization_alias="evidenceCount", validation_alias="evidenceCount")
    target_platforms: List[Platform] = Field(serialization_alias="targetPlatforms", validation_alias="targetPlatforms")
    evidence: List[Dict[str, Any]] = Field(default_factory=list)
    suggested_titles: List[str] = Field(default_factory=list, serialization_alias="suggestedTitles", validation_alias="suggestedTitles")
    suggested_hooks: List[str] = Field(default_factory=list, serialization_alias="suggestedHooks", validation_alias="suggestedHooks")
    suggested_tags: List[str] = Field(default_factory=list, serialization_alias="suggestedTags", validation_alias="suggestedTags")
    next_actions: List[str] = Field(default_factory=list, serialization_alias="nextActions", validation_alias="nextActions")
    generation_id: Optional[str] = Field(default=None, serialization_alias="generationId", validation_alias="generationId")

    model_config = {"populate_by_name": True}


class TopicIdeaGenerateRequest(BaseModel):
    workspace_id: str = Field(default="ws_northstar", serialization_alias="workspaceId", validation_alias="workspaceId")
    account_ids: List[str] = Field(
        default_factory=lambda: ["douyin_demo"],
        serialization_alias="accountIds",
        validation_alias="accountIds",
    )
    direction: str = Field(min_length=1)
    platforms: List[Platform] = Field(default_factory=lambda: [Platform.douyin])
    goal: str = "followers"
    count: int = Field(default=10, ge=1, le=20)
    audience: Optional[str] = None
    constraints: Dict[str, Any] = Field(default_factory=dict)
    include_evidence: bool = Field(default=True, serialization_alias="includeEvidence", validation_alias="includeEvidence")

    model_config = {"populate_by_name": True}

    @field_validator("direction")
    @classmethod
    def direction_must_not_be_blank(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("direction must not be blank")
        return stripped

    @field_validator("account_ids")
    @classmethod
    def account_ids_must_not_be_empty(cls, value: List[str]) -> List[str]:
        if not value:
            raise ValueError("accountIds must not be empty")
        return value


class EvidenceItem(BaseModel):
    id: str
    type: str
    title: str
    description: str
    source: str
    score: Optional[int] = None


class AIGenerationRecord(BaseModel):
    id: str
    workspace_id: str = Field(serialization_alias="workspaceId", validation_alias="workspaceId")
    workflow: str
    provider: str
    model: Optional[str] = None
    prompt_version: str = Field(serialization_alias="promptVersion", validation_alias="promptVersion")
    input_payload: Dict[str, Any] = Field(serialization_alias="inputPayload", validation_alias="inputPayload")
    evidence_ids: List[str] = Field(serialization_alias="evidenceIds", validation_alias="evidenceIds")
    output_payload: Optional[Dict[str, Any]] = Field(default=None, serialization_alias="outputPayload", validation_alias="outputPayload")
    error: Optional[str] = None
    status: str

    model_config = {"populate_by_name": True}


class AgentTask(BaseModel):
    id: str
    name: str
    status: TaskStatus
    progress: int
    current_step: str = Field(serialization_alias="currentStep")
    trace_id: str = Field(serialization_alias="traceId")
    result: Optional[Dict[str, Any]] = None

    model_config = {"populate_by_name": True}


class MemoryPattern(BaseModel):
    id: str
    type: str
    summary: str
    confidence: float
    source_count: int = Field(serialization_alias="sourceCount")
    last_verified_at: str = Field(serialization_alias="lastVerifiedAt")

    model_config = {"populate_by_name": True}


class PublishPlan(BaseModel):
    id: str
    title: str
    platform: Platform
    scheduled_at: str = Field(serialization_alias="scheduledAt")
    stage: str

    model_config = {"populate_by_name": True}
