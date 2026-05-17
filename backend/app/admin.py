from pathlib import Path

from fastapi import FastAPI
from sqladmin import Admin, ModelView

from app.core.admin_auth import ADMIN_SESSION_KEY, AdminAuthBackend, admin_role_permissions
from app.core.config import get_settings
from app.db.models import (
    AIGeneration,
    AgentMemoryRecord,
    AgentRetrievalTrace,
    AgentRun,
    AgentRunStep,
    AgentThreadSummary,
    Base,
    CollectorTask,
    ContentItem,
    ContentKeyword,
    ContentLifetimeMetric,
    ContentTag,
    ContentTextAsset,
    ContentTrafficSource,
    MemoryPattern,
    PlatformAccount,
    PublishPlan,
    ScriptDraft,
    ScriptDraftVersion,
    TopicIdea,
    User,
    Workspace,
    WorkspaceMember,
)
from app.db.session import get_admin_engine


ADMIN_TEMPLATES_DIR = Path(__file__).parent / "templates"

ADMIN_COLUMN_LABELS = {
    "id": "编号",
    "thread_id": "会话编号",
    "workspace_id": "工作区编号",
    "user_id": "用户编号",
    "member_id": "成员编号",
    "account_id": "账号编号",
    "platform_account_id": "平台账号编号",
    "topic_idea_id": "选题编号",
    "run_id": "运行编号",
    "name": "名称",
    "email": "邮箱",
    "role": "角色",
    "is_active": "是否启用",
    "description": "描述",
    "status": "状态",
    "platform": "平台",
    "account_name": "账号名称",
    "external_account_id": "外部账号编号",
    "external_content_id": "外部内容编号",
    "title": "标题",
    "body": "正文",
    "draft_id": "脚本草稿编号",
    "version_no": "版本号",
    "label": "版本名称",
    "duration_seconds": "时长秒数",
    "title_candidates": "标题候选",
    "parent_version_id": "父版本编号",
    "current_version_id": "当前版本编号",
    "adopted_version_id": "采用版本编号",
    "content_type": "内容类型",
    "cover_url": "封面 URL",
    "video_url": "视频 URL",
    "topic_cluster_id": "主题簇编号",
    "raw_collection": "Raw 集合",
    "raw_document_id": "Raw 文档编号",
    "asset_type": "文本类型",
    "language": "语言",
    "segments": "分段",
    "tag": "标签",
    "tag_type": "标签类型",
    "external_tag_id": "外部标签编号",
    "position_start": "起始位置",
    "position_end": "结束位置",
    "keyword": "关键词",
    "keyword_type": "关键词类型",
    "query_count_7d": "7 日搜索量",
    "source_name": "来源名称",
    "source_type": "来源类型",
    "ratio": "占比",
    "count": "数量",
    "raw_payload": "Raw 数据",
    "published_at": "发布时间",
    "duration_seconds": "时长秒数",
    "views": "播放量",
    "likes": "点赞数",
    "comments": "评论数",
    "saves": "收藏数",
    "shares": "分享数",
    "completion_rate": "完播率",
    "followers_gained": "新增粉丝",
    "score": "评分",
    "has_asr": "是否有转写",
    "reviewed": "是否复盘",
    "content_id": "内容编号",
    "play_count": "播放量",
    "like_count": "点赞数",
    "comment_count": "评论数",
    "share_count": "分享数",
    "collect_count": "收藏数",
    "follow_count": "新增粉丝",
    "profile_visit_count": "主页访问",
    "avg_view_duration": "平均观看时长",
    "avg_view_percent": "平均观看占比",
    "finish_rate": "完播率",
    "five_second_retention": "5 秒留存",
    "bounce_rate": "跳出率",
    "negative_feedback_count": "负反馈数",
    "metric_score": "指标评分",
    "angle": "切入角度",
    "topic": "主题",
    "category": "分类",
    "target_audience": "目标受众",
    "platforms": "平台列表",
    "predicted_score": "预测评分",
    "seo_score": "搜索评分",
    "audience_score": "受众评分",
    "difficulty_score": "难度评分",
    "risk": "风险",
    "recommend_reason": "推荐理由",
    "generation_id": "生成批次",
    "workflow": "工作流",
    "provider": "模型供应商",
    "model": "模型",
    "prompt_version": "提示词版本",
    "input_payload": "输入",
    "output_payload": "输出",
    "error": "错误",
    "scheduled_at": "计划发布时间",
    "stage": "阶段",
    "type": "类型",
    "summary": "摘要",
    "confidence": "置信度",
    "source_count": "来源数量",
    "last_verified_at": "最近验证时间",
    "progress": "进度",
    "current_step": "当前步骤",
    "trace_id": "追踪编号",
    "memory_type": "记忆类型",
    "content": "内容",
    "meta_data": "元数据",
    "source_type": "来源类型",
    "source_ids": "来源编号",
    "evidence_count": "证据数量",
    "last_validated_at": "最近校验时间",
    "decisions": "决策记录",
    "rejected_ideas": "已拒绝选题",
    "pending_tasks": "待办任务",
    "workflow": "工作流",
    "graph_version": "图版本",
    "input_payload": "输入数据",
    "output_payload": "输出数据",
    "error": "错误",
    "node_name": "节点名称",
    "input_snapshot": "输入快照",
    "output_snapshot": "输出快照",
    "started_at": "开始时间",
    "finished_at": "结束时间",
    "query": "查询",
    "memory_types": "记忆类型",
    "filters": "筛选条件",
    "top_k": "返回数量",
    "results": "结果",
    "created_at": "创建时间",
    "updated_at": "更新时间",
}


