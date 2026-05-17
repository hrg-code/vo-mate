import asyncio
import json
from types import SimpleNamespace

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool
from starlette.middleware.sessions import SessionMiddleware
from starlette.responses import JSONResponse, PlainTextResponse

from app.core.admin_auth import AdminAuthBackend, admin_role_permissions
from app.core.config import Settings
from app.db.models import Base
from app.db.models import AgentMemoryRecord
from app.db.models import ContentItem as ContentItemModel
from app.db.models import ContentKeyword, ContentLifetimeMetric, ContentTag, ContentTextAsset, PlatformAccount, Workspace
from app.repositories.content_item_repository import ContentItemRepository
from app.repositories.memory_store import repository
from app.repositories.script_draft_repository import ScriptDraftRepository
from app.repositories.topic_evidence_repository import TopicEvidenceRepository
from app.repositories.topic_idea_repository import topic_idea_repository
from app.schemas.common import CollectorImportRequest, ContentItem, ContentStatus, Platform, ScriptDraftCreateRequest, ScriptDraftVersionCreateRequest, TopicIdeaGenerateRequest
from app.services.content_ingestion_service import ContentIngestionService, DouyinRawAdapter
from app.services.content_vector_service import ContentVectorService
from app.services.script_draft_service import ScriptDraftService
from app.services.topic_content_rerank_service import TopicContentRerankService
from app.services.ai_provider_service import DashScopeEmbeddingProvider, DeepSeekChatProvider, MockChatProvider, MockEmbeddingProvider

from app.main import app

client = TestClient(app)


class TopicIdeaProvider:
    def __init__(self, candidates=None, fail: str | None = None) -> None:
        self.candidates = candidates
        self.fail = fail
        self.context = {}

    def generate_json(self, task, system_prompt, user_input, context, schema):
        if self.fail:
            raise RuntimeError(self.fail)
        if task == "topic_content_rerank":
            return {
                "items": [
                    {
                        "contentId": item["contentId"],
                        "relevanceLevel": "same_topic",
                        "score": 0.9,
                        "reason": "测试用真实 provider 相关性复核。",
                        "suggestedUse": "用于当前方向证据",
                    }
                    for item in context.get("candidates", [])
                ]
            }
        self.context.update(context)
        return {"candidates": self.candidates or [_topic_candidate("真实内容数据驱动的选题")]}


def _topic_candidate(title: str, **updates):
    data = {
        "title": title,
        "angle": "结合历史高分内容和长期记忆生成。",
        "predictedScore": 91,
        "seoScore": 88,
        "audienceScore": 86,
        "difficultyScore": 43,
        "risk": "需要补充具体案例。",
    }
    data.update(updates)
    return data


def _setup_real_topic_ideas(monkeypatch, *, candidates=None, provider=None, with_workspace=True, with_content=True, with_memory=True, settings=None):
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    settings = settings or Settings(
        postgres_host="localhost",
        llm_provider="deepseek",
        deepseek_api_key="configured",
        embedding_provider="dashscope",
        dashscope_api_key="configured",
    )
    provider = provider or TopicIdeaProvider(candidates)

    for module_path in [
        "app.repositories.topic_idea_repository",
        "app.repositories.topic_evidence_repository",
        "app.services.topic_idea_service",
        "app.services.topic_evidence_service",
        "app.services.topic_content_rerank_service",
        "app.services.content_vector_service",
    ]:
        monkeypatch.setattr(f"{module_path}.get_settings", lambda settings=settings: settings)
    monkeypatch.setattr("app.repositories.topic_idea_repository.get_admin_engine", lambda: engine)
    monkeypatch.setattr("app.repositories.topic_evidence_repository.get_admin_engine", lambda: engine)
    monkeypatch.setattr("app.services.topic_idea_service.ai_provider_service.get_required_chat_provider", lambda: provider)
    monkeypatch.setattr("app.services.topic_content_rerank_service.ai_provider_service.get_required_chat_provider", lambda: provider)

    with Session(engine) as session:
        if with_workspace:
            session.add(Workspace(id="ws_northstar", name="北极星内容组", status="active"))
            session.add(
                PlatformAccount(
                    id="douyin_demo",
                    workspace_id="ws_northstar",
                    platform="douyin",
                    account_name="抖音 · 程序员老陈",
                    status="active",
                )
            )
        if with_content:
            session.add(
                ContentItemModel(
                    id="ct_pg_1",
                    workspace_id="ws_northstar",
                    platform_account_id="douyin_demo",
                    platform="douyin",
                    external_content_id="7585913482206383412",
                    title="程序员副业接私活真实复盘",
                    description="程序员副业真实案例",
                    status="published",
                    views=120000,
                    likes=8000,
                    comments=500,
                    saves=1200,
                    shares=300,
                    completion_rate=0.42,
                    followers_gained=430,
                    score=92,
                    has_asr=True,
                    reviewed=True,
                )
            )
            session.add(
                ContentLifetimeMetric(
                    content_id="ct_pg_1",
                    play_count=120000,
                    like_count=8000,
                    comment_count=500,
                    collect_count=1200,
                    share_count=300,
                    follow_count=430,
                    finish_rate=0.42,
                    metric_score=92,
                )
            )
            session.add(ContentKeyword(content_id="ct_pg_1", keyword="程序员副业", score=0.9))
            session.add(ContentTag(content_id="ct_pg_1", tag="程序员"))
        if with_memory:
            session.add(
                AgentMemoryRecord(
                    id="mem_pg_1",
                    workspace_id="ws_northstar",
                    account_id="douyin_demo",
                    platform="douyin",
                    memory_type="success_pattern",
                    title="程序员副业成功模式",
                    content="程序员副业真实复盘要先给案例，再给判断标准。",
                    summary="真实长期记忆摘要",
                    source_type="manual",
                    source_ids=["ct_pg_1"],
                    confidence=0.91,
                    evidence_count=1,
                    status="active",
                )
            )
        session.commit()

    return engine, provider


def test_health() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_frontend_dashboard_contract() -> None:
    response = client.get("/api/v1/analytics/dashboard")
    assert response.status_code == 200
    payload = response.json()
    assert {"metrics", "contents", "tasks"} <= payload.keys()
    assert "publishedAt" in payload["contents"][0]
    assert "currentStep" in payload["tasks"][0]


def test_douyin_raw_adapter_maps_standard_content_and_metrics() -> None:
    adapter = DouyinRawAdapter()
    content, metric = adapter.to_standard(
        {
            "_id": "7585913482206383412",
            "base_info": {
                "desc": "程序员可以干一辈子吗\n正文第二行",
                "create_time": 1766233160,
                "duration": 60419,
                "cover": "https://example.com/cover.jpg",
            },
            "creator_stats": {
                "play_count": 34599,
                "digg_count": 132,
                "comment_count": 147,
                "share_count": 19,
                "collect_count": 22,
                "avg_view_duration": 17.06,
            },
        },
        workspace_id="ws_northstar",
        raw_collection="douyin_video_raw",
    )

    assert content.id == "ct_douyin_7585913482206383412"
    assert content.title == "程序员可以干一辈子吗"
    assert content.duration_seconds == 60
    assert content.cover_url == "https://example.com/cover.jpg"
    assert content.raw_document_id == "7585913482206383412"
    assert metric.play_count == 34599
    assert metric.like_count == 132
    assert metric.comment_count == 147
    assert metric.collect_count == 22
    assert metric.metric_score is not None


def test_douyin_raw_adapter_maps_platform_account_id() -> None:
    content, _metric = DouyinRawAdapter().to_standard(
        {"_id": "7585913482206383412", "base_info": {"desc": "程序员副业复盘", "duration": 60000}},
        workspace_id="ws_northstar",
        raw_collection="douyin_video_raw",
        platform_account_id="douyin_demo",
    )

    assert content.platform_account_id == "douyin_demo"


def test_collector_import_indexes_content_vector_best_effort(monkeypatch) -> None:
    class FakeContentRepository:
        def __init__(self) -> None:
            self.contents = []

        def upsert_content(self, content, metric):
            self.contents.append(content)
            return True

        def upsert_enrichment(self, **kwargs):
            return SimpleNamespace(
                text_asset_count=1,
                tag_count=0,
                keyword_count=0,
                traffic_source_count=0,
                asr_count=0,
            )

    indexed_ids = []
    fake_repository = FakeContentRepository()
    service = ContentIngestionService(fake_repository, repository)

    async def load_raw_documents(collection, limit):
        return [{"_id": "7585913482206383412", "base_info": {"desc": "程序员副业复盘", "duration": 60000}}]

    monkeypatch.setattr(service, "_load_raw_documents", load_raw_documents)
    monkeypatch.setattr(service, "_load_asr_documents", lambda collection, external_ids: {})
    monkeypatch.setattr("app.services.content_ingestion_service.content_vector_service.upsert_content_vector", lambda content_id: indexed_ids.append(content_id) or False)

    response = asyncio.run(
        service.import_raw_data(
            CollectorImportRequest(
                workspace_id="ws_northstar",
                account_id="douyin_demo",
                platform=Platform.douyin,
                limit=1,
                include_asr=False,
            )
        )
    )

    assert response.status == "succeeded"
    assert fake_repository.contents[0].platform_account_id == "douyin_demo"
    assert indexed_ids == [fake_repository.contents[0].id]


