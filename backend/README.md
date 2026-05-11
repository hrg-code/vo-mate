# AI 自媒体工作台 Python 服务端

这是根据 `docs/` 中的架构和 SRD 生成的 FastAPI MVP 服务端。当前版本用内存仓库模拟标准数据层，接口路径与前端 `frontend-web/src/api/client.ts` 对齐，后续可以逐步替换为 PostgreSQL、MongoDB、Redis 和 Milvus。

## 启动

```bash
cd backend
python3 -m uvicorn app.main:app --reload --port 8000
```

## 环境变量

服务会读取 `backend/.env`，示例见 `.env.example`。默认 `.env` 中数据库地址为空，服务会跳过外部依赖连接；填入地址后重启即可启用。

```env
VO_MATE_POSTGRES_HOST="localhost"
VO_MATE_POSTGRES_PORT=5432
VO_MATE_POSTGRES_USER="vo_mate"
VO_MATE_POSTGRES_PASSWORD="vo_mate"
VO_MATE_POSTGRES_DATABASE="vo_mate"

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

VO_MATE_LLM_PROVIDER="deepseek"
VO_MATE_DEEPSEEK_API_KEY=
VO_MATE_DEEPSEEK_BASE_URL="https://api.deepseek.com"
VO_MATE_DEEPSEEK_MODEL="deepseek-v4-flash"

VO_MATE_EMBEDDING_PROVIDER="dashscope"
VO_MATE_DASHSCOPE_API_KEY=
VO_MATE_DASHSCOPE_EMBEDDING_MODEL="text-embedding-v3"
VO_MATE_DASHSCOPE_EMBEDDING_DIMENSION=1024

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

依赖连接状态：

```bash
curl http://localhost:8000/api/v1/system/dependencies
```

## 后端管理

服务已接入 SQLAdmin，启动后访问：

```text
http://localhost:8000/admin
```

当前后台使用 PostgreSQL 配置连接数据库。默认 `VO_MATE_SQLADMIN_AUTO_CREATE_TABLES=false`，不会自动建表；如果需要开发期自动创建 SQLAlchemy 模型对应的基础表，可以临时改成 `true` 后重启。

AI 选题生成的持久化表默认也不会自动创建。需要启用 `POST /api/v1/ai/topic-ideas` 的 PostgreSQL 保存和审计时，先手工执行：

```bash
psql -h "$VO_MATE_POSTGRES_HOST" -p "$VO_MATE_POSTGRES_PORT" -U "$VO_MATE_POSTGRES_USER" -d "$VO_MATE_POSTGRES_DATABASE" -f docs/schema/topic_ideas.sql
```

如果 PostgreSQL 未配置或表尚未创建，接口会降级到内存仓库，仍可用于本地联调。

验证 PostgreSQL 证据模式：

```bash
curl -N http://localhost:8000/api/v1/ai/topic-ideas \
  -H 'Content-Type: application/json' \
  -d '{"workspaceId":"ws_northstar","accountIds":["douyin_demo"],"direction":"程序员职业成长","platforms":["douyin"],"count":10}'

curl http://localhost:8000/api/v1/ai/generations/gen_xxx
```

如果 `inputPayload.dataSourceMode` 为 `postgres`，说明本次生成已读取 PostgreSQL 标准层；如果是 `memory_fallback`，说明服务降级到了内存数据。

启用 Milvus 向量记忆召回：

1. 配置 `VO_MATE_MILVUS_HOST`、`VO_MATE_MILVUS_PORT`，并配置 `VO_MATE_EMBEDDING_PROVIDER` / `VO_MATE_DASHSCOPE_API_KEY`。
2. 通过记忆写入入口创建或索引 `active` 状态的长期记忆。
3. 再调用 `POST /api/v1/ai/topic-ideas`。服务会按需创建 Milvus collection `vo_mate_agent_memories`，优先向量召回记忆 ID，并回查 PostgreSQL 或内存记忆仓库补全证据字段。

如果 `inputPayload.dataSourceMode` 为 `milvus`，说明本次生成已使用向量记忆召回；如果 Milvus 或 embedding 不可用，接口会自动降级，不影响前端 SSE 协议。

SQLAdmin 默认启用登录认证。配置 `VO_MATE_SQLADMIN_USERNAME`、`VO_MATE_SQLADMIN_PASSWORD` 或 `VO_MATE_SQLADMIN_PASSWORD_SHA256`、`VO_MATE_SQLADMIN_SESSION_SECRET` 后访问 `/admin` 登录。`VO_MATE_SQLADMIN_ROLE` 支持：

- `owner`：查看、新增、编辑、删除、导出。
- `admin`：查看、新增、编辑、导出，不可删除。
- `viewer`：只读和导出。

前端联调时设置：

```bash
VITE_USE_MOCKS=false
VITE_API_BASE_URL=http://localhost:8000/api/v1
```

## 已实现接口

完整接口说明见 [docs/API.md](docs/API.md)。

- `GET /health`
- `POST /api/v1/auth/login`
- `POST /api/v1/auth/logout`
- `GET /api/v1/auth/me`
- `GET /api/v1/workspaces/current`
- `GET /api/v1/analytics/dashboard`
- `GET /api/v1/analytics/dashboard/overview`
- `GET /api/v1/contents`
- `GET /api/v1/contents/{content_id}`
- `GET /api/v1/contents/{content_id}/metrics`
- `GET /api/v1/contents/{content_id}/analysis`
- `GET /api/v1/contents/{content_id}/asr`
- `GET /api/v1/ai/topic-ideas`
- `POST /api/v1/ai/topic-ideas`
- `GET /api/v1/ai/evidence`
- `POST /api/v1/ai/{workflow}`
- `POST /api/v1/agent/topic-workbench/run`
- `GET /api/v1/agent/runs/{run_id}`
- `GET /api/v1/agent/runs/{run_id}/steps`
- `GET /api/v1/agent/runs/{run_id}/retrieval-traces`
- `GET /api/v1/agent/threads/{thread_id}/summary`
- `GET /api/v1/memory/patterns`
- `POST /api/v1/memory/patterns`
- `PATCH /api/v1/memory/patterns/{pattern_id}`
- `DELETE /api/v1/memory/patterns/{pattern_id}`
- `GET /api/v1/memory/records`
- `POST /api/v1/memory/records`
- `PATCH /api/v1/memory/records/{memory_id}`
- `POST /api/v1/memory/records/{memory_id}/activate`
- `POST /api/v1/memory/records/{memory_id}/deprecate`
- `POST /api/v1/memory/records/{memory_id}/reject`
- `POST /api/v1/memory/search`
- `POST /api/v1/memory/index-content`
- `GET /api/v1/workflows/tasks`
- `GET /api/v1/workflows/publish-plans`
- `GET /api/v1/system/dependencies`
- `POST /api/v1/collector/tasks`
- `GET /api/v1/collector/tasks`
- `GET /api/v1/collector/tasks/{task_id}`
- `POST /api/v1/collector/upload`
- `GET /api/v1/collector/logs`
- `POST /api/v1/collector/import`

## 测试

```bash
cd backend
python3 -m pytest
```
