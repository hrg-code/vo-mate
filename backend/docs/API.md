# AI 自媒体工作台服务端接口文档

版本：v0.1  
服务端：FastAPI  
默认地址：`http://localhost:8000`  
接口前缀：`/api/v1`  
数据格式：`application/json`

## 1. 通用约定

### 1.1 启动服务

```bash
cd backend
python3 -m uvicorn app.main:app --reload --port 8000
```

### 1.2 前端联调配置

```bash
VITE_USE_MOCKS=false
VITE_API_BASE_URL=http://localhost:8000/api/v1
```

### 1.3 后端 `.env` 配置

服务端启动时读取 `backend/.env`。默认仓库提供的 `.env` 将外部依赖地址留空，服务会跳过连接；填入对应地址后重启服务即可连接 PostgreSQL、MongoDB、Redis 和 Milvus。

```env
VO_MATE_POSTGRES_HOST="localhost"
VO_MATE_POSTGRES_PORT=5432
VO_MATE_POSTGRES_USER="vo_mate"
VO_MATE_POSTGRES_PASSWORD="vo_mate"
VO_MATE_POSTGRES_DATABASE="vo_mate"
VO_MATE_POSTGRES_MIN_POOL_SIZE=1
VO_MATE_POSTGRES_MAX_POOL_SIZE=5

VO_MATE_MONGO_HOST="localhost"
VO_MATE_MONGO_PORT=27017
VO_MATE_MONGO_USER=
VO_MATE_MONGO_PASSWORD=
VO_MATE_MONGO_DATABASE="vo_mate"
VO_MATE_MONGO_AUTH_SOURCE="admin"

VO_MATE_REDIS_HOST="localhost"
VO_MATE_REDIS_PORT=6379
VO_MATE_REDIS_DATABASE=0
VO_MATE_REDIS_USER=
VO_MATE_REDIS_PASSWORD=

VO_MATE_MILVUS_HOST="localhost"
VO_MATE_MILVUS_PORT=19530
VO_MATE_MILVUS_SECURE=false
VO_MATE_MILVUS_TOKEN=
VO_MATE_MILVUS_DATABASE=

VO_MATE_SQLADMIN_ENABLED=true
VO_MATE_SQLADMIN_TITLE="VO Mate Admin"
VO_MATE_SQLADMIN_BASE_URL="/admin"
VO_MATE_SQLADMIN_AUTO_CREATE_TABLES=false
VO_MATE_SQLADMIN_AUTH_ENABLED=true
VO_MATE_SQLADMIN_USERNAME="admin"
VO_MATE_SQLADMIN_PASSWORD="change-me"
VO_MATE_SQLADMIN_PASSWORD_SHA256=
VO_MATE_SQLADMIN_SESSION_SECRET="replace-with-a-long-random-session-secret"
VO_MATE_SQLADMIN_ROLE="owner"
```

### 1.4 后端管理

服务已接入 SQLAdmin 管理后台。

```text
http://localhost:8000/admin
```

说明：

- SQLAdmin 使用 PostgreSQL 配置连接数据库。
- 默认不自动创建表：`VO_MATE_SQLADMIN_AUTO_CREATE_TABLES=false`。
- 默认启用后台登录认证：`VO_MATE_SQLADMIN_AUTH_ENABLED=true`。
- 后台角色：`owner` 可删除，`admin` 可新增和编辑但不可删除，`viewer` 只读。
- 当前已注册管理视图：`workspaces`、`users`、`workspace_members`、`platform_accounts`、`content_items`、`content_lifetime_metrics`、`content_text_assets`、`content_tags`、`content_keywords`、`content_traffic_sources`、`topic_ideas`、`ai_generations`、`script_drafts`、`script_draft_versions`、`publish_plans`、`memory_patterns`、`collector_tasks`。

### 1.5 响应格式

当前 MVP 直接返回业务对象或业务数组。错误响应遵循 FastAPI 默认格式：

```json
{
  "detail": "Content not found"
}
```

### 1.6 枚举

`platform`：

```text
douyin | kuaishou | xiaohongshu | youtube | wechat
```

