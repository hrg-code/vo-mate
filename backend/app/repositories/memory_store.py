from datetime import date
from typing import Any, Dict, List, Optional
from uuid import uuid4

from app.schemas.common import (
    AgentTask,
    ContentItem,
    ContentStatus,
    EvidenceItem,
    MemoryPattern,
    MetricSummary,
    Platform,
    PublishPlan,
    TaskStatus,
    TopicIdea,
    WorkspaceContext,
)


class InMemoryRepository:
    def __init__(self) -> None:
        self.workspace = WorkspaceContext(
            workspace_id="ws_northstar",
            workspace_name="北极星内容组",
            account_name="抖音 · 程序员老陈",
            platform_scope=[Platform.douyin],
        )
        self.metrics = [
            MetricSummary(label="播放量", value="34.6w", delta="+42%", direction="up", description="较账号 30 日中位数"),
            MetricSummary(label="互动率", value="7.8%", delta="+1.2%", direction="up", description="点赞、评论、收藏、分享综合"),
            MetricSummary(label="涨粉", value="1,286", delta="+36%", direction="up", description="本周期内容转化"),
            MetricSummary(label="完播率", value="38%", delta="-4%", direction="down", description="需检查开头与中段流失"),
            MetricSummary(label="搜索流量", value="21%", delta="+9%", direction="up", description="关键词承接机会增强"),
        ]
        self.contents = [
            ContentItem(
                id="ct_7585913482206383412",
                title="程序员 35 岁后还能不能继续写代码",
                platform=Platform.douyin,
                published_at="2026-05-08",
                duration_seconds=62,
                views=346000,
                likes=19000,
                comments=892,
                saves=4320,
                shares=1182,
                completion_rate=0.38,
                followers_gained=1286,
                score=89,
                status=ContentStatus.published,
                has_asr=True,
                reviewed=True,
            ),
            ContentItem(
                id="ct_resume_hr",
                title="为什么你的简历总被筛掉",
                platform=Platform.douyin,
                published_at="2026-05-06",
                duration_seconds=48,
                views=182000,
                likes=8431,
                comments=521,
                saves=2900,
                shares=803,
                completion_rate=0.42,
                followers_gained=604,
                score=82,
                status=ContentStatus.needs_review,
                has_asr=True,
                reviewed=False,
            ),
            ContentItem(
                id="ct_ai_three_chances",
                title="人工智能时代普通程序员的三个机会",
                platform=Platform.wechat,
                published_at="2026-05-04",
                duration_seconds=91,
                views=97000,
                likes=3126,
                comments=318,
                saves=1504,
                shares=512,
                completion_rate=0.31,
                followers_gained=298,
                score=76,
                status=ContentStatus.script_reusable,
                has_asr=True,
                reviewed=False,
            ),
            ContentItem(
                id="ct_outsource_truth",
                title="外包五年后我学到的残酷真相",
                platform=Platform.xiaohongshu,
                published_at="2026-05-02",
                duration_seconds=55,
                views=124000,
                likes=5980,
                comments=437,
                saves=3888,
                shares=760,
                completion_rate=0.45,
                followers_gained=781,
                score=86,
                status=ContentStatus.seo_opportunity,
                has_asr=True,
                reviewed=True,
            ),
        ]
        self.topic_ideas = [
            TopicIdea(
                id="tp_role_shift",
                title="35 岁程序员不是危机，是岗位切换信号",
                angle="把年龄焦虑改写成职业策略，适合 60 秒强钩子口播。",
                predicted_score=91,
                seo_score=86,
                audience_score=93,
                difficulty_score=41,
                risk="情绪过强会降低完播",
                evidence_count=12,
                target_platforms=[Platform.douyin, Platform.xiaohongshu],
            ),
            TopicIdea(
                id="tp_ai_task_split",
                title="AI 不会淘汰程序员，但会淘汰不会拆任务的人",
                angle="用真实项目拆解 AI 协作边界，承接近期搜索词。",
                predicted_score=87,
                seo_score=92,
                audience_score=84,
                difficulty_score=52,
                risk="需要避免泛泛讲工具",
                evidence_count=8,
                target_platforms=[Platform.douyin, Platform.wechat],
            ),
        ]
        self.evidence = [
            EvidenceItem(
                id="ev_content_1",
                type="content",
                title="程序员 35 岁后还能不能继续写代码",
                description="播放 34.6w，完播 38%，涨粉 1,286，相关性 94%。",
                source="业务内容表和抖音原始数据",
                score=94,
            ),
            EvidenceItem(
                id="ev_memory_1",
                type="memory",
                title="先承认焦虑，再给可执行步骤",
                description="来源于 9 条高收藏内容，适合抖音与小红书双平台改写。",
                source="创作者模式向量记忆",
                score=82,
            ),
        ]
        self.tasks = [
            AgentTask(id="task_topic_001", name="智能选题生成", status=TaskStatus.running, progress=68, current_step="分析表现模式", trace_id="tr_9a23_topic"),
            AgentTask(id="task_etl_001", name="抖音历史数据清洗", status=TaskStatus.succeeded, progress=100, current_step="已完成", trace_id="tr_7b11_etl"),
            AgentTask(id="task_memory_001", name="向量记忆写入", status=TaskStatus.pending, progress=12, current_step="等待执行", trace_id="tr_5d10_vec"),
        ]
        self.memories = [
            MemoryPattern(id="mem_success_1", type="success", summary="职场焦虑类内容必须在 15 秒内给出第一个解决动作。", confidence=0.82, source_count=14, last_verified_at="2026-05-09"),
            MemoryPattern(id="mem_seo_1", type="seo", summary="“不是 X，而是 Y”标题结构在程序员转型内容中收藏率更高。", confidence=0.76, source_count=9, last_verified_at="2026-05-08"),
        ]
        self.plans = [
            PublishPlan(id="plan_1", title="人工智能时代程序员机会", platform=Platform.douyin, scheduled_at="今天 18:30", stage="idea"),
            PublishPlan(id="plan_2", title="35 岁岗位切换", platform=Platform.xiaohongshu, scheduled_at="明天 11:00", stage="script"),
        ]
        self.raw_uploads: List[Dict[str, Any]] = []

    def create_task(self, workflow: str, payload: Dict[str, Any]) -> AgentTask:
        task = AgentTask(
            id=f"task_{workflow}_{uuid4().hex[:8]}",
            name=f"智能任务 {workflow}",
            status=TaskStatus.pending,
            progress=0,
            current_step="已排队",
            trace_id=f"tr_{uuid4().hex[:10]}",
            result={"acceptedPayload": payload},
        )
        self.tasks.insert(0, task)
        return task

    def get_content(self, content_id: str) -> Optional[ContentItem]:
        return next((item for item in self.contents if item.id == content_id), None)

    def add_raw_upload(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        item = {"id": f"raw_{uuid4().hex[:8]}", "receivedAt": date.today().isoformat(), "payload": payload}
        self.raw_uploads.insert(0, item)
        return item


repository = InMemoryRepository()