def test_content_repository_upsert_is_idempotent(monkeypatch) -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    monkeypatch.setattr("app.repositories.content_item_repository.get_settings", lambda: Settings(postgres_host="localhost"))
    monkeypatch.setattr("app.repositories.content_item_repository.get_admin_engine", lambda: engine)

    adapter = DouyinRawAdapter()
    content, metric = adapter.to_standard(
        {
            "_id": "7585913482206383412",
            "base_info": {"desc": "第一版标题", "duration": 60000},
            "statistics": {"play_count": 100, "digg_count": 10},
        },
        workspace_id="ws_northstar",
        raw_collection="douyin_video_raw",
    )
    repo = ContentItemRepository()

    assert repo.upsert_content(content, metric)
    content.title = "更新后的标题"
    metric.play_count = 200
    assert repo.upsert_content(content, metric)

    rows = repo.list_contents()
    assert rows is not None
    assert len(rows) == 1
    assert rows[0].title == "更新后的标题"
    assert rows[0].views == 200


def test_topic_content_evidence_separates_related_top_and_contrast(monkeypatch) -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    monkeypatch.setattr("app.repositories.topic_evidence_repository.get_settings", lambda: Settings(postgres_host="localhost"))
    monkeypatch.setattr("app.repositories.topic_evidence_repository.get_admin_engine", lambda: engine)

    with Session(engine) as session:
        session.add_all(
            [
                ContentItemModel(
                    id="ct_related",
                    workspace_id="ws_northstar",
                    platform_account_id="douyin_demo",
                    platform="douyin",
                    title="程序员副业接私活真实复盘",
                    status="published",
                    views=2000,
                    score=62,
                ),
                ContentItemModel(
                    id="ct_keyword_related",
                    workspace_id="ws_northstar",
                    platform_account_id="douyin_demo",
                    platform="douyin",
                    title="下班后的第一个工具",
                    status="published",
                    views=1500,
                    score=58,
                ),
                ContentItemModel(
                    id="ct_unrelated_top",
                    workspace_id="ws_northstar",
                    platform_account_id="douyin_demo",
                    platform="douyin",
                    title="职场沟通表达课",
                    status="published",
                    views=900000,
                    score=98,
                ),
                ContentItemModel(
                    id="ct_other_account",
                    workspace_id="ws_northstar",
                    platform_account_id="other_account",
                    platform="douyin",
                    title="程序员副业月入三万",
                    status="published",
                    views=800000,
                    score=96,
                ),
                ContentItemModel(
                    id="ct_low_related",
                    workspace_id="ws_northstar",
                    platform_account_id="douyin_demo",
                    platform="douyin",
                    title="程序员副业失败避坑",
                    status="published",
                    views=100,
                    score=18,
                ),
            ]
        )
        session.add_all(
            [
                ContentLifetimeMetric(content_id="ct_related", play_count=2000, metric_score=62),
                ContentLifetimeMetric(content_id="ct_keyword_related", play_count=1500, metric_score=58),
                ContentLifetimeMetric(content_id="ct_unrelated_top", play_count=900000, metric_score=98),
                ContentLifetimeMetric(content_id="ct_other_account", play_count=800000, metric_score=96),
                ContentLifetimeMetric(content_id="ct_low_related", play_count=100, metric_score=18),
                ContentTag(content_id="ct_keyword_related", tag="程序员", source="test"),
                ContentKeyword(content_id="ct_keyword_related", keyword="副业", score=0.9, source="test"),
                ContentTextAsset(content_id="ct_keyword_related", asset_type="asr", text="讲普通开发者怎么做下班后的独立产品"),
            ]
        )
        session.commit()

    result = TopicEvidenceRepository().load_topic_content_evidence(
        TopicIdeaGenerateRequest(direction="程序员副业", platforms=[Platform.douyin], account_ids=["douyin_demo"])
    )

    assert result is not None
    related_ids = {item["contentId"] for item in result["relatedContents"]}
    top_ids = {item["contentId"] for item in result["topPerformers"]}
    contrast_ids = {item["contentId"] for item in result["contrastContents"]}
    assert "ct_related" in related_ids
    assert "ct_keyword_related" in related_ids
    assert "ct_unrelated_top" not in related_ids
    assert "ct_other_account" not in related_ids
    assert "ct_unrelated_top" in top_ids
    assert "ct_other_account" not in top_ids
    assert contrast_ids <= related_ids
    assert "ct_low_related" in contrast_ids
    assert result["retrievalDiagnostics"]["filteredBy"]["accountIds"] == ["douyin_demo"]
    assert result["retrievalDiagnostics"]["accountFilterFallback"] is False


def test_topic_content_evidence_falls_back_to_null_account_content(monkeypatch) -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    monkeypatch.setattr("app.repositories.topic_evidence_repository.get_settings", lambda: Settings(postgres_host="localhost"))
    monkeypatch.setattr("app.repositories.topic_evidence_repository.get_admin_engine", lambda: engine)

    with Session(engine) as session:
        session.add_all(
            [
                ContentItemModel(
                    id="ct_null_related",
                    workspace_id="ws_northstar",
                    platform_account_id=None,
                    platform="douyin",
                    title="程序员副业接私活真实复盘",
                    status="published",
                    views=2000,
                    score=62,
                ),
                ContentItemModel(
                    id="ct_null_top",
                    workspace_id="ws_northstar",
                    platform_account_id=None,
                    platform="douyin",
                    title="程序员可以干一辈子吗",
                    status="published",
                    views=900000,
                    score=98,
                ),
                ContentItemModel(
                    id="ct_other_account",
                    workspace_id="ws_northstar",
                    platform_account_id="other_account",
                    platform="douyin",
                    title="程序员副业月入三万",
                    status="published",
                    views=800000,
                    score=96,
                ),
            ]
        )
        session.add_all(
            [
                ContentLifetimeMetric(content_id="ct_null_related", play_count=2000, metric_score=62),
                ContentLifetimeMetric(content_id="ct_null_top", play_count=900000, metric_score=98),
            ]
        )
        session.commit()

    result = TopicEvidenceRepository().load_topic_content_evidence(
        TopicIdeaGenerateRequest(direction="程序员副业", platforms=[Platform.douyin], account_ids=["douyin_demo"])
    )

    assert result is not None
    related_ids = {item["contentId"] for item in result["relatedContents"]}
    top_ids = {item["contentId"] for item in result["topPerformers"]}
    diagnostics = result["retrievalDiagnostics"]
    assert "ct_null_related" in related_ids
    assert "ct_null_top" in top_ids
    assert "ct_other_account" not in related_ids
    assert "ct_other_account" not in top_ids
    assert diagnostics["accountFilterFallback"] is True
    assert diagnostics["accountFilteredCandidateCount"] == 0
    assert diagnostics["nullAccountCandidateCount"] == 2
    assert diagnostics["filteredBy"]["accountFilterMode"] == "null"


def test_topic_content_evidence_prefers_exact_account_over_null_fallback(monkeypatch) -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    monkeypatch.setattr("app.repositories.topic_evidence_repository.get_settings", lambda: Settings(postgres_host="localhost"))
    monkeypatch.setattr("app.repositories.topic_evidence_repository.get_admin_engine", lambda: engine)

    with Session(engine) as session:
        session.add_all(
            [
                ContentItemModel(
                    id="ct_exact",
                    workspace_id="ws_northstar",
                    platform_account_id="douyin_demo",
                    platform="douyin",
                    title="程序员副业接私活真实复盘",
                    status="published",
                    views=1000,
                    score=60,
                ),
                ContentItemModel(
                    id="ct_null_should_not_mix",
                    workspace_id="ws_northstar",
                    platform_account_id=None,
                    platform="douyin",
                    title="程序员副业空账号旧数据",
                    status="published",
                    views=999999,
                    score=99,
                ),
            ]
        )
        session.commit()

    result = TopicEvidenceRepository().load_topic_content_evidence(
        TopicIdeaGenerateRequest(direction="程序员副业", platforms=[Platform.douyin], account_ids=["douyin_demo"])
    )

    assert result is not None
    related_ids = {item["contentId"] for item in result["relatedContents"]}
    top_ids = {item["contentId"] for item in result["topPerformers"]}
    diagnostics = result["retrievalDiagnostics"]
    assert "ct_exact" in related_ids
    assert "ct_null_should_not_mix" not in related_ids
    assert "ct_null_should_not_mix" not in top_ids
    assert diagnostics["accountFilterFallback"] is False
    assert diagnostics["accountFilteredCandidateCount"] == 1
    assert diagnostics["nullAccountCandidateCount"] == 0
    assert diagnostics["filteredBy"]["accountFilterMode"] == "requested"


