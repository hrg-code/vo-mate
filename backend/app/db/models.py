from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, Float, Integer, JSON, String, Text, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class Workspace(Base, TimestampMixin):
    __tablename__ = "workspaces"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(32), default="active")


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    email: Mapped[Optional[str]] = mapped_column(String(255), unique=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(64), default="member")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class WorkspaceMember(Base, TimestampMixin):
    __tablename__ = "workspace_members"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    workspace_id: Mapped[str] = mapped_column(String(64), index=True)
    user_id: Mapped[str] = mapped_column(String(64), index=True)
    role: Mapped[str] = mapped_column(String(64), default="member")


class PlatformAccount(Base, TimestampMixin):
    __tablename__ = "platform_accounts"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    workspace_id: Mapped[str] = mapped_column(String(64), index=True)
    platform: Mapped[str] = mapped_column(String(32), index=True)
    account_name: Mapped[str] = mapped_column(String(255), nullable=False)
    external_account_id: Mapped[Optional[str]] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(32), default="active")


class ContentItem(Base, TimestampMixin):
    __tablename__ = "content_items"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    workspace_id: Mapped[str] = mapped_column(String(64), index=True)
    platform_account_id: Mapped[Optional[str]] = mapped_column(String(64), index=True)
    platform: Mapped[str] = mapped_column(String(32), index=True)
    external_content_id: Mapped[Optional[str]] = mapped_column(String(255), index=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(64), default="published")
    published_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), index=True)
    duration_seconds: Mapped[Optional[int]] = mapped_column(Integer)
    content_type: Mapped[Optional[str]] = mapped_column(String(64))
    cover_url: Mapped[Optional[str]] = mapped_column(Text)
    video_url: Mapped[Optional[str]] = mapped_column(Text)
    topic_cluster_id: Mapped[Optional[str]] = mapped_column(String(64), index=True)
    raw_collection: Mapped[Optional[str]] = mapped_column(String(128))
    raw_document_id: Mapped[Optional[str]] = mapped_column(String(255), index=True)
    views: Mapped[int] = mapped_column(Integer, default=0)
    likes: Mapped[int] = mapped_column(Integer, default=0)
    comments: Mapped[int] = mapped_column(Integer, default=0)
    saves: Mapped[int] = mapped_column(Integer, default=0)
    shares: Mapped[int] = mapped_column(Integer, default=0)
    completion_rate: Mapped[Optional[float]] = mapped_column(Float)
    followers_gained: Mapped[int] = mapped_column(Integer, default=0)
    score: Mapped[Optional[float]] = mapped_column(Float)
    has_asr: Mapped[bool] = mapped_column(Boolean, default=False)
    reviewed: Mapped[bool] = mapped_column(Boolean, default=False)


