# Agent 记忆系统后端 MVP 实施计划

## Summary

目标先落地“选题到质检”后端闭环：输入一个选题，系统加载账号上下文，召回记忆，生成选题预测、标题/简介/脚本建议，返回质检报告、证据链和可调试运行记录。

默认范围：

- 后端优先，不做完整前端改造，只保留可联调 API。
- LLM/Embedding 采用抽象 Provider，第一版用 mock provider 跑通流程。
- 支持无 PostgreSQL/Milvus 配置时继续使用内存 mock，避免破坏当前 MVP。
- 有 PostgreSQL/Milvus 配置时走真实持久化和向量召回。
- LangGraph 用于编排、thread state、压缩节点和运行恢复。

## Key Changes

### 1. 数据与记忆模型

新增后端持久化模型：

- `agent_memory_records`
  保存长期记忆主表，字段包括 `workspace_id`、`account_id`、`platform`、`memory_type`、`title`、`content`、`summary`、`metadata`、`source_type`、`source_ids`、`confidence`、`evidence_count`、`status`、`last_validated_at`。
- `agent_thread_summaries`
  保存 LangGraph thread 压缩摘要，字段包括 `thread_id`、`workspace_id`、`member_id`、`account_id`、`summary`、`decisions`、`rejected_ideas`、`pending_tasks`。
- `agent_runs`
  保存每次 Agent 执行，字段包括 `run_id`、`thread_id`、`workflow`、`status`、`input`、`output`、`error`、`graph_version`。
- `agent_run_steps`
  保存节点级调试记录，字段包括 `run_id`、`node_name`、`input_snapshot`、`output_snapshot`、`started_at`、`finished_at`。
- `agent_retrieval_traces`
  保存召回调试记录，字段包括 `run_id`、`query`、`memory_types`、`filters`、`top_k`、`results`。

Milvus collection：

- collection 名称：`agent_memory_vectors`
- metadata 固定包含 `memory_id`、`workspace_id`、`account_id`、`platform`、`memory_type`、`status`、`confidence`、`topic_cluster`。
- Milvus 只做召回索引，完整内容始终回查 PostgreSQL。

第一版支持 memory types：

```text
content_case
hook_pattern
persona_profile
search_intent
success_pattern
failure_pattern
qa_rule
```

### 2. 服务层与 Provider 抽象

新增服务模块：

- `MemoryRecordService`
  负责长期记忆 CRUD、状态流转、置信度、候选记忆审核。
- `MemoryVectorService`
  负责 embedding、Milvus upsert/search/delete；Milvus 未配置时返回 mock 检索结果。
- `AgentRunService`
  负责 run、step、retrieval trace 记录。
- `AgentProvider`
  抽象 LLM 和 embedding，第一版实现 `MockAgentProvider`，后续可加 OpenAI、本地模型。
- `TopicWorkbenchGraph`
  LangGraph 主图，编排 parse、load context、retrieve、score、generate、qa、compress、finalize。

Provider 接口固定为：

```text
complete_json(task, system_prompt, user_input, context, schema) -> dict
embed_text(text) -> list[float]
```

第一版 mock provider 必须返回稳定 JSON，便于测试。

### 3. Agent 编排流程

主流程：

```text
parse_request
-> load_account_context
-> retrieve_memories
-> score_topic
-> generate_topic_strategy
-> generate_title_description_script
-> qa_content
-> finalize_response
-> compress_thread_memory
-> schedule_memory_learning
```

节点输出要求：

- `retrieve_memories` 返回 evidence pack，只包含摘要、指标和 `memoryId`，不把大段历史原文塞进 state。
- `score_topic` 返回 `personaFit`、`searchIntentScore`、`historicalSimilarityScore`、`retentionPotential`、`riskPenalty`、`topicScore`。
- `generate_title_description_script` 返回搜索型/争议型/人设型/干货型标题、简介、话题标签、45 秒脚本。
- `qa_content` 返回人设、SEO/GEO、留存、风险、转化五类质检分和修改建议。
- `finalize_response` 的每条关键建议必须绑定 `evidence.memoryId`；无证据的内容标记为 `inference`。

LangGraph state 固定结构：

```text
messages
workspace_id
member_id
account_id
platform
task_type
topic_brief
retrieved_memories
draft_versions
qa_reports
current_summary
decisions
rejected_ideas
pending_tasks
```

压缩规则：

- 最近 6 轮消息保留原文。
- 旧消息压缩进 `current_summary`。
- 用户确认内容写入 `decisions`。
- 用户否定方向写入 `rejected_ideas`。
- 召回证据只保留 `memory_id + summary + score`。

### 4. API 设计

新增 `/api/v1/agent` 路由：

```text
POST /api/v1/agent/topic-workbench/run
GET  /api/v1/agent/runs/{runId}
GET  /api/v1/agent/runs/{runId}/steps
GET  /api/v1/agent/runs/{runId}/retrieval-traces
GET  /api/v1/agent/threads/{threadId}/summary
POST /api/v1/agent/threads/{threadId}/compress
```

`POST /agent/topic-workbench/run` 请求：

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

响应：

```json
{
  "runId": "run_xxx",
  "threadId": "th_ws_member_topic_001",
  "status": "succeeded",
  "topicScore": 82,
  "scores": {
    "personaFit": 90,
    "searchIntentScore": 84,
    "retentionPotential": 76,
    "riskPenalty": 18
  },
  "strategy": {},
  "drafts": {},
  "qaReport": {},
  "evidence": [],
  "inferences": []
}
```

扩展 `/api/v1/memory`：

```text
GET  /memory/records
POST /memory/records
PATCH /memory/records/{memoryId}
POST /memory/records/{memoryId}/activate
POST /memory/records/{memoryId}/deprecate
POST /memory/records/{memoryId}/reject
POST /memory/search
POST /memory/index-content
```