def test_topic_workspace_context_prefers_postgres(monkeypatch) -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    monkeypatch.setattr("app.repositories.topic_evidence_repository.get_settings", lambda: Settings(postgres_host="localhost"))
    monkeypatch.setattr("app.repositories.topic_evidence_repository.get_admin_engine", lambda: engine)

    with Session(engine) as session:
        session.add(Workspace(id="ws_northstar", name="真实工作区", status="active"))
        session.add(
            PlatformAccount(
                id="douyin_demo",
                workspace_id="ws_northstar",
                platform="douyin",
                account_name="真实抖音账号",
                status="active",
            )
        )
        session.commit()

    context = TopicEvidenceRepository().load_workspace_context(
        TopicIdeaGenerateRequest(direction="程序员副业", platforms=[Platform.douyin], account_ids=["douyin_demo"])
    )

    assert context is not None
    assert context["workspaceName"] == "真实工作区"
    assert context["accountName"] == "真实抖音账号"
    assert context["platformScope"] == ["douyin"]
    assert context["workspaceContextSource"] == "postgres"


def test_topic_content_evidence_merges_embedding_hits_and_keeps_gate(monkeypatch) -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    monkeypatch.setattr("app.repositories.topic_evidence_repository.get_settings", lambda: Settings(postgres_host="localhost", milvus_host="localhost"))
    monkeypatch.setattr("app.repositories.topic_evidence_repository.get_admin_engine", lambda: engine)
    monkeypatch.setattr(
        "app.repositories.topic_evidence_repository.content_vector_service.search_content_hits",
        lambda request, query, top_k=24: [
            ("ct_hybrid", 0.93, "content:ct_hybrid:summary"),
            ("ct_embedding_related", 0.91, "content:ct_embedding_related:summary"),
            ("ct_embedding_unrelated", 0.99, "content:ct_embedding_unrelated:summary"),
        ],
    )
    monkeypatch.setattr("app.repositories.topic_evidence_repository.content_vector_service.last_error", None)

    with Session(engine) as session:
        session.add_all(
            [
                ContentItemModel(
                    id="ct_hybrid",
                    workspace_id="ws_northstar",
                    platform_account_id="douyin_demo",
                    platform="douyin",
                    title="程序员副业接私活真实复盘",
                    status="published",
                    views=2000,
                    score=62,
                ),
                ContentItemModel(
                    id="ct_embedding_related",
                    workspace_id="ws_northstar",
                    platform_account_id="douyin_demo",
                    platform="douyin",
                    title="下班后做工具",
                    status="published",
                    views=1000,
                    score=55,
                ),
                ContentItemModel(
                    id="ct_embedding_unrelated",
                    workspace_id="ws_northstar",
                    platform_account_id="douyin_demo",
                    platform="douyin",
                    title="职场沟通表达课",
                    status="published",
                    views=900000,
                    score=98,
                ),
            ]
        )
        session.add_all(
            [
                ContentLifetimeMetric(content_id="ct_hybrid", play_count=2000, metric_score=62),
                ContentLifetimeMetric(content_id="ct_embedding_related", play_count=1000, metric_score=55),
                ContentLifetimeMetric(content_id="ct_embedding_unrelated", play_count=900000, metric_score=98),
                ContentTextAsset(content_id="ct_embedding_related", asset_type="asr", text="普通程序员副业独立产品路线"),
            ]
        )
        session.commit()

    result = TopicEvidenceRepository().load_topic_content_evidence(
        TopicIdeaGenerateRequest(direction="程序员副业", platforms=[Platform.douyin], account_ids=["douyin_demo"])
    )

    assert result is not None
    related_by_id = {item["contentId"]: item for item in result["relatedContents"]}
    assert related_by_id["ct_hybrid"]["retrievalSource"] == "hybrid"
    assert related_by_id["ct_hybrid"]["embeddingScore"] == 0.93
    assert related_by_id["ct_embedding_related"]["retrievalSource"] == "hybrid"
    assert "ct_embedding_unrelated" not in related_by_id
    assert result["retrievalDiagnostics"]["strategy"] == "hybrid_keyword_embedding_gate"
    assert result["retrievalDiagnostics"]["embeddingCandidateCount"] == 3
    assert result["retrievalDiagnostics"]["mergedCandidateCount"] == 3
    assert result["retrievalDiagnostics"]["embeddingConfigured"] is True
    assert result["retrievalDiagnostics"]["rerankEnabled"] is True


def test_topic_content_rerank_service_normalizes_and_filters(monkeypatch) -> None:
    class RerankProvider:
        def generate_json(self, task, system_prompt, user_input, context, schema):
            return {
                "items": [
                    {
                        "contentId": "ct_same",
                        "relevanceLevel": "same_topic",
                        "score": 92,
                        "reason": "同主题",
                        "suggestedUse": "作为核心证据",
                    },
                    {
                        "contentId": "ct_weak",
                        "relevanceLevel": "weak",
                        "score": 0.4,
                        "reason": "只共享人群",
                        "suggestedUse": "不使用",
                    },
                ]
            }

    monkeypatch.setattr("app.services.topic_content_rerank_service.ai_provider_service.get_required_chat_provider", lambda: RerankProvider())
    result = TopicContentRerankService().rerank(
        TopicIdeaGenerateRequest(direction="程序员副业", platforms=[Platform.douyin], account_ids=["douyin_demo"]),
        [
            {"contentId": "ct_same", "title": "程序员副业复盘", "relevanceScore": 0.9, "score": 60, "views": 100},
            {"contentId": "ct_weak", "title": "程序员沟通", "relevanceScore": 0.8, "score": 98, "views": 900000},
        ],
    )

    assert result["diagnostics"]["rerankFallback"] is False
    assert result["diagnostics"]["rerankAcceptedCount"] == 1
    assert result["diagnostics"]["rerankRejectedCount"] == 1
    assert result["candidates"][0]["contentId"] == "ct_same"
    assert result["candidates"][0]["llmRelevanceScore"] == 0.92
    assert result["candidates"][0]["llmRelevanceLevel"] == "same_topic"


def test_topic_content_rerank_service_falls_back_on_provider_failure(monkeypatch) -> None:
    class FailingProvider:
        def generate_json(self, *args, **kwargs):
            raise RuntimeError("rerank unavailable")

    monkeypatch.setattr("app.services.topic_content_rerank_service.ai_provider_service.get_required_chat_provider", lambda: FailingProvider())
    candidates = [{"contentId": "ct_rule", "title": "程序员副业", "relevanceScore": 0.9}]
    result = TopicContentRerankService().rerank(
        TopicIdeaGenerateRequest(direction="程序员副业", platforms=[Platform.douyin], account_ids=["douyin_demo"]),
        candidates,
    )

    assert result["candidates"] == candidates
    assert result["diagnostics"]["rerankFallback"] is True
    assert "rerank unavailable" in result["diagnostics"]["rerankError"]


def test_topic_content_evidence_uses_llm_rerank_to_filter_and_sort(monkeypatch) -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    monkeypatch.setattr("app.repositories.topic_evidence_repository.get_settings", lambda: Settings(postgres_host="localhost"))
    monkeypatch.setattr("app.repositories.topic_evidence_repository.get_admin_engine", lambda: engine)

    class RerankProvider:
        def generate_json(self, task, system_prompt, user_input, context, schema):
            return {
                "items": [
                    {"contentId": "ct_adjacent", "relevanceLevel": "adjacent_topic", "score": 0.95, "reason": "相邻主题", "suggestedUse": "辅助证据"},
                    {"contentId": "ct_same", "relevanceLevel": "same_topic", "score": 0.7, "reason": "同主题", "suggestedUse": "核心证据"},
                    {"contentId": "ct_weak_high", "relevanceLevel": "weak", "score": 0.99, "reason": "只共享人群", "suggestedUse": "不使用"},
                ]
            }

    monkeypatch.setattr("app.services.topic_content_rerank_service.ai_provider_service.get_required_chat_provider", lambda: RerankProvider())

    with Session(engine) as session:
        session.add_all(
            [
                ContentItemModel(
                    id="ct_same",
                    workspace_id="ws_northstar",
                    platform_account_id="douyin_demo",
                    platform="douyin",
                    title="程序员副业接私活复盘",
                    status="published",
                    views=100,
                    score=50,
                ),
                ContentItemModel(
                    id="ct_adjacent",
                    workspace_id="ws_northstar",
                    platform_account_id="douyin_demo",
                    platform="douyin",
                    title="程序员副业独立产品路线",
                    status="published",
                    views=200,
                    score=60,
                ),
                ContentItemModel(
                    id="ct_weak_high",
                    workspace_id="ws_northstar",
                    platform_account_id="douyin_demo",
                    platform="douyin",
                    title="程序员副业泛泛建议",
                    status="published",
                    views=999999,
                    score=99,
                ),
            ]
        )
        session.commit()

    result = TopicEvidenceRepository().load_topic_content_evidence(
        TopicIdeaGenerateRequest(direction="程序员副业", platforms=[Platform.douyin], account_ids=["douyin_demo"])
    )

    assert result is not None
    related_ids = [item["contentId"] for item in result["relatedContents"]]
    assert related_ids[:2] == ["ct_same", "ct_adjacent"]
    assert "ct_weak_high" not in related_ids
    assert result["relatedContents"][0]["llmRelevanceLevel"] == "same_topic"
    assert result["retrievalDiagnostics"]["rerankAcceptedCount"] == 2
    assert result["retrievalDiagnostics"]["rerankRejectedCount"] == 1
    assert result["retrievalDiagnostics"]["rerankFallback"] is False