class ChineseModelView(ModelView):
    column_labels = ADMIN_COLUMN_LABELS


class AdminPermissionMixin:
    def is_accessible(self, request) -> bool:
        try:
            session = request.session
        except AssertionError:
            return True
        if not session:
            return True
        user = session.get(ADMIN_SESSION_KEY)
        return isinstance(user, dict) and bool(user.get("role"))

    def is_visible(self, request) -> bool:
        return self.is_accessible(request)


class WorkspaceAdmin(AdminPermissionMixin, ChineseModelView, model=Workspace):
    name = "工作区"
    name_plural = "工作区"
    icon = "fa-solid fa-layer-group"
    column_list = [Workspace.id, Workspace.name, Workspace.status, Workspace.created_at]
    column_searchable_list = [Workspace.id, Workspace.name]


class UserAdmin(AdminPermissionMixin, ChineseModelView, model=User):
    name = "用户"
    name_plural = "用户"
    icon = "fa-solid fa-user"
    column_list = [User.id, User.email, User.name, User.role, User.is_active]
    column_searchable_list = [User.email, User.name]


class WorkspaceMemberAdmin(AdminPermissionMixin, ChineseModelView, model=WorkspaceMember):
    name = "工作区成员"
    name_plural = "工作区成员"
    icon = "fa-solid fa-users"
    column_list = [WorkspaceMember.id, WorkspaceMember.workspace_id, WorkspaceMember.user_id, WorkspaceMember.role]


class PlatformAccountAdmin(AdminPermissionMixin, ChineseModelView, model=PlatformAccount):
    name = "平台账号"
    name_plural = "平台账号"
    icon = "fa-solid fa-link"
    column_list = [PlatformAccount.id, PlatformAccount.workspace_id, PlatformAccount.platform, PlatformAccount.account_name, PlatformAccount.status]
    column_searchable_list = [PlatformAccount.account_name, PlatformAccount.external_account_id]