class ContentLifetimeMetric(Base):
    __tablename__ = "content_lifetime_metrics"

    content_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    play_count: Mapped[int] = mapped_column(Integer, default=0)
    like_count: Mapped[int] = mapped_column(Integer, default=0)
    comment_count: Mapped[int] = mapped_column(Integer, default=0)
    share_count: Mapped[int] = mapped_column(Integer, default=0)
    collect_count: Mapped[int] = mapped_column(Integer, default=0)
    follow_count: Mapped[int] = mapped_column(Integer, default=0)
    profile_visit_count: Mapped[int] = mapped_column(Integer, default=0)
    avg_view_duration: Mapped[Optional[float]] = mapped_column(Float)
    avg_view_percent: Mapped[Optional[float]] = mapped_column(Float)
    finish_rate: Mapped[Optional[float]] = mapped_column(Float)
    five_second_retention: Mapped[Optional[float]] = mapped_column(Float)
    bounce_rate: Mapped[Optional[float]] = mapped_column(Float)
    negative_feedback_count: Mapped[int] = mapped_column(Integer, default=0)
    metric_score: Mapped[Optional[float]] = mapped_column(Float)
    raw_document_id: Mapped[Optional[str]] = mapped_column(String(255), index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class ContentTextAsset(Base, TimestampMixin):
    __tablename__ = "content_text_assets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    content_id: Mapped[str] = mapped_column(String(64), index=True)
    asset_type: Mapped[str] = mapped_column(String(64), index=True)
    text: Mapped[str] = mapped_column(Text, default="")
    language: Mapped[Optional[str]] = mapped_column(String(32))
    segments: Mapped[list] = mapped_column(JSON, default=list)
    raw_collection: Mapped[Optional[str]] = mapped_column(String(128))
    raw_document_id: Mapped[Optional[str]] = mapped_column(String(255), index=True)
    source: Mapped[Optional[str]] = mapped_column(String(128), index=True)


class ContentTag(Base, TimestampMixin):
    __tablename__ = "content_tags"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    content_id: Mapped[str] = mapped_column(String(64), index=True)
    tag: Mapped[str] = mapped_column(String(255), index=True)
    tag_type: Mapped[str] = mapped_column(String(64), default="topic")
    external_tag_id: Mapped[Optional[str]] = mapped_column(String(255), index=True)
    source: Mapped[Optional[str]] = mapped_column(String(128), index=True)
    position_start: Mapped[Optional[int]] = mapped_column(Integer)
    position_end: Mapped[Optional[int]] = mapped_column(Integer)


class ContentKeyword(Base, TimestampMixin):
    __tablename__ = "content_keywords"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    content_id: Mapped[str] = mapped_column(String(64), index=True)
    keyword: Mapped[str] = mapped_column(String(255), index=True)
    keyword_type: Mapped[str] = mapped_column(String(64), default="search")
    score: Mapped[Optional[float]] = mapped_column(Float)
    query_count_7d: Mapped[Optional[int]] = mapped_column(Integer)
    source: Mapped[Optional[str]] = mapped_column(String(128), index=True)


class ContentTrafficSource(Base, TimestampMixin):
    __tablename__ = "content_traffic_sources"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    content_id: Mapped[str] = mapped_column(String(64), index=True)
    source_name: Mapped[str] = mapped_column(String(255), index=True)
    source_type: Mapped[str] = mapped_column(String(64), default="traffic")
    ratio: Mapped[Optional[float]] = mapped_column(Float)
    count: Mapped[Optional[int]] = mapped_column(Integer)
    raw_payload: Mapped[dict] = mapped_column(JSON, default=dict)


class TopicIdea(Base, TimestampMixin):
    __tablename__ = "topic_ideas"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    workspace_id: Mapped[str] = mapped_column(String(64), index=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    topic: Mapped[Optional[str]] = mapped_column(String(255))
    angle: Mapped[Optional[str]] = mapped_column(Text)
    category: Mapped[Optional[str]] = mapped_column(String(128), index=True)
    target_audience: Mapped[Optional[str]] = mapped_column(String(255))
    platforms: Mapped[list] = mapped_column(JSON, default=list)
    predicted_score: Mapped[Optional[float]] = mapped_column(Float)
    seo_score: Mapped[Optional[float]] = mapped_column(Float)
    audience_score: Mapped[Optional[float]] = mapped_column(Float)
    difficulty_score: Mapped[Optional[float]] = mapped_column(Float)
    risk: Mapped[Optional[str]] = mapped_column(Text)
    recommend_reason: Mapped[Optional[str]] = mapped_column(Text)
    evidence: Mapped[list] = mapped_column(JSON, default=list)
    suggested_titles: Mapped[list] = mapped_column(JSON, default=list)
    suggested_hooks: Mapped[list] = mapped_column(JSON, default=list)
    suggested_tags: Mapped[list] = mapped_column(JSON, default=list)
    next_actions: Mapped[list] = mapped_column(JSON, default=list)
    generation_id: Mapped[Optional[str]] = mapped_column(String(64), index=True)
    source_payload: Mapped[dict] = mapped_column(JSON, default=dict)
    status: Mapped[str] = mapped_column(String(64), default="idea")


class AIGeneration(Base, TimestampMixin):
    __tablename__ = "ai_generations"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    workspace_id: Mapped[str] = mapped_column(String(64), index=True)
    workflow: Mapped[str] = mapped_column(String(64), index=True)
    provider: Mapped[str] = mapped_column(String(64), default="mock")
    model: Mapped[Optional[str]] = mapped_column(String(128))
    prompt_version: Mapped[str] = mapped_column(String(32), default="v0.1")
    input_payload: Mapped[dict] = mapped_column(JSON, default=dict)
    evidence_ids: Mapped[list] = mapped_column(JSON, default=list)
    output_payload: Mapped[Optional[dict]] = mapped_column(JSON)
    error: Mapped[Optional[str]] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(32), default="succeeded", index=True)


class ScriptDraft(Base, TimestampMixin):
    __tablename__ = "script_drafts"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    workspace_id: Mapped[str] = mapped_column(String(64), index=True)
    topic_idea_id: Mapped[Optional[str]] = mapped_column(String(64), index=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    body: Mapped[Optional[str]] = mapped_column(Text)
    platform: Mapped[Optional[str]] = mapped_column(String(32))
    status: Mapped[str] = mapped_column(String(64), default="draft")
    current_version_id: Mapped[Optional[str]] = mapped_column(String(64), index=True)
    adopted_version_id: Mapped[Optional[str]] = mapped_column(String(64), index=True)


class ScriptDraftVersion(Base, TimestampMixin):
    __tablename__ = "script_draft_versions"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    draft_id: Mapped[str] = mapped_column(String(64), index=True)
    version_no: Mapped[int] = mapped_column(Integer, default=1)
    label: Mapped[str] = mapped_column(String(255), nullable=False)
    platform: Mapped[Optional[str]] = mapped_column(String(32))
    duration_seconds: Mapped[Optional[int]] = mapped_column(Integer)
    body: Mapped[str] = mapped_column(Text, default="")
    blocks: Mapped[list] = mapped_column(JSON, default=list)
    description: Mapped[Optional[str]] = mapped_column(Text)
    tags: Mapped[list] = mapped_column(JSON, default=list)
    title_candidates: Mapped[list] = mapped_column(JSON, default=list)
    source_type: Mapped[str] = mapped_column(String(64), default="user_save", index=True)
    parent_version_id: Mapped[Optional[str]] = mapped_column(String(64), index=True)
    generation_id: Mapped[Optional[str]] = mapped_column(String(64), index=True)
    status: Mapped[str] = mapped_column(String(64), default="candidate", index=True)


class PublishPlan(Base, TimestampMixin):
    __tablename__ = "publish_plans"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    workspace_id: Mapped[str] = mapped_column(String(64), index=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    platform: Mapped[str] = mapped_column(String(32), index=True)
    scheduled_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), index=True)
    stage: Mapped[str] = mapped_column(String(64), default="idea")


class MemoryPattern(Base, TimestampMixin):
    __tablename__ = "memory_patterns"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    workspace_id: Mapped[str] = mapped_column(String(64), index=True)
    type: Mapped[str] = mapped_column(String(64), index=True)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    confidence: Mapped[Optional[float]] = mapped_column(Float)
    source_count: Mapped[int] = mapped_column(Integer, default=0)
    last_verified_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))