def test_topic_content_evidence_keeps_rule_results_when_rerank_fails(monkeypatch) -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    monkeypatch.setattr("app.repositories.topic_evidence_repository.get_settings", lambda: Settings(postgres_host="localhost"))
    monkeypatch.setattr("app.repositories.topic_evidence_repository.get_admin_engine", lambda: engine)

    class FailingProvider:
        def generate_json(self, *args, **kwargs):
            raise RuntimeError("rerank unavailable")

    monkeypatch.setattr("app.services.topic_content_rerank_service.ai_provider_service.get_required_chat_provider", lambda: FailingProvider())

    with Session(engine) as session:
        session.add(
            ContentItemModel(
                id="ct_rule",
                workspace_id="ws_northstar",
                platform_account_id="douyin_demo",
                platform="douyin",
                title="程序员副业接私活复盘",
                status="published",
                views=100,
                score=50,
            )
        )
        session.commit()

    result = TopicEvidenceRepository().load_topic_content_evidence(
        TopicIdeaGenerateRequest(direction="程序员副业", platforms=[Platform.douyin], account_ids=["douyin_demo"])
    )

    assert result is not None
    assert [item["contentId"] for item in result["relatedContents"]] == ["ct_rule"]
    assert result["retrievalDiagnostics"]["rerankFallback"] is True
    assert "rerank unavailable" in result["retrievalDiagnostics"]["rerankError"]


def test_mock_topic_ideas_use_content_evidence_without_ai_cliches() -> None:
    provider = MockChatProvider()
    result = provider.generate_json(
        task="topic_ideas",
        system_prompt="",
        user_input="程序员副业",
        context={
            "direction": "程序员副业",
            "platforms": ["douyin"],
            "goal": "followers",
            "count": 2,
            "audience": "25-35 岁普通程序员",
            "evidence": [{"id": "mem_1"}],
            "contentEvidence": {
                "relatedContents": [
                    {
                        "title": "程序员副业接私活真实复盘",
                        "views": 2000,
                        "comments": 36,
                        "score": 82,
                    }
                ],
                "topPerformers": [{"title": "程序员可以干一辈子吗", "views": 34599, "score": 91}],
                "contrastContents": [{"title": "程序员副业泛泛建议", "views": 100, "score": 18}],
            },
            "patternSummary": {"topContentTitle": "程序员可以干一辈子吗"},
        },
        schema={},
    )

    candidates = result["candidates"]
    assert candidates[0]["title"].startswith("程序员副业：")
    assert "程序员副业接私活真实复盘" in candidates[0]["angle"]
    joined = json.dumps(candidates, ensure_ascii=False)
    assert "比单纯努力更重要" not in joined
    assert "普通人自救" not in joined
    assert "底层逻辑" not in joined


def test_content_vector_service_searchable_text_and_filter(monkeypatch) -> None:
    class ContentRow:
        id = "ct_vector"
        workspace_id = "ws_northstar"
        platform_account_id = "douyin_demo"
        platform = "douyin"
        external_content_id = "7585913482206383412"
        title = "程序员副业复盘"
        description = "普通开发者做独立产品"
        status = "published"
        published_at = None
        views = 100
        score = 80
        completion_rate = 0.4

    metric = SimpleNamespace(metric_score=88, play_count=1200, finish_rate=0.41)
    service = ContentVectorService()
    text = service.searchable_text(
        ContentRow(),
        enrichment={"tags": ["程序员"], "keywords": ["副业"]},
        text_assets=["ASR 里提到接私活"],
        metric=metric,
    )
    expr = service._milvus_filter_expr(
        TopicIdeaGenerateRequest(direction="程序员副业", platforms=[Platform.douyin], account_ids=["douyin_demo"])
    )

    assert "程序员副业复盘" in text
    assert "副业" in text
    assert "ASR 里提到接私活" in text
    assert "score=88" in text
    assert 'workspace_id == "ws_northstar"' in expr
    assert 'account_id in ["douyin_demo"]' in expr
    assert 'platform in ["douyin"]' in expr
    assert 'status == "published"' in expr


def test_content_vector_service_search_failure_returns_empty(monkeypatch) -> None:
    class FailingEmbeddingProvider:
        def embed_query(self, text):
            raise RuntimeError("embedding unavailable")

    service = ContentVectorService()
    service.embedding_provider = FailingEmbeddingProvider()
    monkeypatch.setattr("app.services.content_vector_service.get_settings", lambda: Settings(milvus_host="localhost"))

    hits = service.search_content_hits(
        TopicIdeaGenerateRequest(direction="程序员副业", platforms=[Platform.douyin], account_ids=["douyin_demo"]),
        "程序员副业 followers",
    )

    assert hits == []
    assert "embedding unavailable" in service.last_error


def test_douyin_raw_adapter_maps_enrichment_and_asr() -> None:
    adapter = DouyinRawAdapter()
    raw = {
        "_id": "7585913482206383412",
        "base_info": {"desc": "程序员可以干一辈子吗", "duration": 60000},
        "raw_list_data": {
            "caption": "程序员能干一辈子吗？#程序员",
            "cha_list": [{"cha_name": "程序员", "cha_id": "157"}],
            "text_extra": [{"hashtag_name": "职场", "hashtag_id": "188", "start": 12, "end": 15}],
        },
        "analysis": {
            "other_data": {
                "audience_search_most_keywords": [
                    {"keywords": "程序员35岁", "query_cnt_7d": 1234},
                    {"keywords": "AI程序员", "query_7d_list": [{"value": 10}, {"value": 20}]},
                ]
            },
            "traffic_sources": [{"source_name": "搜索", "ratio": 0.21, "count": 100}],
        },
    }
    content, _metric = adapter.to_standard(raw, workspace_id="ws_northstar", raw_collection="douyin_video_raw")
    asr_asset = adapter.asr_asset(
        {
            "_id": "asr_1",
            "video_id": "7585913482206383412",
            "text": "程序员能干一辈子吗？",
            "language": "zh",
            "segments": [{"start": 0.0, "end": 2.19, "text": "程序员能干一辈子吗？"}],
            "duration_seconds": 60,
        },
        content,
        "douyin_video_asr_results",
    )

    assert [asset.asset_type for asset in adapter.text_assets(raw, content)] == ["title", "description", "caption"]
    assert {tag.tag for tag in adapter.tags(raw, content.id)} == {"程序员", "职场"}
    assert {keyword.keyword for keyword in adapter.keywords(raw, content.id)} == {"程序员35岁", "AI程序员"}
    assert adapter.traffic_sources(raw, content.id)[0].source_name == "搜索"
    assert asr_asset is not None
    assert asr_asset.text == "程序员能干一辈子吗？"


def test_content_repository_enrichment_is_idempotent(monkeypatch) -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    monkeypatch.setattr("app.repositories.content_item_repository.get_settings", lambda: Settings(postgres_host="localhost"))
    monkeypatch.setattr("app.repositories.content_item_repository.get_admin_engine", lambda: engine)

    adapter = DouyinRawAdapter()
    raw = {
        "_id": "7585913482206383412",
        "base_info": {"desc": "第一版标题", "duration": 60000},
        "raw_list_data": {"cha_list": [{"cha_name": "程序员"}]},
        "analysis": {"other_data": {"audience_search_most_keywords": [{"keywords": "程序员35岁", "query_cnt_7d": 100}]}},
    }
    content, metric = adapter.to_standard(raw, workspace_id="ws_northstar", raw_collection="douyin_video_raw")
    repo = ContentItemRepository()

    assert repo.upsert_content(content, metric)
    for _ in range(2):
        counts = repo.upsert_enrichment(
            content_id=content.id,
            text_assets=adapter.text_assets(raw, content),
            tags=adapter.tags(raw, content.id),
            keywords=adapter.keywords(raw, content.id),
            traffic_sources=adapter.traffic_sources(raw, content.id),
            asr_asset=adapter.asr_asset(
                {"video_id": "7585913482206383412", "text": "ASR 文本", "language": "zh", "segments": [{"start": 0, "end": 1, "text": "ASR 文本"}]},
                content,
                "douyin_video_asr_results",
            ),
        )
        assert counts is not None

    summary = repo.load_enrichment_summary([content.id])
    asr = repo.get_asr(content.id)
    assert summary[content.id]["tags"] == ["程序员"]
    assert summary[content.id]["keywords"] == ["程序员35岁"]
    assert asr is not None
    assert asr["text"] == "ASR 文本"
    assert len(asr["segments"]) == 1


