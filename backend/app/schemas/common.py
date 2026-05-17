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


class ScriptVersionSourceType(str, Enum):
    ai_initial = "ai_initial"
    user_save = "user_save"
    ai_rewrite = "ai_rewrite"
    platform_adaptation = "platform_adaptation"


class ScriptVersionStatus(str, Enum):
    candidate = "candidate"
    adopted = "adopted"
    discarded = "discarded"


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
    #工作区 ID。用于限定从哪个 workspace 读取账号上下文、历史内容、记忆证据。
    workspace_id: str = Field(default="ws_northstar", serialization_alias="workspaceId", validation_alias="workspaceId")
    # 账号 ID 列表。不能为空。当前记忆召回主要用第一个账号 ID。
    account_ids: List[str] = Field(
        default_factory=lambda: ["douyin_demo"],
        serialization_alias="accountIds",
        validation_alias="accountIds",
    )
    # 选题方向 / 生成主题，比如 "程序员职业成长"。不能为空字符串，是生成选题的核心输入。
    direction: str = Field(min_length=1)
    # 目标平台范围。可选值见 Platform：douyin、kuaishou、xiaohongshu、youtube、wechat。
    platforms: List[Platform] = Field(default_factory=lambda: [Platform.douyin])
    # 本次选题目标，比如涨粉、转化、搜索流量、互动等。目前是自由字符串，会传给 AI/provider 和记忆召回查询。
    goal: str = "followers"
    # 希望生成几个选题。限制是 1 <= count <= 20。
    count: int = Field(default=10, ge=1, le=20)
    # 目标受众描述，比如 "25-35 岁普通程序员"。会影响候选选题的受众定位。
    audience: Optional[str] = None
    # 生成约束，自由 JSON。比如语气、禁忌话题、内容边界：{"tone":"理性但有冲突感","avoidTopics":["裁员恐慌"]}。
    constraints: Dict[str, Any] = Field(default_factory=dict)
    # 是否在 SSE 中返回证据，以及每个选题里是否带 evidence 字段。即使是 false，服务内部仍会召回证据辅助生成，只是不把证据暴露给前端。
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
    metrics: List[str] = Field(default_factory=list)
    action: Optional[str] = None


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


class ScriptDraftVersion(BaseModel):
    id: str
    draft_id: str = Field(serialization_alias="draftId", validation_alias="draftId")
    version_no: int = Field(serialization_alias="versionNo", validation_alias="versionNo")
    label: str
    platform: Optional[Platform] = None
    duration_seconds: Optional[int] = Field(default=None, serialization_alias="durationSeconds", validation_alias="durationSeconds")
    body: str
    description: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    title_candidates: List[Dict[str, Any]] = Field(default_factory=list, serialization_alias="titleCandidates", validation_alias="titleCandidates")
    source_type: ScriptVersionSourceType = Field(serialization_alias="sourceType", validation_alias="sourceType")
    parent_version_id: Optional[str] = Field(default=None, serialization_alias="parentVersionId", validation_alias="parentVersionId")
    generation_id: Optional[str] = Field(default=None, serialization_alias="generationId", validation_alias="generationId")
    status: ScriptVersionStatus = ScriptVersionStatus.candidate
    created_at: Optional[str] = Field(default=None, serialization_alias="createdAt", validation_alias="createdAt")

    model_config = {"populate_by_name": True}


class ScriptDraftSummary(BaseModel):
    id: str
    workspace_id: str = Field(serialization_alias="workspaceId", validation_alias="workspaceId")
    topic_idea_id: Optional[str] = Field(default=None, serialization_alias="topicIdeaId", validation_alias="topicIdeaId")
    title: str
    body: Optional[str] = None
    platform: Optional[Platform] = None
    status: str
    current_version_id: Optional[str] = Field(default=None, serialization_alias="currentVersionId", validation_alias="currentVersionId")
    adopted_version_id: Optional[str] = Field(default=None, serialization_alias="adoptedVersionId", validation_alias="adoptedVersionId")
    current_version: Optional[ScriptDraftVersion] = Field(default=None, serialization_alias="currentVersion", validation_alias="currentVersion")
    updated_at: Optional[str] = Field(default=None, serialization_alias="updatedAt", validation_alias="updatedAt")

    model_config = {"populate_by_name": True}