class ContentItemAdmin(AdminPermissionMixin, ChineseModelView, model=ContentItem):
    name = "内容"
    name_plural = "内容"
    icon = "fa-solid fa-video"
    column_list = [ContentItem.id, ContentItem.platform, ContentItem.title, ContentItem.status, ContentItem.views, ContentItem.score, ContentItem.published_at]
    column_searchable_list = [ContentItem.id, ContentItem.title, ContentItem.external_content_id]
    column_sortable_list = [ContentItem.views, ContentItem.score, ContentItem.published_at]


class ContentLifetimeMetricAdmin(AdminPermissionMixin, ChineseModelView, model=ContentLifetimeMetric):
    name = "内容累计指标"
    name_plural = "内容累计指标"
    icon = "fa-solid fa-chart-line"
    column_list = [
        ContentLifetimeMetric.content_id,
        ContentLifetimeMetric.play_count,
        ContentLifetimeMetric.like_count,
        ContentLifetimeMetric.comment_count,
        ContentLifetimeMetric.collect_count,
        ContentLifetimeMetric.metric_score,
        ContentLifetimeMetric.updated_at,
    ]
    column_sortable_list = [ContentLifetimeMetric.play_count, ContentLifetimeMetric.metric_score, ContentLifetimeMetric.updated_at]


class ContentTextAssetAdmin(AdminPermissionMixin, ChineseModelView, model=ContentTextAsset):
    name = "内容文本资产"
    name_plural = "内容文本资产"
    icon = "fa-solid fa-align-left"
    column_list = [ContentTextAsset.id, ContentTextAsset.content_id, ContentTextAsset.asset_type, ContentTextAsset.language, ContentTextAsset.source, ContentTextAsset.updated_at]
    column_searchable_list = [ContentTextAsset.content_id, ContentTextAsset.text]
    column_sortable_list = [ContentTextAsset.updated_at]


class ContentTagAdmin(AdminPermissionMixin, ChineseModelView, model=ContentTag):
    name = "内容标签"
    name_plural = "内容标签"
    icon = "fa-solid fa-tags"
    column_list = [ContentTag.id, ContentTag.content_id, ContentTag.tag, ContentTag.tag_type, ContentTag.source, ContentTag.updated_at]
    column_searchable_list = [ContentTag.content_id, ContentTag.tag]
    column_sortable_list = [ContentTag.updated_at]


class ContentKeywordAdmin(AdminPermissionMixin, ChineseModelView, model=ContentKeyword):
    name = "内容关键词"
    name_plural = "内容关键词"
    icon = "fa-solid fa-key"
    column_list = [ContentKeyword.id, ContentKeyword.content_id, ContentKeyword.keyword, ContentKeyword.keyword_type, ContentKeyword.query_count_7d, ContentKeyword.score]
    column_searchable_list = [ContentKeyword.content_id, ContentKeyword.keyword]
    column_sortable_list = [ContentKeyword.query_count_7d, ContentKeyword.score]


class ContentTrafficSourceAdmin(AdminPermissionMixin, ChineseModelView, model=ContentTrafficSource):
    name = "内容流量来源"
    name_plural = "内容流量来源"
    icon = "fa-solid fa-route"
    column_list = [ContentTrafficSource.id, ContentTrafficSource.content_id, ContentTrafficSource.source_name, ContentTrafficSource.source_type, ContentTrafficSource.ratio, ContentTrafficSource.count]
    column_searchable_list = [ContentTrafficSource.content_id, ContentTrafficSource.source_name]
    column_sortable_list = [ContentTrafficSource.ratio, ContentTrafficSource.count]


class TopicIdeaAdmin(AdminPermissionMixin, ChineseModelView, model=TopicIdea):
    name = "选题"
    name_plural = "选题"
    icon = "fa-solid fa-lightbulb"
    column_list = [TopicIdea.id, TopicIdea.title, TopicIdea.category, TopicIdea.predicted_score, TopicIdea.status, TopicIdea.created_at]
    column_searchable_list = [TopicIdea.title]