`task.status`：

```text
pending | running | requires_action | succeeded | failed | cancelled
```

`content.status`：

```text
published | needs_review | script_reusable | seo_opportunity
```

## 2. 数据结构

### 2.1 WorkspaceContext

```json
{
  "workspaceId": "ws_northstar",
  "workspaceName": "北极星内容组",
  "accountName": "抖音 · 程序员老陈",
  "platformScope": ["douyin"]
}
```

### 2.2 MetricSummary

```json
{
  "label": "播放量",
  "value": "34.6w",
  "delta": "+42%",
  "direction": "up",
  "description": "较账号 30 日中位数"
}
```

### 2.3 ContentItem

```json
{
  "id": "ct_7585913482206383412",
  "title": "程序员 35 岁后还能不能继续写代码",
  "platform": "douyin",
  "publishedAt": "2026-05-08",
  "durationSeconds": 62,
  "views": 346000,
  "likes": 19000,
  "comments": 892,
  "saves": 4320,
  "shares": 1182,
  "completionRate": 0.38,
  "followersGained": 1286,
  "score": 89,
  "status": "published",
  "hasAsr": true,
  "reviewed": true
}
```

### 2.4 TopicIdea

```json
{
  "id": "tp_role_shift",
  "title": "35 岁程序员不是危机，是岗位切换信号",
  "topic": "程序员职业成长",
  "angle": "把年龄焦虑改写成职业策略，适合 60 秒强钩子口播。",
  "category": "career_growth",
  "targetAudience": "25-35 岁普通程序员",
  "predictedScore": 91,
  "seoScore": 86,
  "audienceScore": 93,
  "difficultyScore": 41,
  "risk": "情绪过强会降低完播",
  "recommendReason": "历史职业焦虑内容评论强，适合改写成更可执行的岗位切换策略。",
  "evidenceCount": 12,
  "targetPlatforms": ["douyin", "xiaohongshu"],
  "evidence": [],
  "suggestedTitles": ["35 岁程序员不是危机，是岗位切换信号"],
  "suggestedHooks": ["如果你也在担心 35 岁，先别急着否定自己。"],
  "suggestedTags": ["#程序员", "#职业规划"],
  "nextActions": ["generate_titles", "generate_script", "save_to_topic_pool"],
  "generationId": "gen_xxx"
}
```

### 2.5 EvidenceItem

```json
{
  "id": "ev_content_1",
  "type": "content",
  "title": "程序员 35 岁后还能不能继续写代码",
  "description": "播放 34.6w，完播 38%，涨粉 1,286，相关性 94%。",
  "source": "PostgreSQL content_items + douyin_video_raw",
  "score": 94
}
```

### 2.6 AgentTask

```json
{
  "id": "task_script_a0d6cdbb",
  "name": "AI script",
  "status": "pending",
  "progress": 0,
  "currentStep": "Queued",
  "traceId": "tr_b5a3a26ada",
  "result": {
    "acceptedPayload": {
      "topicId": "tp_role_shift"
    }
  }
}
```

### 2.7 MemoryPattern

```json
{
  "id": "mem_success_1",
  "type": "success",
  "summary": "职场焦虑类内容必须在 15 秒内给出第一个解决动作。",
  "confidence": 0.82,
  "sourceCount": 14,
  "lastVerifiedAt": "2026-05-09"
}
```

### 2.8 PublishPlan

```json
{
  "id": "plan_1",
  "title": "AI 时代程序员机会",
  "platform": "douyin",
  "scheduledAt": "今天 18:30",
  "stage": "idea"
}
```

## 3. 健康检查

### GET /health

说明：检查服务是否可用。

响应：

```json
{
  "status": "ok"
}
```

### GET /api/v1/system/dependencies

说明：检查 PostgreSQL、MongoDB、Redis、Milvus 的配置和连接状态。未配置的服务会返回 `configured: false`。

响应：

```json
{
  "postgres": {
    "configured": false,
    "connected": false
  },
  "mongodb": {
    "configured": false,
    "connected": false
  },
  "redis": {
    "configured": false,
    "connected": false
  },
  "milvus": {
    "configured": false,
    "connected": false
  }
}
```