class CollectorTask(Base, TimestampMixin):
    __tablename__ = "collector_tasks"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    workspace_id: Mapped[Optional[str]] = mapped_column(String(64), index=True)
    platform: Mapped[Optional[str]] = mapped_column(String(32), index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(64), default="pending")
    progress: Mapped[int] = mapped_column(Integer, default=0)
    current_step: Mapped[Optional[str]] = mapped_column(String(255))
    trace_id: Mapped[Optional[str]] = mapped_column(String(64))


class AgentMemoryRecord(Base, TimestampMixin):
    # L3/L4 智能体记忆事实表。
    # 保存完整结构化记录、证据链、生命周期状态和置信度。
    # Milvus 应通过记忆 ID 引用本表，而不是成为业务主存储。
    __tablename__ = "agent_memory_records"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    workspace_id: Mapped[str] = mapped_column(String(64), index=True)
    account_id: Mapped[str] = mapped_column(String(128), index=True)
    platform: Mapped[str] = mapped_column(String(32), index=True)
    memory_type: Mapped[str] = mapped_column(String(64), index=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    meta_data: Mapped[dict] = mapped_column("metadata", JSON, default=dict)
    source_type: Mapped[str] = mapped_column(String(64), default="manual")
    source_ids: Mapped[list] = mapped_column(JSON, default=list)
    confidence: Mapped[float] = mapped_column(Float, default=0.5)
    evidence_count: Mapped[int] = mapped_column(Integer, default=1)
    status: Mapped[str] = mapped_column(String(32), default="candidate", index=True)
    last_validated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))