class AIGenerationAdmin(AdminPermissionMixin, ChineseModelView, model=AIGeneration):
    name = "AI 生成记录"
    name_plural = "AI 生成记录"
    icon = "fa-solid fa-wand-magic-sparkles"
    column_list = [AIGeneration.id, AIGeneration.workflow, AIGeneration.provider, AIGeneration.status, AIGeneration.created_at]
    column_searchable_list = [AIGeneration.id, AIGeneration.workflow]


class ScriptDraftAdmin(AdminPermissionMixin, ChineseModelView, model=ScriptDraft):
    name = "脚本草稿"
    name_plural = "脚本草稿"
    icon = "fa-solid fa-file-lines"
    column_list = [ScriptDraft.id, ScriptDraft.title, ScriptDraft.platform, ScriptDraft.status, ScriptDraft.current_version_id, ScriptDraft.updated_at]
    column_searchable_list = [ScriptDraft.title]


class ScriptDraftVersionAdmin(AdminPermissionMixin, ChineseModelView, model=ScriptDraftVersion):
    name = "脚本版本"
    name_plural = "脚本版本"
    icon = "fa-solid fa-code-branch"
    column_list = [
        ScriptDraftVersion.id,
        ScriptDraftVersion.draft_id,
        ScriptDraftVersion.version_no,
        ScriptDraftVersion.label,
        ScriptDraftVersion.source_type,
        ScriptDraftVersion.status,
        ScriptDraftVersion.created_at,
    ]
    column_searchable_list = [ScriptDraftVersion.id, ScriptDraftVersion.draft_id, ScriptDraftVersion.label]


class PublishPlanAdmin(AdminPermissionMixin, ChineseModelView, model=PublishPlan):
    name = "发布计划"
    name_plural = "发布计划"
    icon = "fa-solid fa-calendar"
    column_list = [PublishPlan.id, PublishPlan.title, PublishPlan.platform, PublishPlan.stage, PublishPlan.scheduled_at]
    column_sortable_list = [PublishPlan.scheduled_at]


class MemoryPatternAdmin(AdminPermissionMixin, ChineseModelView, model=MemoryPattern):
    name = "记忆模式"
    name_plural = "记忆模式"
    icon = "fa-solid fa-brain"
    column_list = [MemoryPattern.id, MemoryPattern.type, MemoryPattern.confidence, MemoryPattern.source_count, MemoryPattern.last_verified_at]
    column_searchable_list = [MemoryPattern.summary]


class CollectorTaskAdmin(AdminPermissionMixin, ChineseModelView, model=CollectorTask):
    name = "采集任务"
    name_plural = "采集任务"
    icon = "fa-solid fa-cloud-arrow-down"
    column_list = [CollectorTask.id, CollectorTask.platform, CollectorTask.name, CollectorTask.status, CollectorTask.progress, CollectorTask.updated_at]
    column_sortable_list = [CollectorTask.updated_at, CollectorTask.progress]


class AgentMemoryRecordAdmin(AdminPermissionMixin, ChineseModelView, model=AgentMemoryRecord):
    name = "智能体记忆"
    name_plural = "智能体记忆"
    icon = "fa-solid fa-database"
    column_list = [AgentMemoryRecord.id, AgentMemoryRecord.memory_type, AgentMemoryRecord.status, AgentMemoryRecord.confidence, AgentMemoryRecord.updated_at]
    column_searchable_list = [AgentMemoryRecord.title, AgentMemoryRecord.summary]


class AgentThreadSummaryAdmin(AdminPermissionMixin, ChineseModelView, model=AgentThreadSummary):
    name = "会话摘要"
    name_plural = "会话摘要"
    icon = "fa-solid fa-diagram-project"
    column_list = [AgentThreadSummary.thread_id, AgentThreadSummary.workspace_id, AgentThreadSummary.member_id, AgentThreadSummary.updated_at]