## 4. Auth

### POST /api/v1/auth/login

说明：开发期登录接口。当前 MVP 不校验账号密码。

请求体：

```json
{
  "username": "demo",
  "password": "demo"
}
```

响应：

```json
{
  "accessToken": "dev-token",
  "tokenType": "bearer"
}
```

### POST /api/v1/auth/logout

响应：

```json
{
  "ok": true
}
```

### GET /api/v1/auth/me

响应：

```json
{
  "id": "user_dev",
  "name": "开发用户",
  "role": "owner"
}
```

## 5. Workspace

### GET /api/v1/workspaces/current

说明：获取当前工作区上下文。

响应：`WorkspaceContext`

```json
{
  "workspaceId": "ws_northstar",
  "workspaceName": "北极星内容组",
  "accountName": "抖音 · 程序员老陈",
  "platformScope": ["douyin"]
}
```

## 6. Analytics

### GET /api/v1/analytics/dashboard

说明：获取首页看板数据。该接口已对齐前端 `api.getDashboard()`。

响应：

```json
{
  "metrics": [
    {
      "label": "播放量",
      "value": "34.6w",
      "delta": "+42%",
      "direction": "up",
      "description": "较账号 30 日中位数"
    }
  ],
  "contents": [
    {
      "id": "ct_7585913482206383412",
      "title": "程序员 35 岁后还能不能继续写代码",
      "platform": "douyin",
      "publishedAt": "2026-05-08",
      "durationSeconds": 62,
      "views": 346000,
      "likes": 19000,
      "comments": 892,
      "saves": 4320,
      "shares": 1182,
      "completionRate": 0.38,
      "followersGained": 1286,
      "score": 89,
      "status": "published",
      "hasAsr": true,
      "reviewed": true
    }
  ],
  "tasks": [
    {
      "id": "task_topic_001",
      "name": "AI 选题生成",
      "status": "running",
      "progress": 68,
      "currentStep": "Analyze Performance Pattern",
      "traceId": "tr_9a23_topic",
      "result": null
    }
  ]
}
```

### GET /api/v1/analytics/dashboard/overview

说明：SRD 中 `GET /dashboard/overview` 的当前实现路径，返回内容同 `/analytics/dashboard`。

响应：同 `GET /api/v1/analytics/dashboard`

## 7. Contents

### GET /api/v1/contents

说明：获取统一内容列表。

响应：`ContentItem[]`

### GET /api/v1/contents/{content_id}

说明：获取单条内容详情。

路径参数：

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `content_id` | string | 是 | 内容 ID |

响应：`ContentItem`

### GET /api/v1/contents/{content_id}/metrics

说明：获取单条内容核心指标。

响应：

```json
{
  "views": 346000,
  "engagementRate": 0.0734,
  "completionRate": 0.38,
  "followersGained": 1286,
  "score": 89
}
```

### GET /api/v1/contents/{content_id}/analysis

说明：获取单条内容分析。

响应：

```json
{
  "contentId": "ct_7585913482206383412",
  "summary": "该内容适合进入复盘池，重点检查开头钩子、搜索关键词和收藏动机。",
  "strengths": ["话题焦虑明确", "评论互动充足", "涨粉转化高于近期均值"],
  "risks": ["完播率仍有优化空间"]
}
```

### GET /api/v1/contents/{content_id}/asr

说明：获取单条内容 ASR 文本。

响应：

```json
{
  "contentId": "ct_7585913482206383412",
  "text": "完整 ASR 文本",
  "language": "zh",
  "durationSeconds": 60,
  "segments": [
    {
      "start": 0.0,
      "end": 2.19,
      "text": "程序员能干一辈子吗？"
    }
  ]
}
```

## 8. Scripts

### GET /api/v1/scripts

说明：获取脚本草稿列表，包含当前版本摘要。PostgreSQL 已配置且执行过 `backend/docs/schema/script_drafts.sql` 时优先读取数据库，否则使用内存仓库。