class AgentThreadSummary(Base, TimestampMixin):
    # L1/L2 线程记忆表。
    # 一行表示一个内容任务或会话的可恢复工作摘要：
    # 当前摘要、已确认决策、已拒绝方向和待处理事项。
    __tablename__ = "agent_thread_summaries"

    thread_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    workspace_id: Mapped[str] = mapped_column(String(64), index=True)
    member_id: Mapped[str] = mapped_column(String(64), index=True)
    account_id: Mapped[str] = mapped_column(String(128), index=True)
    summary: Mapped[str] = mapped_column(Text, default="")
    decisions: Mapped[list] = mapped_column(JSON, default=list)
    rejected_ideas: Mapped[list] = mapped_column(JSON, default=list)
    pending_tasks: Mapped[list] = mapped_column(JSON, default=list)


class AgentRun(Base, TimestampMixin):
    # 单次智能体图执行的调试和审计记录。
    # 活跃的 L0 图状态是临时的，但运行记录和节点快照需要可追溯。
    __tablename__ = "agent_runs"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    thread_id: Mapped[str] = mapped_column(String(128), index=True)
    workflow: Mapped[str] = mapped_column(String(64), index=True)
    status: Mapped[str] = mapped_column(String(32), default="running", index=True)
    graph_version: Mapped[str] = mapped_column(String(32), default="v0.1")
    input_payload: Mapped[dict] = mapped_column(JSON, default=dict)
    output_payload: Mapped[Optional[dict]] = mapped_column(JSON)
    error: Mapped[Optional[str]] = mapped_column(Text)


class AgentRunStep(Base, TimestampMixin):
    # 节点级快照用于调试记忆行为：
    # 加载了什么上下文、召回了哪些记忆、生成或质检节点产出了什么。
    __tablename__ = "agent_run_steps"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    run_id: Mapped[str] = mapped_column(String(64), index=True)
    node_name: Mapped[str] = mapped_column(String(128), index=True)
    input_snapshot: Mapped[dict] = mapped_column(JSON, default=dict)
    output_snapshot: Mapped[dict] = mapped_column(JSON, default=dict)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))


class AgentRetrievalTrace(Base, TimestampMixin):
    # L3/L4 召回追踪表。保存查询、过滤条件、召回数量和返回的记忆 ID/分数，
    # 方便把异常生成结果追溯到具体召回输入和命中记忆。
    __tablename__ = "agent_retrieval_traces"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    run_id: Mapped[str] = mapped_column(String(64), index=True)
    query: Mapped[str] = mapped_column(Text, nullable=False)
    memory_types: Mapped[list] = mapped_column(JSON, default=list)
    filters: Mapped[dict] = mapped_column(JSON, default=dict)
    top_k: Mapped[int] = mapped_column(Integer, default=8)
    results: Mapped[list] = mapped_column(JSON, default=list)