保留现有 `/memory/patterns`，但内部适配到新 `agent_memory_records`，避免前端现有页面断掉。

## Task Breakdown

### Phase 1：基础骨架

- 增加 LangGraph/LangChain Core 依赖和 Provider 抽象。
- 增加 Agent schema：请求、响应、scores、drafts、qa report、evidence、run detail。
- 增加 SQLAlchemy 模型和 SQLAdmin 视图。
- 增加 repository/service 接口，提供 Postgres 实现和 in-memory fallback。
- 新增 `/api/v1/agent` router，并接入主 router。
- 更新 `backend/docs/API.md` 的 Agent 与 Memory API。

验收：

- 不配置数据库/Milvus 时，现有测试继续通过。
- `POST /api/v1/agent/topic-workbench/run` 可返回稳定 mock 结果。
- `GET /api/v1/agent/runs/{runId}` 可查询本次执行结果。

### Phase 2：记忆召回闭环

- 实现 `agent_memory_records` 的 CRUD 和状态流转。
- 实现 Milvus collection 初始化、向量写入、向量检索；未配置 Milvus 时使用 mock 检索。
- 实现 `retrieve_memories` 节点，按任务类型召回 `content_case`、`persona_profile`、`search_intent`、`success_pattern`、`failure_pattern`。
- 实现 evidence pack 生成，所有 evidence 带 `memoryId`、`memoryType`、`summary`、`score`。
- 实现 `/memory/search` 返回真实或 mock 的召回结果。
- 实现 `/memory/index-content` 的任务入口，先生成任务记录，不在请求内做批量入库。

验收：

- 手动创建一条 `persona_profile` 和一条 `content_case` 后，Agent run 能召回并引用。
- Retrieval Trace 能看到 query、filter、topK、召回结果。
- Milvus 未配置时接口仍返回可测试结果。

### Phase 3：LangGraph 主图

- 实现 `TopicWorkbenchState`。
- 实现节点：`parse_request`、`load_account_context`、`retrieve_memories`、`score_topic`、`generate_title_description_script`、`qa_content`、`finalize_response`、`compress_thread_memory`。
- 每个节点写入 `agent_run_steps`。
- `compress_thread_memory` 生成结构化 summary，并保存到 `agent_thread_summaries`。
- `qa_content` 输出五类质检：人设、SEO/GEO、留存、风险、转化。
- 所有生成结果使用 Provider 抽象，第一版仍由 mock provider 生成稳定内容。

验收：

- 同一个 `threadId` 连续运行两次，第二次能加载已有 summary。
- 长输入触发压缩后，summary 中包含 selectedAngle、personaConstraints、rejectedIdeas。
- run detail 可以看到每个节点的输入输出摘要。

### Phase 4：历史数据学习入口

- 先不做全量自动 ETL，只做单条/批量内容入库任务入口。
- 从已有 `ContentItem`、`MemoryPattern` 和抖音字段规范中定义 `ContentInsight` schema。
- 实现 `MemoryLearningGraph` 的最小版本：输入内容摘要，产出 `content_case`、`hook_pattern`、`search_intent` 候选记忆。
- 新候选记忆默认 `status=candidate`，不自动参与高权重召回。
- 后台可通过 Memory API activate/reject/deprecate。

验收：

- 调用 `/memory/index-content` 后创建任务。
- 学习任务可生成 candidate 记忆。
- candidate 记忆被 activate 后参与下一次 Agent 召回。

### Phase 5：调试与测试收口

- 增加 Agent Run Detail 测试。
- 增加 Retrieval Trace 测试。
- 增加 memory lifecycle 测试。
- 增加 thread compression 测试。
- 增加 fallback 测试：PostgreSQL/Milvus/LLM 都未配置时 API 可用。
- 更新 README 和 API 文档中的启动、配置、验证命令。

验收：

- `backend/.venv/bin/python -m pytest` 通过。
- 现有前端 API contract 测试不破坏。
- 新 Agent API 返回 camelCase JSON 字段。
- 无真实密钥写入文档或代码。

## Test Plan

- 单元测试：
  - memory record 创建、更新、状态流转。
  - mock provider 输出稳定 JSON。
  - score_topic 对相同输入返回稳定分数。
  - compress_thread_memory 保留关键决策和 rejected ideas。
- API 测试：
  - `POST /agent/topic-workbench/run`
  - `GET /agent/runs/{runId}`
  - `GET /agent/runs/{runId}/steps`
  - `GET /agent/runs/{runId}/retrieval-traces`
  - `/memory/records` lifecycle。
- 集成测试：
  - 无外部依赖配置时走 fallback。
  - 配置 Milvus 时 search 使用 collection metadata filter。
  - 同 thread 多次运行能重连 summary。
- 回归测试：
  - 现有 `/ai/topic-ideas`、`/memory/patterns`、`/analytics/dashboard` 不破坏。
  - 前端要求的 camelCase 字段继续存在。

## Assumptions

- 第一版不接真实 OpenAI 或本地模型，只实现 Provider 抽象和 mock provider。
- 第一版不做完整前端调试台，只通过 API 暴露 run、step、retrieval trace。
- 第一版不引入 Alembic；沿用当前 SQLAlchemy 模型方式，表创建仍受 `VO_MATE_SQLADMIN_AUTO_CREATE_TABLES` 控制，生产库建表由后续迁移方案处理。
- 第一版不做全量抖音 Mongo ETL，只做记忆学习任务入口和候选记忆生成骨架。
- `user/member` 权限系统暂不纳入本计划，只预留 `workspaceId`、`memberId`、`accountId` 字段。