def test_content_asr_prefers_postgres_repository(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.api.v1.contents.content_item_repository.get_asr",
        lambda content_id: {
            "contentId": content_id,
            "text": "真实 ASR 文本",
            "language": "zh",
            "durationSeconds": 60,
            "segments": [{"start": 0.0, "end": 1.0, "text": "真实 ASR 文本"}],
        },
    )

    response = client.get("/api/v1/contents/ct_douyin_7585913482206383412/asr")
    assert response.status_code == 200
    assert response.json()["text"] == "真实 ASR 文本"
    assert response.json()["segments"][0]["end"] == 1.0


def test_topic_evidence_content_metric_includes_enrichment() -> None:
    class ContentRow:
        id = "ct_douyin_1"
        title = "真实内容"
        platform = "douyin"
        published_at = None
        duration_seconds = 60
        views = 100
        likes = 10
        comments = 2
        saves = 3
        shares = 1
        completion_rate = 0.4
        followers_gained = 5
        score = 80
        status = "published"
        has_asr = True
        reviewed = False

    metric = TopicEvidenceRepository()._content_metric(
        ContentRow(),
        enrichment={"tags": ["程序员", "职场"], "keywords": ["程序员35岁"]},
    )

    assert metric["tags"] == ["程序员", "职场"]
    assert metric["keywords"] == ["程序员35岁"]
    assert metric["hasAsr"] is True


def test_contents_prefer_postgres_repository(monkeypatch) -> None:
    pg_content = ContentItem(
        id="ct_pg_real",
        title="真实入库内容",
        platform=Platform.douyin,
        published_at="2026-05-12",
        duration_seconds=60,
        views=888,
        likes=80,
        comments=8,
        saves=18,
        shares=6,
        completion_rate=0.41,
        followers_gained=12,
        score=91,
        status=ContentStatus.published,
        has_asr=False,
        reviewed=False,
    )
    monkeypatch.setattr("app.api.v1.contents.content_item_repository.list_contents", lambda limit=100: [pg_content])
    monkeypatch.setattr("app.api.v1.analytics.content_item_repository.list_contents", lambda limit=100: [pg_content])

    contents = client.get("/api/v1/contents")
    assert contents.status_code == 200
    assert contents.json()[0]["id"] == "ct_pg_real"

    dashboard = client.get("/api/v1/analytics/dashboard")
    assert dashboard.status_code == 200
    assert dashboard.json()["contents"][0]["id"] == "ct_pg_real"