class AgentRunAdmin(AdminPermissionMixin, ChineseModelView, model=AgentRun):
    name = "智能体运行"
    name_plural = "智能体运行"
    icon = "fa-solid fa-robot"
    column_list = [AgentRun.id, AgentRun.thread_id, AgentRun.workflow, AgentRun.status, AgentRun.created_at]
    column_searchable_list = [AgentRun.id, AgentRun.thread_id]


class AgentRunStepAdmin(AdminPermissionMixin, ChineseModelView, model=AgentRunStep):
    name = "运行步骤"
    name_plural = "运行步骤"
    icon = "fa-solid fa-list-check"
    column_list = [AgentRunStep.id, AgentRunStep.run_id, AgentRunStep.node_name, AgentRunStep.started_at, AgentRunStep.finished_at]


class AgentRetrievalTraceAdmin(AdminPermissionMixin, ChineseModelView, model=AgentRetrievalTrace):
    name = "检索追踪"
    name_plural = "检索追踪"
    icon = "fa-solid fa-magnifying-glass-chart"
    column_list = [AgentRetrievalTrace.id, AgentRetrievalTrace.run_id, AgentRetrievalTrace.top_k, AgentRetrievalTrace.created_at]


ADMIN_MODEL_VIEWS = [
    WorkspaceAdmin,
    UserAdmin,
    WorkspaceMemberAdmin,
    PlatformAccountAdmin,
    ContentItemAdmin,
    TopicIdeaAdmin,
    AIGenerationAdmin,
    ScriptDraftAdmin,
    ScriptDraftVersionAdmin,
    PublishPlanAdmin,
    MemoryPatternAdmin,
    CollectorTaskAdmin,
    ContentLifetimeMetricAdmin,
    ContentTextAssetAdmin,
    ContentTagAdmin,
    ContentKeywordAdmin,
    ContentTrafficSourceAdmin,
    AgentMemoryRecordAdmin,
    AgentThreadSummaryAdmin,
    AgentRunAdmin,
    AgentRunStepAdmin,
    AgentRetrievalTraceAdmin,
]


def build_sqladmin_auth_backend() -> AdminAuthBackend | None:
    settings = get_settings()
    if not settings.sqladmin_auth_enabled:
        return None

    if not settings.sqladmin_username or not settings.sqladmin_session_secret:
        return AdminAuthBackend(secret_key="sqladmin-auth-not-configured", username="", role="viewer")
    if not settings.sqladmin_password and not settings.sqladmin_password_sha256:
        return AdminAuthBackend(secret_key=settings.sqladmin_session_secret, username="", role="viewer")

    return AdminAuthBackend(
        secret_key=settings.sqladmin_session_secret,
        username=settings.sqladmin_username,
        password=settings.sqladmin_password,
        password_sha256=settings.sqladmin_password_sha256,
        role=settings.sqladmin_role,
    )


def apply_sqladmin_permissions() -> None:
    settings = get_settings()
    permissions = admin_role_permissions(settings.sqladmin_role)
    for view in ADMIN_MODEL_VIEWS:
        view.can_create = permissions["can_create"]
        view.can_edit = permissions["can_edit"]
        view.can_delete = permissions["can_delete"]
        view.can_export = permissions["can_export"]
        view.can_view_details = permissions["can_view_details"]


def setup_sqladmin(app: FastAPI) -> None:
    settings = get_settings()
    if not settings.sqladmin_enabled:
        return

    engine = get_admin_engine()
    if engine is None:
        return

    if settings.sqladmin_auto_create_tables:
        try:
            Base.metadata.create_all(engine)
        except Exception:
            return

    apply_sqladmin_permissions()
    try:
        admin = Admin(
            app,
            engine,
            title=settings.sqladmin_title,
            base_url=settings.sqladmin_base_url,
            templates_dir=str(ADMIN_TEMPLATES_DIR),
            authentication_backend=build_sqladmin_auth_backend(),
        )
    except Exception:
        return
    for view in ADMIN_MODEL_VIEWS:
        admin.add_view(view)