class ScriptDraftDetail(ScriptDraftSummary):
    versions: List[ScriptDraftVersion] = Field(default_factory=list)


class ScriptDraftCreateRequest(BaseModel):
    workspace_id: str = Field(default="ws_northstar", serialization_alias="workspaceId", validation_alias="workspaceId")
    topic_idea_id: Optional[str] = Field(default=None, serialization_alias="topicIdeaId", validation_alias="topicIdeaId")
    topic: str = Field(default="35 岁程序员不是危机，是岗位切换信号", min_length=1)
    title: Optional[str] = None
    platform: Platform = Platform.douyin
    duration_seconds: int = Field(default=60, ge=15, le=600, serialization_alias="durationSeconds", validation_alias="durationSeconds")

    model_config = {"populate_by_name": True}

    @field_validator("topic")
    @classmethod
    def topic_must_not_be_blank(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("topic must not be blank")
        return stripped


class ScriptDraftVersionCreateRequest(BaseModel):
    body: str = Field(min_length=1)
    label: Optional[str] = None
    platform: Optional[Platform] = None
    duration_seconds: Optional[int] = Field(default=None, ge=1, le=600, serialization_alias="durationSeconds", validation_alias="durationSeconds")
    description: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    title_candidates: List[Dict[str, Any]] = Field(default_factory=list, serialization_alias="titleCandidates", validation_alias="titleCandidates")
    source_type: ScriptVersionSourceType = Field(default=ScriptVersionSourceType.user_save, serialization_alias="sourceType", validation_alias="sourceType")
    parent_version_id: Optional[str] = Field(default=None, serialization_alias="parentVersionId", validation_alias="parentVersionId")

    model_config = {"populate_by_name": True}


class ScriptVersionStatusUpdateRequest(BaseModel):
    status: ScriptVersionStatus


class ScriptCurrentVersionUpdateRequest(BaseModel):
    version_id: str = Field(serialization_alias="versionId", validation_alias="versionId")

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


class CollectorImportRequest(BaseModel):
    workspace_id: str = Field(default="ws_northstar", serialization_alias="workspaceId", validation_alias="workspaceId")
    account_id: str = Field(default="douyin_demo", serialization_alias="accountId", validation_alias="accountId")
    platform: Platform = Platform.douyin
    collection: str = "douyin_video_raw"
    asr_collection: str = Field(default="douyin_video_asr_results", serialization_alias="asrCollection", validation_alias="asrCollection")
    include_asr: bool = Field(default=True, serialization_alias="includeAsr", validation_alias="includeAsr")
    limit: int = Field(default=100, ge=1, le=1000)

    model_config = {"populate_by_name": True}


class CollectorImportResponse(BaseModel):
    task_id: str = Field(serialization_alias="taskId", validation_alias="taskId")
    status: str
    processed_count: int = Field(serialization_alias="processedCount", validation_alias="processedCount")
    upserted_count: int = Field(serialization_alias="upsertedCount", validation_alias="upsertedCount")
    failed_count: int = Field(serialization_alias="failedCount", validation_alias="failedCount")
    text_asset_count: int = Field(default=0, serialization_alias="textAssetCount", validation_alias="textAssetCount")
    tag_count: int = Field(default=0, serialization_alias="tagCount", validation_alias="tagCount")
    keyword_count: int = Field(default=0, serialization_alias="keywordCount", validation_alias="keywordCount")
    traffic_source_count: int = Field(default=0, serialization_alias="trafficSourceCount", validation_alias="trafficSourceCount")
    asr_count: int = Field(default=0, serialization_alias="asrCount", validation_alias="asrCount")

    model_config = {"populate_by_name": True}


class ContentAsrResponse(BaseModel):
    content_id: str = Field(serialization_alias="contentId", validation_alias="contentId")
    text: str
    language: Optional[str] = None
    duration_seconds: Optional[float] = Field(default=None, serialization_alias="durationSeconds", validation_alias="durationSeconds")
    segments: List[Dict[str, Any]] = Field(default_factory=list)

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
