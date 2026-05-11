import json

from fastapi.testclient import TestClient
from starlette.middleware.sessions import SessionMiddleware
from starlette.responses import JSONResponse, PlainTextResponse

from app.core.admin_auth import AdminAuthBackend, admin_role_permissions
from app.core.config import Settings
from app.repositories.topic_idea_repository import topic_idea_repository
from app.services.ai_provider_service import DashScopeEmbeddingProvider, DeepSeekChatProvider, MockEmbeddingProvider

from app.main import app

client = TestClient(app)


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


def test_ai_task_creation() -> None:
    response = client.post("/api/v1/ai/script", json={"topicId": "tp_role_shift"})
    assert response.status_code == 200
    payload = response.json()
    assert payload["id"].startswith("task_script_")
    assert payload["status"] == "pending"


def test_topic_ideas_streams_results() -> None:
    response = client.post(
        "/api/v1/ai/topic-ideas",
        json={
            "direction": "程序员职业成长",
            "platforms": ["douyin", "xiaohongshu"],
            "goal": "followers",
            "count": 10,
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
    assert len(topic_events) == 10
    assert "predictedScore" in topic_events[0]["data"]
    assert "recommendReason" in topic_events[0]["data"]
    assert topic_events[0]["data"]["targetPlatforms"] == ["douyin", "xiaohongshu"]
    assert events[-1]["data"]["count"] == 10
    assert len(events[-1]["data"]["topicIdeas"]) == 10

    generation = topic_idea_repository.get_generation(events[-1]["data"]["generationId"])
    assert generation is not None
    assert generation["status"] == "succeeded"
    assert generation["workflow"] == "topic-ideas"
    assert generation["inputPayload"]["dataSourceMode"] == "memory_fallback"
    assert generation["outputPayload"]["count"] == 10

    generation_response = client.get(f"/api/v1/ai/generations/{events[-1]['data']['generationId']}")
    assert generation_response.status_code == 200
    assert generation_response.json()["status"] == "succeeded"

    listed = client.get("/api/v1/ai/topic-ideas")
    assert listed.status_code == 200
    assert any(item["generationId"] == events[-1]["data"]["generationId"] for item in listed.json())


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


def test_topic_ideas_can_hide_evidence_details() -> None:
    response = client.post(
        "/api/v1/ai/topic-ideas",
        json={
            "direction": "程序员职业成长",
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
    class FailingProvider:
        def generate_json(self, *args, **kwargs):
            raise RuntimeError("provider unavailable")

    monkeypatch.setattr(
        "app.services.topic_idea_service.ai_provider_service.get_chat_provider",
        lambda: FailingProvider(),
    )
    response = client.post(
        "/api/v1/ai/topic-ideas",
        json={"direction": "程序员职业成长", "platforms": ["douyin"]},
    )

    assert response.status_code == 200
    events = _parse_sse_events(response.text)
    assert events[-1]["event"] == "error"
    assert events[-1]["data"]["code"] == "RuntimeError"

    generation = topic_idea_repository.get_generation(events[-1]["data"]["generationId"])
    assert generation is not None
    assert generation["status"] == "failed"
    assert generation["error"] == "provider unavailable"


def test_topic_ideas_use_postgres_evidence_when_available(monkeypatch) -> None:
    captured_context = {}

    class CapturingProvider:
        def generate_json(self, task, system_prompt, user_input, context, schema):
            captured_context.update(context)
            return {
                "candidates": [
                    {
                        "title": "真实内容数据驱动的选题",
                        "angle": "结合历史高分内容和长期记忆生成。",
                        "predictedScore": 91,
                        "seoScore": 88,
                        "audienceScore": 86,
                        "difficultyScore": 43,
                        "risk": "需要补充具体案例。",
                    }
                ]
            }

    monkeypatch.setattr(
        "app.services.topic_idea_service.ai_provider_service.get_chat_provider",
        lambda: CapturingProvider(),
    )
    monkeypatch.setattr(
        "app.services.topic_evidence_service.topic_evidence_service.evidence_repository.load_content_metrics",
        lambda request: [
            {
                "id": "ct_pg_1",
                "contentId": "ct_pg_1",
                "sourceType": "postgres_content",
                "sourceId": "ct_pg_1",
                "title": "PG 高表现历史内容",
                "platform": "douyin",
                "views": 120000,
                "likes": 8000,
                "comments": 500,
                "saves": 1200,
                "shares": 300,
                "completionRate": 0.42,
                "followersGained": 430,
                "score": 92,
                "hasAsr": True,
                "reviewed": True,
            }
        ],
    )
    monkeypatch.setattr(
        "app.services.topic_evidence_service.topic_evidence_service.evidence_repository.retrieve_topic_memories",
        lambda request: [
            {
                "id": "mem_pg_1",
                "memoryId": "mem_pg_1",
                "sourceType": "postgres_memory",
                "sourceId": "mem_pg_1",
                "memoryType": "success_pattern",
                "title": "PG 成功模式",
                "summary": "真实长期记忆摘要",
                "score": 0.91,
                "reason": "命中成功模式",
            }
        ],
    )

    response = client.post(
        "/api/v1/ai/topic-ideas",
        json={"direction": "真实数据选题", "platforms": ["douyin"], "count": 2},
    )

    assert response.status_code == 200
    events = _parse_sse_events(response.text)
    assert events[-1]["event"] == "done"
    assert captured_context["dataSourceMode"] == "postgres"
    assert captured_context["contentMetrics"][0]["sourceType"] == "postgres_content"
    assert captured_context["evidence"][0]["sourceType"] == "postgres_memory"

    generation = topic_idea_repository.get_generation(events[-1]["data"]["generationId"])
    assert generation is not None
    assert generation["inputPayload"]["dataSourceMode"] == "postgres"
    assert generation["evidenceIds"] == ["mem_pg_1"]


def test_topic_ideas_prefer_milvus_evidence_when_available(monkeypatch) -> None:
    captured_context = {}

    class CapturingProvider:
        def generate_json(self, task, system_prompt, user_input, context, schema):
            captured_context.update(context)
            return {
                "candidates": [
                    {
                        "title": "向量记忆驱动的选题",
                        "angle": "优先使用 Milvus 命中的长期记忆。",
                        "predictedScore": 93,
                        "seoScore": 89,
                        "audienceScore": 87,
                        "difficultyScore": 41,
                        "risk": "需要补充案例细节。",
                    }
                ]
            }

    monkeypatch.setattr(
        "app.services.topic_idea_service.ai_provider_service.get_chat_provider",
        lambda: CapturingProvider(),
    )
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
        json={"direction": "向量选题", "platforms": ["douyin"], "count": 1},
    )

    assert response.status_code == 200
    events = _parse_sse_events(response.text)
    assert events[-1]["event"] == "done"
    assert captured_context["dataSourceMode"] == "milvus"
    assert captured_context["evidence"][0]["sourceType"] == "milvus_memory"

    generation = topic_idea_repository.get_generation(events[-1]["data"]["generationId"])
    assert generation is not None
    assert generation["inputPayload"]["dataSourceMode"] == "milvus"
    assert generation["evidenceIds"] == ["mem_milvus_1"]


def test_topic_ideas_fall_back_to_postgres_when_milvus_fails(monkeypatch) -> None:
    captured_context = {}

    class CapturingProvider:
        def generate_json(self, task, system_prompt, user_input, context, schema):
            captured_context.update(context)
            return {
                "candidates": [
                    {
                        "title": "PG 降级选题",
                        "angle": "Milvus 失败后使用 PostgreSQL 证据。",
                        "predictedScore": 90,
                        "seoScore": 86,
                        "audienceScore": 85,
                        "difficultyScore": 44,
                        "risk": "需要补充案例。",
                    }
                ]
            }

    def fail_milvus(request):
        raise RuntimeError("milvus unavailable")

    monkeypatch.setattr(
        "app.services.topic_idea_service.ai_provider_service.get_chat_provider",
        lambda: CapturingProvider(),
    )
    monkeypatch.setattr("app.services.topic_evidence_service.memory_vector_service.search_milvus_hits", fail_milvus)
    monkeypatch.setattr(
        "app.services.topic_evidence_service.topic_evidence_service.evidence_repository.retrieve_topic_memories",
        lambda request: [
            {
                "id": "mem_pg_after_milvus_failure",
                "memoryId": "mem_pg_after_milvus_failure",
                "sourceType": "postgres_memory",
                "sourceId": "mem_pg_after_milvus_failure",
                "memoryType": "success_pattern",
                "title": "PG 降级模式",
                "summary": "Milvus 不可用时仍可生成。",
                "score": 0.9,
                "reason": "关键词命中",
            }
        ],
    )

    response = client.post(
        "/api/v1/ai/topic-ideas",
        json={"direction": "降级选题", "platforms": ["douyin"], "count": 1},
    )

    assert response.status_code == 200
    events = _parse_sse_events(response.text)
    assert events[-1]["event"] == "done"
    assert captured_context["dataSourceMode"] == "postgres"
    assert captured_context["evidence"][0]["sourceType"] == "postgres_memory"


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


def test_agent_topic_workbench_run_and_debug_contract() -> None:
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
    result = deepseek.generate_json("test", "system", "topic", {"topic": "测试"}, {})
    assert result["topic"] == "测试"


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