响应：`ScriptDraftSummary[]`

### GET /api/v1/scripts/{draft_id}

说明：获取单个脚本草稿详情、版本列表和当前打开版本。

响应：

```json
{
  "id": "scr_xxx",
  "workspaceId": "ws_northstar",
  "topicIdeaId": "tp_role_shift",
  "topic": "35 岁程序员不是危机，是岗位切换信号",
  "title": "35 岁程序员不是危机，是岗位切换信号",
  "body": "当前版本正文",
  "platform": "douyin",
  "status": "draft",
  "currentVersionId": "sv_xxx",
  "adoptedVersionId": null,
  "currentVersion": {
    "id": "sv_xxx",
    "draftId": "scr_xxx",
    "versionNo": 1,
    "label": "v1 AI 初稿",
    "sourceType": "ai_initial",
    "generationId": "gen_xxx",
    "status": "candidate",
    "body": "脚本正文",
    "blocks": [
      {
        "id": "sb_hook_xxx",
        "role": "hook",
        "label": "开头钩子",
        "voiceover": "前 3 秒口播正文",
        "visualHint": "正面半身，第一句直接看镜头。",
        "durationSeconds": 5
      }
    ]
  },
  "versions": []
}
```

### POST /api/v1/scripts

说明：从选题或手动主题创建脚本草稿，并创建 `v1 AI 初稿`。该接口会调用现有 AI Provider 的脚本生成能力，并记录 `ai_generations` 审计记录。
响应中的 `body` 是兼容文本镜像，结构化脚本以 `blocks` 为准。
同一 `workspaceId + topicIdeaId` 只会保留一个脚本草稿；未传 `topicIdeaId` 时，同一 `workspaceId + topic` 只会保留一个脚本草稿。重复请求直接返回已有草稿，不会再次生成。

请求体：

```json
{
  "workspaceId": "ws_northstar",
  "topicIdeaId": "tp_role_shift",
  "topic": "35 岁程序员不是危机，是岗位切换信号",
  "platform": "douyin",
  "durationSeconds": 60
}
```

### POST /api/v1/scripts/{draft_id}/versions

说明：基于当前编辑正文保存一个新版本。用户手动保存不会强制创建 AI 生成审计记录，`generationId` 可为空。

请求体：

```json
{
  "body": "用户修改后的脚本正文",
  "blocks": [
    {
      "id": "sb_hook_xxx",
      "role": "hook",
      "label": "开头钩子",
      "voiceover": "用户修改后的开头口播",
      "visualHint": "正面半身，第一句直接看镜头。",
      "durationSeconds": 5
    }
  ],
  "label": "v2 用户修改",
  "sourceType": "user_save",
  "parentVersionId": "sv_parent"
}
```

### PATCH /api/v1/scripts/{draft_id}/versions/{version_id}/status

说明：标记版本状态。`status=adopted` 时同步更新草稿的 `adoptedVersionId`。

请求体：

```json
{"status": "adopted"}
```

### PATCH /api/v1/scripts/{draft_id}/current-version

说明：切换脚本工作台当前打开版本，并同步 `script_drafts.body` 为该版本正文镜像。

请求体：

```json
{"versionId": "sv_xxx"}
```

## 9. AI

### GET /api/v1/ai/topic-ideas

说明：获取选题候选列表。该接口已对齐前端 `api.getTopicIdeas()`。如果 PostgreSQL 已配置且执行过 `backend/docs/schema/topic_ideas.sql`，优先读取 `topic_ideas`；否则返回内存仓库中的候选。

响应：`TopicIdea[]`

### POST /api/v1/ai/topic-ideas

说明：直接生成 AI 选题候选，并以 SSE 流式返回结果。该接口不再创建后台任务，也不需要前端轮询任务状态。该生成链路采用真实依赖 fail-closed 策略：必须配置 `VO_MATE_LLM_PROVIDER=deepseek`、`VO_MATE_DEEPSEEK_API_KEY`、PostgreSQL 连接、workspace/account、真实内容证据、真实长期记忆，以及 `topic_ideas` / `ai_generations` 表。任何必需依赖缺失都会返回 SSE `error` 事件，不再降级到 mock provider 或内存样例。

