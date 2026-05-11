# DeepSeek + 阿里云 Embedding 接入后的 Agent 记忆系统实施计划

## Summary

本计划在现有“后端优先、选题到质检闭环”基础上，明确接入：

- Chat/Reasoning：DeepSeek `deepseek-v4-flash`
- Embedding：阿里云 DashScope `text-embedding-v3`，1024 维
- Agent 编排：LangGraph
- 长期记忆：PostgreSQL + Milvus
- 第一版闭环：输入选题 -> 召回记忆 -> 生成标题/简介/脚本 -> 质检 -> 返回证据链和调试记录

参考官方信息：

- DeepSeek API 兼容 OpenAI 格式，base URL 使用 `https://api.deepseek.com`，当前推荐模型包含 `deepseek-v4-flash`。
- 阿里云 `text-embedding-v3` 支持 1024 维，适合 Milvus dense vector 入库。

## Key Changes

### 1. Provider 配置

新增配置项，全部走 `.env`，不写死密钥：

```env
VO_MATE_LLM_PROVIDER="deepseek"
VO_MATE_DEEPSEEK_API_KEY=
VO_MATE_DEEPSEEK_BASE_URL="https://api.deepseek.com"
VO_MATE_DEEPSEEK_MODEL="deepseek-v4-flash"
VO_MATE_DEEPSEEK_TIMEOUT_SECONDS=60

VO_MATE_EMBEDDING_PROVIDER="dashscope"
VO_MATE_DASHSCOPE_API_KEY=
VO_MATE_DASHSCOPE_BASE_URL="https://dashscope.aliyuncs.com/api/v1"
VO_MATE_DASHSCOPE_EMBEDDING_MODEL="text-embedding-v3"
VO_MATE_DASHSCOPE_EMBEDDING_DIMENSION=1024
```

Provider 抽象：

```text
ChatProvider.generate_json(...)
EmbeddingProvider.embed_documents(...)
EmbeddingProvider.embed_query(...)
```

实现：

- `DeepSeekChatProvider`
  使用 OpenAI-compatible chat completions。
- `DashScopeEmbeddingProvider`
  调用阿里云 text embedding，同一模型区分 query/document 输入。
- `MockChatProvider` / `MockEmbeddingProvider`
  无 key 或测试环境时使用，保证现有 MVP 不被外部依赖阻塞。

### 2. Milvus 设计

Milvus collection：

```text
agent_memory_vectors
```

固定向量维度：

```text
1024
```

字段：

```text
id
memory_id
workspace_id
account_id
platform
memory_type
status
confidence
topic_cluster
embedding
created_at
```

索引：

```text
metric_type = COSINE
index_type = HNSW 或 AUTOINDEX
```

第一版只存 dense vector，不做 sparse/hybrid search。

Embedding 输入策略：

- 文档入库用 `embed_documents`
- 用户查询用 `embed_query`
- 对 content_case、search_intent、persona_profile、success_pattern、failure_pattern 分别生成可检索文本
- Milvus 只返回 `memory_id` 和 score，完整内容回查 PostgreSQL

### 3. Agent 主流程

新增 `/api/v1/agent/topic-workbench/run`。

请求：

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

LangGraph 节点：

```text
parse_request
load_account_context
retrieve_memories
score_topic
generate_strategy
generate_title_description_script
qa_content
finalize_response
compress_thread_memory
```

DeepSeek 只参与：

- 结构化理解
- 标题/简介/脚本生成
- 质检报告
- 摘要压缩

阿里云 embedding 只参与：

- 记忆入库
- 查询向量化
- Milvus 召回

### 4. 数据模型与调试

新增表：

```text
agent_memory_records
agent_thread_summaries
agent_runs
agent_run_steps
agent_retrieval_traces
```

记忆状态：

```text
candidate
active
deprecated
rejected
archived
```

调试 API：

```text
GET /api/v1/agent/runs/{runId}
GET /api/v1/agent/runs/{runId}/steps
GET /api/v1/agent/runs/{runId}/retrieval-traces
GET /api/v1/agent/threads/{threadId}/summary
```

每次 Agent 输出必须包含：

```text
evidence[]
inferences[]
```