def test_collector_import_returns_counts_when_mongo_unavailable() -> None:
    response = client.post(
        "/api/v1/collector/import",
        json={
            "workspaceId": "ws_northstar",
            "platform": "douyin",
            "collection": "douyin_video_raw",
            "limit": 100,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["taskId"].startswith("task_raw-import_")
    assert payload["status"] == "failed"
    assert payload["processedCount"] == 0
    assert payload["upsertedCount"] == 0
    assert payload["failedCount"] == 0
    assert payload["textAssetCount"] == 0
    assert payload["asrCount"] == 0


def test_ai_task_creation() -> None:
    response = client.post("/api/v1/ai/script", json={"topicId": "tp_role_shift"})
    assert response.status_code == 200
    payload = response.json()
    assert payload["id"].startswith("task_script_")
    assert payload["status"] == "pending"


def test_topic_ideas_streams_results(monkeypatch) -> None:
    _engine, provider = _setup_real_topic_ideas(
        monkeypatch,
        candidates=[
            _topic_candidate("真实内容数据驱动的选题 A"),
            _topic_candidate("真实内容数据驱动的选题 B", predictedScore=88),
        ],
    )
    response = client.post(
        "/api/v1/ai/topic-ideas",
        json={
            "direction": "程序员副业",
            "platforms": ["douyin"],
            "goal": "followers",
            "count": 2,
        },
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    events = _parse_sse_events(response.text)
    event_names = [event["event"] for event in events]
    assert event_names[0] == "start"
    assert "progress" in event_names
    assert "evidence" in event_names
    assert event_names[-1] == "done"

    topic_events = [event for event in events if event["event"] == "topic_idea"]
    assert len(topic_events) == 2
    assert "predictedScore" in topic_events[0]["data"]
    assert "recommendReason" in topic_events[0]["data"]
    assert topic_events[0]["data"]["targetPlatforms"] == ["douyin"]
    assert events[-1]["data"]["count"] == 2
    assert len(events[-1]["data"]["topicIdeas"]) == 2
    assert provider.context["dataSourceMode"] == "postgres_no_vector"

    generation = topic_idea_repository.get_generation(events[-1]["data"]["generationId"])
    assert generation is not None
    assert generation["status"] == "succeeded"
    assert generation["workflow"] == "topic-ideas"
    assert generation["inputPayload"]["workspaceContextSource"] == "postgres"
    assert generation["inputPayload"]["dataSourceMode"] == "postgres_no_vector"
    assert generation["inputPayload"]["contentRetrievalDiagnostics"]["dataSourceMode"] == "postgres"
    assert "memory_fallback" not in json.dumps(generation, ensure_ascii=False)
    assert generation["outputPayload"]["count"] == 2

    generation_response = client.get(f"/api/v1/ai/generations/{events[-1]['data']['generationId']}")
    assert generation_response.status_code == 200
    assert generation_response.json()["status"] == "succeeded"

    listed = client.get("/api/v1/ai/topic-ideas")
    assert listed.status_code == 200
    assert any(item["generationId"] == events[-1]["data"]["generationId"] for item in listed.json())


def test_ai_evidence_defaults_to_postgres_evidence(monkeypatch) -> None:
    _setup_real_topic_ideas(monkeypatch)

    response = client.get("/api/v1/ai/evidence")

    assert response.status_code == 200
    payload = response.json()
    assert payload
    assert any(item["source"] == "postgres_content" for item in payload)
    assert any(item["source"] == "postgres_memory" for item in payload)
    assert all(item["source"] != "memory_store" for item in payload)


def test_ai_evidence_previews_postgres_content_and_memory(monkeypatch) -> None:
    _setup_real_topic_ideas(monkeypatch)

    response = client.get(
        "/api/v1/ai/evidence",
        params={
            "workspaceId": "ws_northstar",
            "accountId": "douyin_demo",
            "platform": "douyin",
            "direction": "程序员副业",
            "limit": 10,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert any(item["type"] in {"content", "metric"} and item["source"] == "postgres_content" for item in payload)
    assert any(item["type"] == "memory" and item["source"] == "postgres_memory" for item in payload)
    assert any(item["type"] == "raw" and item["source"] == "retrievalDiagnostics" for item in payload)


def test_ai_evidence_fails_without_postgres_evidence(monkeypatch) -> None:
    settings = Settings(postgres_host=None)
    for module_path in [
        "app.repositories.topic_evidence_repository",
        "app.services.topic_evidence_service",
    ]:
        monkeypatch.setattr(f"{module_path}.get_settings", lambda settings=settings: settings)

    response = client.get("/api/v1/ai/evidence")

    assert response.status_code == 503
    assert "PostgreSQL" in response.json()["detail"]


def test_ai_evidence_reads_generation_context(monkeypatch) -> None:
    _setup_real_topic_ideas(monkeypatch, candidates=[_topic_candidate("真实内容数据驱动的选题")])
    response = client.post(
        "/api/v1/ai/topic-ideas",
        json={"direction": "程序员副业", "platforms": ["douyin"], "count": 1},
    )
    events = _parse_sse_events(response.text)
    generation_id = events[-1]["data"]["generationId"]

    evidence_response = client.get(f"/api/v1/ai/evidence?generationId={generation_id}")

    assert evidence_response.status_code == 200
    payload = evidence_response.json()
    assert any(item["type"] == "memory" for item in payload)
    assert any(item["type"] == "raw" and item["source"] == "retrievalDiagnostics" for item in payload)


def test_ai_evidence_generation_not_found() -> None:
    response = client.get("/api/v1/ai/evidence?generationId=gen_missing")

    assert response.status_code == 404


def test_topic_ideas_request_validation() -> None:
    blank_direction = client.post(
        "/api/v1/ai/topic-ideas",
        json={"direction": "   ", "platforms": ["douyin"]},
    )
    assert blank_direction.status_code == 422

    invalid_platform = client.post(
        "/api/v1/ai/topic-ideas",
        json={"direction": "程序员职业成长", "platforms": ["not-a-platform"]},
    )
    assert invalid_platform.status_code == 422


def test_topic_ideas_can_hide_evidence_details(monkeypatch) -> None:
    _setup_real_topic_ideas(monkeypatch)
    response = client.post(
        "/api/v1/ai/topic-ideas",
        json={
            "direction": "程序员副业",
            "platforms": ["douyin"],
            "includeEvidence": False,
        },
    )

    assert response.status_code == 200
    events = _parse_sse_events(response.text)
    assert "evidence" not in [event["event"] for event in events]
    topic_event = next(event for event in events if event["event"] == "topic_idea")
    assert topic_event["data"]["evidence"] == []
    generation = topic_idea_repository.get_generation(events[-1]["data"]["generationId"])
    assert generation is not None
    assert generation["evidenceIds"]


def test_topic_idea_service_emits_error_event_on_provider_failure(monkeypatch) -> None:
    _setup_real_topic_ideas(monkeypatch, provider=TopicIdeaProvider(fail="provider unavailable"))
    response = client.post(
        "/api/v1/ai/topic-ideas",
        json={"direction": "程序员副业", "platforms": ["douyin"]},
    )

    assert response.status_code == 200
    events = _parse_sse_events(response.text)
    assert events[-1]["event"] == "error"
    assert events[-1]["data"]["code"] == "RuntimeError"

    generation = topic_idea_repository.get_generation(events[-1]["data"]["generationId"])
    assert generation is not None
    assert generation["status"] == "failed"
    assert generation["error"] == "provider unavailable"


def test_topic_ideas_require_deepseek_key(monkeypatch) -> None:
    _setup_real_topic_ideas(
        monkeypatch,
        settings=Settings(postgres_host="localhost", llm_provider="deepseek", deepseek_api_key=None),
    )
    monkeypatch.setattr(
        "app.services.topic_idea_service.ai_provider_service.get_required_chat_provider",
        lambda: (_ for _ in ()).throw(RuntimeError("VO_MATE_DEEPSEEK_API_KEY is required for real topic idea generation")),
    )

    response = client.post(
        "/api/v1/ai/topic-ideas",
        json={"direction": "程序员副业", "platforms": ["douyin"], "count": 1},
    )

    assert response.status_code == 200
    events = _parse_sse_events(response.text)
    assert events[-1]["event"] == "error"
    assert "DEEPSEEK_API_KEY" in events[-1]["data"]["message"]
    generation = topic_idea_repository.get_generation(events[-1]["data"]["generationId"])
    assert generation is not None
    assert generation["status"] == "failed"


def test_topic_ideas_require_postgres_workspace(monkeypatch) -> None:
    _setup_real_topic_ideas(monkeypatch, with_workspace=False)

    response = client.post(
        "/api/v1/ai/topic-ideas",
        json={"direction": "程序员副业", "platforms": ["douyin"], "count": 1},
    )

    events = _parse_sse_events(response.text)
    assert events[-1]["event"] == "error"
    assert "workspace/account" in events[-1]["data"]["message"]
    assert "memory_fallback" not in response.text


def test_topic_ideas_require_postgres_content_evidence(monkeypatch) -> None:
    _setup_real_topic_ideas(monkeypatch, with_content=False)

    response = client.post(
        "/api/v1/ai/topic-ideas",
        json={"direction": "程序员副业", "platforms": ["douyin"], "count": 1},
    )

    events = _parse_sse_events(response.text)
    assert events[-1]["event"] == "error"
    assert "content evidence" in events[-1]["data"]["message"]
    assert "memory_content" not in response.text


def test_topic_ideas_prefer_milvus_evidence_when_available(monkeypatch) -> None:
    settings = Settings(
        postgres_host="localhost",
        llm_provider="deepseek",
        deepseek_api_key="configured",
        embedding_provider="dashscope",
        dashscope_api_key="configured",
        milvus_host="localhost",
    )
    _engine, provider = _setup_real_topic_ideas(monkeypatch, settings=settings)
    monkeypatch.setattr(
        "app.services.topic_evidence_service.memory_vector_service.search_milvus_hits",
        lambda request: [("mem_milvus_1", 0.94)],
    )
    monkeypatch.setattr(
        "app.services.topic_evidence_service.topic_evidence_service.evidence_repository.load_memory_evidence_by_ids",
        lambda hits: [
            {
                "id": "mem_milvus_1",
                "memoryId": "mem_milvus_1",
                "sourceType": "milvus_memory",
                "sourceId": "mem_milvus_1",
                "memoryType": "success_pattern",
                "title": "Milvus 成功模式",
                "summary": "向量召回到的长期记忆摘要",
                "score": 0.94,
                "reason": "向量召回成功模式",
            }
        ],
    )
    monkeypatch.setattr(
        "app.services.topic_evidence_service.topic_evidence_service.evidence_repository.retrieve_topic_memories",
        lambda request: [
            {
                "id": "mem_pg_should_not_win",
                "memoryId": "mem_pg_should_not_win",
                "sourceType": "postgres_memory",
                "sourceId": "mem_pg_should_not_win",
                "memoryType": "success_pattern",
                "title": "PG 备用模式",
                "summary": "不应优先于 Milvus。",
                "score": 0.88,
                "reason": "关键词命中",
            }
        ],
    )

    response = client.post(
        "/api/v1/ai/topic-ideas",
        json={"direction": "程序员副业", "platforms": ["douyin"], "count": 1},
    )

    assert response.status_code == 200
    events = _parse_sse_events(response.text)
    assert events[-1]["event"] == "done"
    assert provider.context["dataSourceMode"] == "milvus"
    assert provider.context["evidence"][0]["sourceType"] == "milvus_memory"

    generation = topic_idea_repository.get_generation(events[-1]["data"]["generationId"])
    assert generation is not None
    assert generation["inputPayload"]["dataSourceMode"] == "milvus"
    assert generation["evidenceIds"] == ["mem_milvus_1"]


def test_topic_ideas_fall_back_to_postgres_when_milvus_fails(monkeypatch) -> None:
    settings = Settings(
        postgres_host="localhost",
        llm_provider="deepseek",
        deepseek_api_key="configured",
        embedding_provider="dashscope",
        dashscope_api_key="configured",
        milvus_host="localhost",
    )
    _engine, provider = _setup_real_topic_ideas(monkeypatch, settings=settings)

    def fail_milvus(request):
        raise RuntimeError("milvus unavailable")

    monkeypatch.setattr("app.services.topic_evidence_service.memory_vector_service.search_milvus_hits", fail_milvus)

    response = client.post(
        "/api/v1/ai/topic-ideas",
        json={"direction": "程序员副业", "platforms": ["douyin"], "count": 1},
    )

    assert response.status_code == 200
    events = _parse_sse_events(response.text)
    assert events[-1]["event"] == "done"
    assert provider.context["dataSourceMode"] == "postgres_no_vector"
    assert provider.context["evidence"][0]["sourceType"] == "postgres_memory"


def test_topic_ideas_require_postgres_memory_evidence(monkeypatch) -> None:
    _setup_real_topic_ideas(monkeypatch, with_memory=False)

    response = client.post(
        "/api/v1/ai/topic-ideas",
        json={"direction": "程序员副业", "platforms": ["douyin"], "count": 1},
    )

    events = _parse_sse_events(response.text)
    assert events[-1]["event"] == "error"
    assert "agent_memory_records" in events[-1]["data"]["message"]
    assert "sourceType" not in response.text


def test_topic_ideas_do_not_rule_fill_missing_candidate_count(monkeypatch) -> None:
    _setup_real_topic_ideas(monkeypatch, candidates=[_topic_candidate("只返回一个真实候选")])

    response = client.post(
        "/api/v1/ai/topic-ideas",
        json={"direction": "程序员副业", "platforms": ["douyin"], "count": 3},
    )

    events = _parse_sse_events(response.text)
    assert events[-1]["event"] == "done"
    assert events[-1]["data"]["count"] == 1
    assert len([event for event in events if event["event"] == "topic_idea"]) == 1


def test_topic_ideas_coerce_incomplete_model_candidate(monkeypatch) -> None:
    _setup_real_topic_ideas(monkeypatch, candidates=[{"title": "字段不完整的真实候选"}])

    response = client.post(
        "/api/v1/ai/topic-ideas",
        json={"direction": "程序员副业", "platforms": ["douyin"], "count": 1},
    )

    events = _parse_sse_events(response.text)
    assert events[-1]["event"] == "done"
    topic_event = next(event for event in events if event["event"] == "topic_idea")
    assert topic_event["data"]["title"] == "字段不完整的真实候选"
    assert topic_event["data"]["angle"]
    assert topic_event["data"]["predictedScore"] > 0


def test_topic_ideas_persistence_failure_does_not_write_memory(monkeypatch) -> None:
    settings = Settings(postgres_host=None, llm_provider="deepseek", deepseek_api_key="configured")
    for module_path in ["app.repositories.topic_idea_repository", "app.services.topic_idea_service"]:
        monkeypatch.setattr(f"{module_path}.get_settings", lambda settings=settings: settings)

    response = client.post(
        "/api/v1/ai/topic-ideas",
        json={"direction": "程序员副业", "platforms": ["douyin"], "count": 1},
    )

    events = _parse_sse_events(response.text)
    assert events[-1]["event"] == "error"
    assert "PostgreSQL ai_generations persistence is required" in events[-1]["data"]["message"]
    assert topic_idea_repository.get_generation(events[-1]["data"]["generationId"]) is None


def test_memory_search_uses_milvus_before_memory_fallback(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.services.memory_record_service.memory_vector_service.search_milvus_hits",
        lambda request: [("mem_case_demo", 0.97)],
    )

    response = client.post(
        "/api/v1/memory/search",
        json={"query": "程序员职业成长", "workspaceId": "ws_northstar", "accountId": "douyin_demo"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["results"][0]["memoryId"] == "mem_case_demo"
    assert payload["results"][0]["score"] == 0.97


def test_ai_generation_not_found() -> None:
    response = client.get("/api/v1/ai/generations/gen_missing")
    assert response.status_code == 404


def test_create_script_draft_generates_initial_version(monkeypatch) -> None:
    monkeypatch.setattr("app.repositories.script_draft_repository.get_settings", lambda: Settings(postgres_host=""))
    monkeypatch.setattr("app.services.script_draft_service.get_settings", lambda: Settings(postgres_host=""))
    monkeypatch.setattr("app.services.script_draft_service.ai_provider_service.get_chat_provider", lambda: MockChatProvider())

    response = client.post(
        "/api/v1/scripts",
        json={"topic": "AI 时代普通程序员怎么转型", "platform": "douyin", "durationSeconds": 60},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["id"].startswith("scr_")
    assert payload["currentVersionId"] == payload["versions"][0]["id"]
    assert payload["versions"][0]["versionNo"] == 1
    assert payload["versions"][0]["sourceType"] == "ai_initial"
    assert payload["versions"][0]["generationId"].startswith("gen_")
    assert payload["versions"][0]["body"].strip()
    assert payload["versions"][0]["blocks"]
    assert len(payload["versions"][0]["blocks"]) >= 4
    assert payload["versions"][0]["blocks"][0]["role"] == "hook"

    generation_response = client.get(f"/api/v1/ai/generations/{payload['versions'][0]['generationId']}")
    assert generation_response.status_code == 200
    assert generation_response.json()["workflow"] == "script"


def test_create_script_draft_is_idempotent_for_topic_idea(monkeypatch) -> None:
    class CountingScriptProvider(MockChatProvider):
        def __init__(self) -> None:
            self.calls = 0

        def generate_json(self, *args, **kwargs):
            self.calls += 1
            return super().generate_json(*args, **kwargs)

    provider = CountingScriptProvider()
    monkeypatch.setattr("app.repositories.script_draft_repository.get_settings", lambda: Settings(postgres_host=""))
    monkeypatch.setattr("app.services.script_draft_service.get_settings", lambda: Settings(postgres_host=""))
    monkeypatch.setattr("app.services.script_draft_service.ai_provider_service.get_chat_provider", lambda: provider)

    payload = {"topicIdeaId": "tp_idempotent_script", "topic": "唯一选题生成脚本", "platform": "douyin"}
    first = client.post("/api/v1/scripts", json=payload)
    second = client.post("/api/v1/scripts", json=payload)

    assert first.status_code == 200
    assert second.status_code == 200
    assert second.json()["id"] == first.json()["id"]
    assert provider.calls == 1


def test_create_script_draft_is_idempotent_for_manual_topic(monkeypatch) -> None:
    class CountingScriptProvider(MockChatProvider):
        def __init__(self) -> None:
            self.calls = 0

        def generate_json(self, *args, **kwargs):
            self.calls += 1
            return super().generate_json(*args, **kwargs)

    provider = CountingScriptProvider()
    monkeypatch.setattr("app.repositories.script_draft_repository.get_settings", lambda: Settings(postgres_host=""))
    monkeypatch.setattr("app.services.script_draft_service.get_settings", lambda: Settings(postgres_host=""))
    monkeypatch.setattr("app.services.script_draft_service.ai_provider_service.get_chat_provider", lambda: provider)

    first = client.post("/api/v1/scripts", json={"topic": "手动唯一话题生成脚本", "platform": "douyin"})
    second = client.post("/api/v1/scripts", json={"topic": " 手动唯一话题生成脚本 ", "platform": "douyin"})

    assert first.status_code == 200
    assert second.status_code == 200
    assert second.json()["id"] == first.json()["id"]
    assert provider.calls == 1


def test_create_script_draft_accepts_top_level_script_body(monkeypatch) -> None:
    class TopLevelScriptProvider:
        def generate_json(self, *args, **kwargs):
            return {
                "scriptBody": "开头：这是顶层脚本文本。\n主体：用于验证真实 provider 返回结构。",
                "titles": [{"text": "顶层标题"}],
                "tags": ["#测试"],
            }

    monkeypatch.setattr("app.repositories.script_draft_repository.get_settings", lambda: Settings(postgres_host=""))
    monkeypatch.setattr("app.services.script_draft_service.get_settings", lambda: Settings(postgres_host=""))
    monkeypatch.setattr("app.services.script_draft_service.ai_provider_service.get_chat_provider", lambda: TopLevelScriptProvider())

    payload = ScriptDraftService(ScriptDraftRepository()).create_ai_initial_draft(ScriptDraftCreateRequest(topic="真实 provider 返回结构"))

    assert payload["currentVersion"]["body"].startswith("开头：这是顶层脚本文本")
    assert payload["currentVersion"]["titleCandidates"] == [{"text": "顶层标题"}]
    assert len(payload["currentVersion"]["blocks"]) == 2
    assert payload["currentVersion"]["blocks"][0]["voiceover"].startswith("这是顶层脚本文本")


def test_create_script_draft_falls_back_when_provider_omits_body(monkeypatch) -> None:
    class EmptyScriptProvider:
        def generate_json(self, *args, **kwargs):
            return {"drafts": {"titles": [{"text": "只有标题"}]}}

    monkeypatch.setattr("app.repositories.script_draft_repository.get_settings", lambda: Settings(postgres_host=""))
    monkeypatch.setattr("app.services.script_draft_service.get_settings", lambda: Settings(postgres_host=""))
    monkeypatch.setattr("app.services.script_draft_service.ai_provider_service.get_chat_provider", lambda: EmptyScriptProvider())

    payload = ScriptDraftService(ScriptDraftRepository()).create_ai_initial_draft(ScriptDraftCreateRequest(topic="选题转脚本兜底"))

    assert "选题转脚本兜底" in payload["currentVersion"]["body"]
    assert payload["currentVersion"]["body"].strip()
    assert payload["currentVersion"]["blocks"]


def test_save_script_version_and_adopt(monkeypatch) -> None:
    monkeypatch.setattr("app.repositories.script_draft_repository.get_settings", lambda: Settings(postgres_host=""))
    monkeypatch.setattr("app.services.script_draft_service.get_settings", lambda: Settings(postgres_host=""))
    monkeypatch.setattr("app.services.script_draft_service.ai_provider_service.get_chat_provider", lambda: MockChatProvider())

    created = client.post("/api/v1/scripts", json={"topic": "35 岁程序员岗位切换", "platform": "douyin"}).json()
    parent_version_id = created["currentVersionId"]

    saved = client.post(
        f"/api/v1/scripts/{created['id']}/versions",
        json={
            "body": "用户修改后的脚本正文",
            "blocks": [
                {
                    "id": "sb_test_hook",
                    "role": "hook",
                    "label": "开头钩子",
                    "voiceover": "用户修改后的脚本正文",
                    "visualHint": "正面半身，第一句直接看镜头。",
                    "durationSeconds": 5,
                }
            ],
            "label": "v2 用户修改",
            "sourceType": "user_save",
            "parentVersionId": parent_version_id,
        },
    )
    assert saved.status_code == 200
    payload = saved.json()
    assert payload["currentVersion"]["body"] == "用户修改后的脚本正文"
    assert payload["currentVersion"]["blocks"][0]["id"] == "sb_test_hook"
    assert payload["currentVersion"]["versionNo"] == 2
    assert payload["currentVersion"]["parentVersionId"] == parent_version_id

    adopted = client.patch(
        f"/api/v1/scripts/{created['id']}/versions/{payload['currentVersionId']}/status",
        json={"status": "adopted"},
    )
    assert adopted.status_code == 200
    assert adopted.json()["adoptedVersionId"] == payload["currentVersionId"]


def test_script_draft_not_found() -> None:
    missing = client.get("/api/v1/scripts/scr_missing")
    assert missing.status_code == 404

    missing_version = client.post("/api/v1/scripts/scr_missing/versions", json={"body": "x"})
    assert missing_version.status_code == 404


def test_script_repository_sqlite_persistence(monkeypatch) -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    monkeypatch.setattr("app.repositories.script_draft_repository.get_settings", lambda: Settings(postgres_host="localhost"))
    monkeypatch.setattr("app.repositories.script_draft_repository.get_admin_engine", lambda: engine)

    repo = ScriptDraftRepository()
    draft = repo.create_draft_with_initial_version(
        draft={
            "id": "scr_sqlite",
            "workspaceId": "ws_northstar",
            "topicIdeaId": None,
            "title": "SQLite 持久化脚本版本",
            "body": "第一版正文",
            "platform": "douyin",
            "status": "draft",
            "currentVersionId": "sv_sqlite_1",
            "adoptedVersionId": None,
        },
        version={
            "id": "sv_sqlite_1",
            "draftId": "scr_sqlite",
            "versionNo": 1,
            "label": "v1 AI 初稿",
            "platform": "douyin",
            "durationSeconds": 60,
            "body": "第一版正文",
            "blocks": [
                {
                    "id": "sb_sqlite_hook",
                    "role": "hook",
                    "label": "开头钩子",
                    "voiceover": "第一版正文",
                    "visualHint": "正面半身，第一句直接看镜头。",
                    "durationSeconds": 60,
                }
            ],
            "description": None,
            "tags": [],
            "titleCandidates": [],
            "sourceType": "ai_initial",
            "parentVersionId": None,
            "generationId": "gen_sqlite",
            "status": "candidate",
        },
        generation_id="gen_sqlite",
        generated={},
    )
    assert draft["versions"][0]["versionNo"] == 1
    assert draft["versions"][0]["blocks"][0]["id"] == "sb_sqlite_hook"
    assert repo.get_draft(draft["id"]) is not None
    assert repo.create_version(draft["id"], ScriptDraftVersionCreateRequest(body="第二版正文")) is not None


def test_collector_upload_creates_etl_task() -> None:
    response = client.post("/api/v1/collector/upload", json={"platform": "douyin", "payload": {"items": []}})
    assert response.status_code == 200
    payload = response.json()
    assert payload["rawId"].startswith("raw_")
    assert payload["status"] == "accepted"


def test_sqladmin_auth_backend_login_and_logout() -> None:
    auth_backend = AdminAuthBackend(
        secret_key="test-secret",
        username="admin",
        password="correct-password",
        role="owner",
    )

    from fastapi import FastAPI, Request

    auth_app = FastAPI()
    auth_app.add_middleware(SessionMiddleware, secret_key="test-secret")

    @auth_app.post("/login")
    async def login(request: Request):
        ok = await auth_backend.login(request)
        return JSONResponse({"ok": ok})

    @auth_app.get("/guard")
    async def guard(request: Request):
        result = await auth_backend.authenticate(request)
        if result is True:
            return JSONResponse({"ok": True})
        return result

    @auth_app.post("/logout")
    async def logout(request: Request):
        await auth_backend.logout(request)
        return PlainTextResponse("ok")

    auth_client = TestClient(auth_app)

    failed = auth_client.post("/login", data={"username": "admin", "password": "wrong"})
    assert failed.status_code == 200
    assert failed.json() == {"ok": False}

    blocked = auth_client.get("/guard", follow_redirects=False)
    assert blocked.status_code == 302

    logged_in = auth_client.post("/login", data={"username": "admin", "password": "correct-password"})
    assert logged_in.status_code == 200
    assert logged_in.json() == {"ok": True}

    allowed = auth_client.get("/guard")
    assert allowed.status_code == 200
    assert allowed.json() == {"ok": True}

    auth_client.post("/logout")
    logged_out = auth_client.get("/guard", follow_redirects=False)
    assert logged_out.status_code == 302


def test_sqladmin_role_permissions() -> None:
    assert admin_role_permissions("owner")["can_delete"] is True
    assert admin_role_permissions("admin")["can_delete"] is False
    assert admin_role_permissions("admin")["can_edit"] is True
    assert admin_role_permissions("viewer")["can_create"] is False
    assert admin_role_permissions("unknown")["can_export"] is True


def test_agent_topic_workbench_run_and_debug_contract(monkeypatch) -> None:
    mock_provider = MockChatProvider()
    monkeypatch.setattr("app.agents.chains.strategy_chain.strategy_chain.chat_provider", mock_provider)
    monkeypatch.setattr("app.agents.chains.script_chain.script_chain.chat_provider", mock_provider)
    monkeypatch.setattr("app.agents.chains.qa_chain.qa_chain.chat_provider", mock_provider)

    response = client.post(
        "/api/v1/agent/topic-workbench/run",
        json={
            "threadId": "th_test_topic_001",
            "workspaceId": "ws_northstar",
            "memberId": "m_demo",
            "accountId": "douyin_demo",
            "platform": "douyin",
            "taskType": "topic_to_qa",
            "topic": "程序员 35 岁危机",
            "targetDurationSeconds": 45,
            "constraints": {"tone": "普通人视角", "avoid": ["大厂精英口吻"]},
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["runId"].startswith("run_")
    assert payload["status"] == "succeeded"
    assert "qaReport" in payload
    assert payload["evidence"][0]["memoryId"].startswith("mem_")
    assert payload["inferences"]

    run_id = payload["runId"]
    run = client.get(f"/api/v1/agent/runs/{run_id}")
    assert run.status_code == 200
    assert run.json()["status"] == "succeeded"

    steps = client.get(f"/api/v1/agent/runs/{run_id}/steps")
    assert steps.status_code == 200
    assert {step["nodeName"] for step in steps.json()} >= {"retrieve_memories", "qa_content", "compress_thread_memory"}

    traces = client.get(f"/api/v1/agent/runs/{run_id}/retrieval-traces")
    assert traces.status_code == 200
    assert traces.json()[0]["topK"] == 8

    summary = client.get("/api/v1/agent/threads/th_test_topic_001/summary")
    assert summary.status_code == 200
    assert summary.json()["threadId"] == "th_test_topic_001"


def test_memory_record_lifecycle_and_search() -> None:
    created = client.post(
        "/api/v1/memory/records",
        json={
            "workspaceId": "ws_northstar",
            "accountId": "douyin_demo",
            "platform": "douyin",
            "memoryType": "content_case",
            "title": "普通程序员三条路线",
            "content": "普通程序员在 AI 时代可以走方案、产品化、自动化三条路线。",
            "summary": "普通程序员路线型内容适合搜索流量。",
            "confidence": 0.77,
            "evidenceCount": 2,
        },
    )
    assert created.status_code == 200
    memory_id = created.json()["id"]
    assert created.json()["status"] == "candidate"

    activated = client.post(f"/api/v1/memory/records/{memory_id}/activate")
    assert activated.status_code == 200
    assert activated.json()["status"] == "active"

    search = client.post(
        "/api/v1/memory/search",
        json={
            "query": "普通程序员 AI 三条路线",
            "workspaceId": "ws_northstar",
            "accountId": "douyin_demo",
            "platform": "douyin",
            "memoryTypes": ["content_case"],
            "status": "active",
            "topK": 5,
        },
    )
    assert search.status_code == 200
    assert any(item["memoryId"] == memory_id for item in search.json()["results"])

    rejected = client.post(f"/api/v1/memory/records/{memory_id}/reject")
    assert rejected.status_code == 200
    assert rejected.json()["status"] == "rejected"


def test_provider_defaults_and_embedding_dimension() -> None:
    settings = Settings(dashscope_api_key=None, deepseek_api_key=None)
    assert settings.deepseek_model == "deepseek-v4-flash"
    assert settings.dashscope_embedding_model == "text-embedding-v3"
    assert settings.dashscope_embedding_dimension == 1024

    embedding = MockEmbeddingProvider(settings.dashscope_embedding_dimension).embed_query("hello")
    assert len(embedding) == 1024

    dashscope = DashScopeEmbeddingProvider(settings)
    assert len(dashscope.embed_query("hello")) == 1024

    deepseek = DeepSeekChatProvider(settings)
    try:
        deepseek.generate_json("test", "system", "topic", {"topic": "测试"}, {})
    except RuntimeError as exc:
        assert "VO_MATE_DEEPSEEK_API_KEY" in str(exc)


def _parse_sse_events(body: str) -> list[dict[str, object]]:
    events = []
    for raw_event in body.strip().split("\n\n"):
        event_name = ""
        event_data = ""
        for line in raw_event.splitlines():
            if line.startswith("event: "):
                event_name = line.removeprefix("event: ")
            if line.startswith("data: "):
                event_data = line.removeprefix("data: ")
        events.append({"event": event_name, "data": json.loads(event_data)})
    return events