持久化：接口必须写入 PostgreSQL `topic_ideas` 和 `ai_generations` 审计记录。PostgreSQL 未配置、表未创建或写入失败时，本次生成失败；不会写入内存仓库。

证据来源：接口会先按 workspace、account、platform 和 published 状态读取 PostgreSQL 分层内容证据，生成上下文包含 `relatedContents`、`topPerformers`、`contrastContents` 和 `retrievalDiagnostics`。如果精确账号下没有真实内容证据，接口失败，不再混入 `platform_account_id IS NULL` 的旧数据，也不再读取内存样例。Milvus / DashScope 向量检索是可选增强：只有 `VO_MATE_MILVUS_HOST`、`VO_MATE_EMBEDDING_PROVIDER=dashscope`、`VO_MATE_DASHSCOPE_API_KEY` 同时配置时才会参与内容和记忆向量召回；否则跳过向量路径，并使用 PostgreSQL `agent_memory_records` 关键词召回真实记忆。审计记录的 `inputPayload.dataSourceMode` 只应出现 `milvus`、`postgres` 或 `postgres_no_vector`。

内测数据：本地或内测库可执行 `backend/docs/schema/topic_ideas_dev_seed.sql` 写入 `ws_northstar` / `douyin_demo` 的 workspace、账号、历史内容、语义富化和长期记忆，用于跑通该接口的真实 PostgreSQL 证据链。

请求体：

```json
{
  "workspaceId": "ws_northstar",
  "accountIds": ["douyin_demo"],
  "direction": "程序员职业成长",
  "platforms": ["douyin", "xiaohongshu"],
  "goal": "followers",
  "count": 10,
  "audience": "25-35 岁普通程序员",
  "constraints": {
    "tone": "理性但有冲突感",
    "avoidTopics": ["裁员恐慌"]
  },
  "includeEvidence": true
}
```

响应：`text/event-stream`

事件：

```text
event: start
data: {"workflow":"topic-ideas","generationId":"gen_xxx","promptVersion":"v0.2","providerDiagnostics":{"llmProvider":"deepseek","deepseekKeyConfigured":true,"embeddingProvider":"dashscope",...},"acceptedPayload":{...}}

event: progress
data: {"step":"load_topic_content_evidence","message":"已读取分层历史内容证据。"}

event: evidence
data: {"items":[{"memoryId":"mem_pg_1","memoryType":"content_case","sourceType":"postgres_memory",...}]}

event: topic_idea
data: {"id":"tp_role_shift","title":"35 岁程序员不是危机，是岗位切换信号","recommendReason":"...",...}

event: done
data: {"generationId":"gen_xxx","count":10,"topicIdeas":[...]}
```

异常事件：

```text
event: error
data: {"generationId":"gen_xxx","code":"LLM_TIMEOUT","message":"选题生成超时，请稍后重试"}
```

### GET /api/v1/ai/generations/{generation_id}

说明：查看单次 AI 选题生成审计记录。用于调试实际使用的数据源、输入、证据 ID、输出和错误。

响应：

```json
{
  "id": "gen_xxx",
  "workspaceId": "ws_northstar",
  "workflow": "topic-ideas",
  "provider": "mock",
  "model": null,
  "promptVersion": "v0.1",
  "inputPayload": {"dataSourceMode": "milvus"},
  "evidenceIds": ["mem_pg_1"],
  "outputPayload": {"count": 10, "topicIdeas": []},
  "error": null,
  "status": "succeeded"
}
```

### GET /api/v1/ai/evidence

说明：获取 AI 建议依据列表。该接口已对齐前端 `api.getEvidence()` 和 Evidence Drawer，可按生成记录查看某次选题生成实际依据，也可按当前 workspace/account/platform/direction 预览 PostgreSQL 证据池。

Query：

```text
generationId  可选；传入后优先按 ai_generations 审计记录返回本次生成依据
workspaceId   可选；默认 ws_northstar
accountId     可选；默认 douyin_demo
platform      可选；默认 douyin
direction     可选；传入后召回方向相关内容和记忆
limit         可选；默认 20，范围 1-100
```