规则：

- 有 `memoryId` 支撑的结论放入 `evidence`
- 无直接证据、由模型推理得出的内容放入 `inferences`
- Retrieval trace 必须记录 query、memoryTypes、filters、topK、results

## Task Breakdown

### Phase 1：Provider 与配置

- 扩展 `Settings`，加入 DeepSeek 和 DashScope 配置。
- 新增 chat provider / embedding provider 抽象。
- 实现 `DeepSeekChatProvider`。
- 实现 `DashScopeEmbeddingProvider`，固定 1024 维。
- 实现 mock provider fallback。
- 增加 provider 单元测试，测试无 key 时 fallback，有配置时构造正确请求参数。

验收：

- 无 DeepSeek key 时测试仍可跑。
- DeepSeek provider 使用 `deepseek-v4-flash`。
- DashScope embedding 输出维度校验为 1024。
- 不在日志、测试快照、文档中输出真实 key。

### Phase 2：记忆存储与 Milvus

- 新增 `agent_memory_records` SQLAlchemy 模型。
- 新增 `MemoryRecordService`。
- 新增 `MemoryVectorService`。
- 初始化 Milvus collection `agent_memory_vectors`。
- 实现 memory upsert：PostgreSQL 写主记录，DashScope 生成 embedding，Milvus 写向量。
- 实现 memory search：DashScope 生成 query embedding，Milvus 搜索，PostgreSQL 回填详情。
- Milvus 未配置时返回 mock search 结果。

验收：

- 创建 `persona_profile` 后可搜索召回。
- 创建 `content_case` 后可按 `workspaceId/accountId/memoryType/status` 过滤。
- Milvus collection 维度固定 1024。
- `/memory/search` 返回 camelCase JSON。

### Phase 3：Agent Run 与 LangGraph

- 新增 Agent schemas。
- 新增 `TopicWorkbenchState`。
- 新增 LangGraph 主图。
- 节点接入 DeepSeek provider。
- 召回节点接入 MemoryVectorService。
- 每个节点写 `agent_run_steps`。
- 每次召回写 `agent_retrieval_traces`。
- 压缩节点写 `agent_thread_summaries`。

验收：

- `POST /agent/topic-workbench/run` 返回 strategy、drafts、qaReport、evidence。
- 同一个 `threadId` 第二次运行能加载 summary。
- run detail 可看到每个节点输入输出摘要。
- 质检报告包含人设、SEO/GEO、留存、风险、转化五类分数。

### Phase 4：内容学习入口

- 新增 `/memory/index-content` 后台任务入口。
- 定义 `ContentInsight` schema。
- 单条内容生成候选记忆：
  - `content_case`
  - `hook_pattern`
  - `search_intent`
- 候选记忆默认 `candidate`。
- 新增 activate/deprecate/reject API。
- active 记忆参与 Agent 召回，candidate 默认只在调试或审核接口展示。

验收：

- index-content 能创建 candidate 记忆。
- activate 后下一次 Agent run 可召回该记忆。
- rejected/deprecated 记忆默认不参与召回。

### Phase 5：测试与文档

- 更新 `backend/docs/API.md`。
- 更新 `backend/.env.example`。
- 增加 API 测试：
  - Agent run
  - Run detail
  - Retrieval traces
  - Memory lifecycle
  - Provider fallback
- 增加集成测试：
  - 无外部服务配置时 mock provider 工作
  - DashScope embedding 维度配置校验
  - DeepSeek 请求参数构造校验

验证命令：

```bash
cd backend
.venv/bin/python -m pytest
```

## Assumptions

- 第一版默认 DeepSeek 模型为 `deepseek-v4-flash`。
- 第一版 embedding 使用阿里云 DashScope `text-embedding-v3`，固定 1024 维。
- 第一版只做 dense vector search，不做 sparse 或 hybrid retrieval。
- 第一版不接完整前端调试台，只提供后端 API。
- 第一版不做全量 Mongo 历史 ETL，只做单条/批量记忆学习入口。
- 第一版不引入 Alembic，沿用当前 SQLAlchemy/SQLAdmin 方式；生产迁移方案后续单独规划。