行为：

- `generationId` 有值时，忽略其他实时查询条件；从 `ai_generations` 的输入、输出和 evidence ids 聚合 UI 友好依据。
- `generationId` 无值但有查询条件时，读取 PostgreSQL 内容证据和 active 长期记忆。
- 无查询参数时，使用默认 `ws_northstar` / `douyin_demo` / `douyin` / `程序员职业成长` 查询真实 PostgreSQL 证据。
- PostgreSQL 证据不可用或为空时返回错误，不返回 mock 或内存样例。

响应：`EvidenceItem[]`

```json
[
  {
    "id": "ct_inner_pg_001",
    "type": "content",
    "title": "程序员副业接私活真实复盘：第一单到底亏在哪",
    "description": "命中当前方向相关词：程序员, 副业",
    "source": "postgres_content",
    "score": 94,
    "metrics": ["播放 186400", "完播率 46%"],
    "action": "当前方向相关历史内容"
  }
]
```


### POST /api/v1/ai/{workflow}

说明：创建通用 AI 工作流任务。适用于 SRD 中的脚本、标题、SEO、复盘、多平台改写等任务。

常见 `workflow`：

```text
script | title | seo | review-content | video-retrospective | multi-platform-rewrite
```

请求示例：

```json
{
  "topicId": "tp_role_shift",
  "platform": "douyin",
  "durationSeconds": 60
}
```

响应：`AgentTask`

## 9. Memory

### GET /api/v1/memory/patterns

说明：获取成功/失败/SEO/钩子等记忆模式。

响应：`MemoryPattern[]`

### POST /api/v1/memory/patterns

说明：新增记忆模式。

请求体：

```json
{
  "type": "success",
  "summary": "先承认焦虑，再给可执行步骤，收藏率更高。",
  "confidence": 0.72,
  "sourceCount": 3,
  "lastVerifiedAt": "2026-05-10"
}
```

响应：`MemoryPattern`

### PATCH /api/v1/memory/patterns/{pattern_id}

说明：更新记忆模式。

请求体：

```json
{
  "confidence": 0.81,
  "sourceCount": 5
}
```

响应：`MemoryPattern`

### DELETE /api/v1/memory/patterns/{pattern_id}

说明：删除记忆模式。

响应：

```json
{
  "deleted": true
}
```

### POST /api/v1/memory/search

说明：搜索向量记忆。当前 MVP 返回样例证据，后续接 Milvus。

请求体：

```json
{
  "query": "35 岁程序员转型",
  "limit": 5
}
```

响应：

```json
{
  "query": "35 岁程序员转型",
  "results": [
    {
      "id": "ev_content_1",
      "type": "content",
      "title": "程序员 35 岁后还能不能继续写代码",
      "description": "播放 34.6w，完播 38%，涨粉 1,286，相关性 94%。",
      "source": "PostgreSQL content_items + douyin_video_raw",
      "score": 94
    }
  ]
}
```

### POST /api/v1/memory/index-content

说明：创建内容向量化任务。

请求体：

```json
{
  "contentId": "ct_7585913482206383412"
}
```

响应：

```json
{
  "taskId": "task_memory-index-content_xxxxxxxx",
  "status": "pending"
}
```

## 10. Workflows

### GET /api/v1/workflows/tasks

说明：获取 Agent / ETL / 向量化任务列表。该接口已对齐前端 `api.getTasks()`。

响应：`AgentTask[]`

### GET /api/v1/workflows/publish-plans

说明：获取发布计划列表。该接口已对齐前端 `api.getPublishPlans()`。

响应：`PublishPlan[]`

## 11. Collector

### POST /api/v1/collector/tasks

说明：创建采集任务。

请求体：

```json
{
  "platform": "douyin",
  "accountId": "acct_douyin_001",
  "range": {
    "from": "2026-05-01",
    "to": "2026-05-10"
  }
}
```

响应：`AgentTask`

### GET /api/v1/collector/tasks

说明：获取采集相关任务。

响应：`AgentTask[]`

### GET /api/v1/collector/tasks/{task_id}

说明：获取采集任务详情。

响应：`AgentTask`

### POST /api/v1/collector/upload

说明：采集端上传平台 Raw 数据。服务端会保存 Raw 数据并创建 ETL 任务。

请求体：

```json
{
  "platform": "douyin",
  "sourceUrl": "https://creator.douyin.com/...",
  "payload": {
    "items": []
  },
  "meta": {
    "collectedAt": "2026-05-10T12:00:00+08:00"
  }
}
```

响应：

```json
{
  "rawId": "raw_xxxxxxxx",
  "taskId": "task_etl_xxxxxxxx",
  "status": "accepted"
}
```

### GET /api/v1/collector/logs

说明：获取采集日志。

响应：

```json
[
  {
    "level": "info",
    "message": "Collector API ready",
    "source": "fastapi"
  }
]
```

### POST /api/v1/collector/import

说明：同步触发一轮历史 Raw 数据导入。当前 MVP 支持 `douyin_video_raw`，会从 MongoDB Raw 集合读取文档，标准化后 upsert 到 PostgreSQL `content_items`、`content_lifetime_metrics`、`content_text_assets`、`content_tags`、`content_keywords` 和 `content_traffic_sources`。启用前需手动执行 `backend/docs/schema/content_ingestion.sql` 和 `backend/docs/schema/content_enrichment.sql`；未配置 MongoDB 或 PostgreSQL 时会返回失败统计，不影响服务启动。

请求体：

```json
{
 "workspaceId": "ws_northstar",
  "accountId": "douyin_demo",
  "platform": "douyin",
  "collection": "douyin_video_raw",
  "asrCollection": "douyin_video_asr_results",
  "includeAsr": true,
  "limit": 100
}
```

响应：

```json
{
  "taskId": "task_raw-import_xxxxxxxx",
  "status": "succeeded",
  "processedCount": 100,
  "upsertedCount": 100,
  "failedCount": 0,
  "textAssetCount": 300,
  "tagCount": 120,
  "keywordCount": 80,
  "trafficSourceCount": 0,
  "asrCount": 100
}
```

## 12. Agent 记忆与选题工作台

架构设计见 [`AI_AGENT_ARCHITECTURE.md`](AI_AGENT_ARCHITECTURE.md)。Agent 层采用 FastAPI + 应用服务 + LangGraph runtime + LangChain chains 的分层设计：FastAPI router 保持薄入口，LangGraph 负责任务编排、checkpoint 和节点调试，LangChain 负责模型调用、Prompt、结构化输出和工具适配。

### 12.1 Provider 配置

服务端支持 DeepSeek Chat Provider 和阿里云 DashScope Embedding Provider。除 `POST /api/v1/ai/topic-ideas` 外，未配置密钥时可使用 mock provider 便于本地开发和测试；选题生成接口要求真实 DeepSeek 和 PostgreSQL 证据。

```env
VO_MATE_LLM_PROVIDER="deepseek"
VO_MATE_DEEPSEEK_API_KEY=
VO_MATE_DEEPSEEK_BASE_URL="https://api.deepseek.com"
VO_MATE_DEEPSEEK_MODEL="deepseek-v4-flash"

VO_MATE_EMBEDDING_PROVIDER="dashscope"
VO_MATE_DASHSCOPE_API_KEY=
VO_MATE_DASHSCOPE_EMBEDDING_MODEL="text-embedding-v3"
VO_MATE_DASHSCOPE_EMBEDDING_DIMENSION=1024
```

### POST /api/v1/agent/topic-workbench/run

说明：运行“选题到质检”Agent 工作流，返回策略、标题/简介/脚本、质检报告、证据链和模型推断。

请求体：

```json
{
  "threadId": "th_ws_member_topic_001",
  "workspaceId": "ws_northstar",
  "memberId": "m_demo",
  "accountId": "douyin_demo",
  "platform": "douyin",
  "taskType": "topic_to_qa",
  "topic": "程序员 35 岁危机",
  "targetDurationSeconds": 45,
  "constraints": {
    "tone": "普通人视角",
    "avoid": ["大厂精英口吻", "过度焦虑"]
  }
}
```

响应核心字段：

```json
{
  "runId": "run_xxxxxxxxxx",
  "threadId": "th_ws_member_topic_001",
  "status": "succeeded",
  "topicScore": 85,
  "scores": {
    "personaFit": 90,
    "searchIntentScore": 84,
    "historicalSimilarityScore": 82,
    "retentionPotential": 76,
    "riskPenalty": 18,
    "topicScore": 85
  },
  "strategy": {},
  "drafts": {},
  "qaReport": {},
  "evidence": [],
  "inferences": []
}
```

### Agent 调试接口

| 接口 | 说明 |
| --- | --- |
| `GET /api/v1/agent/runs/{runId}` | 查看 Agent run 结果 |
| `GET /api/v1/agent/runs/{runId}/steps` | 查看 LangGraph 节点步骤输入输出摘要 |
| `GET /api/v1/agent/runs/{runId}/retrieval-traces` | 查看记忆召回 query、filter、topK 和结果 |
| `GET /api/v1/agent/threads/{threadId}/summary` | 查看 thread 压缩摘要 |
| `POST /api/v1/agent/threads/{threadId}/compress` | 创建或返回 thread 摘要 |

### Memory Record 接口

| 接口 | 说明 |
| --- | --- |
| `GET /api/v1/memory/records` | 查看长期记忆记录 |
| `POST /api/v1/memory/records` | 创建记忆并生成 embedding |
| `PATCH /api/v1/memory/records/{memoryId}` | 更新记忆 |
| `POST /api/v1/memory/records/{memoryId}/activate` | 启用候选记忆 |
| `POST /api/v1/memory/records/{memoryId}/deprecate` | 标记记忆过时 |
| `POST /api/v1/memory/records/{memoryId}/reject` | 驳回记忆 |
| `POST /api/v1/memory/search` | 按语义和 metadata 搜索记忆 |

记忆状态：

```text
candidate | active | deprecated | rejected | archived
```

## 13. 前端当前使用接口清单

`frontend-web/src/api/client.ts` 当前使用：

| 前端方法 | HTTP 接口 |
| --- | --- |
| `getWorkspace()` | `GET /api/v1/workspaces/current` |
| `getDashboard()` | `GET /api/v1/analytics/dashboard` |
| `getContents()` | `GET /api/v1/contents` |
| `getTopicIdeas()` | `GET /api/v1/ai/topic-ideas` |
| `getEvidence()` | `GET /api/v1/ai/evidence` |
| `getTasks()` | `GET /api/v1/workflows/tasks` |
| `getMemories()` | `GET /api/v1/memory/patterns` |
| `getPublishPlans()` | `GET /api/v1/workflows/publish-plans` |
| `createAiTask(workflow, payload)` | `POST /api/v1/ai/{workflow}` |

## 14. 后续待补齐接口

以下接口在 SRD 中已有需求，但当前 MVP 尚未实现或尚未拆到独立模块：

| SRD 接口 | 建议实现路径 |
| --- | --- |
| `GET /me` | 可保留 `GET /api/v1/auth/me`，或增加兼容别名 |
| `GET /workspaces` | `GET /api/v1/workspaces` |
| `POST /workspaces` | `POST /api/v1/workspaces` |
| `GET /platform-accounts` | `GET /api/v1/platform-accounts` |
| `POST /platform-accounts` | `POST /api/v1/platform-accounts` |
| `GET /accounts/{id}/fans-summary` | `GET /api/v1/platform-accounts/{id}/fans-summary` |
| `GET /dashboard/topics` | `GET /api/v1/analytics/dashboard/topics` |
| `POST /ai/topic-score` | `POST /api/v1/ai/topic-score` |
| `POST /ai/title` | 已可通过 `POST /api/v1/ai/title` 使用通用工作流 |
| `POST /ai/seo` | 已可通过 `POST /api/v1/ai/seo` 使用通用工作流 |
