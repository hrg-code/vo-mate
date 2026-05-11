# AGENTS.md

本文件约束仓库根目录及未另行声明的子目录。面向 Codex、Copilot、Claude Code 等编码代理；人类开发者也可作为协作规范使用。

若子目录存在自己的 `AGENTS.md`，以更靠近目标文件的那份为准。当前 `frontend-web/AGENTS.md` 已单独约束前端实现。

## 项目定位

- 本仓库是 VO Mate / AI 自媒体工作台原型与服务端实现。
- 产品目标是把创作者历史数据、多平台采集、AI 生成、向量记忆、内容工作流和复盘学习串成闭环。
- 当前包含：
  - `docs/`：产品需求、架构、字段和交互规范。
  - `frontend-web/`：React Web 工作台。
  - `backend/`：FastAPI Python 服务端、SQLAdmin 后台和外部依赖连接。
  - `ui:ux-web/`：早期静态原型或管理端原型。

## 工作原则

- 先读 `docs/` 和目标目录现有代码，再动手。
- 保持模块化单体思路，按业务域拆分，不要提前引入复杂微服务结构。
- 新增能力优先贴合现有接口和数据模型；避免为了局部需求重写项目结构。
- 不要提交或修改无关构建产物、缓存、虚拟环境内容。
- 不要把密钥、账号、密码写进文档示例或代码常量；配置值只放 `.env`，示例用占位。
- 修改 `.env` 时注意它可能包含真实密钥，只改必要字段，不在回复中复述敏感值。

## 目录职责

```text
docs/                 产品、架构、页面、组件、字段和 API 需求文档
frontend-web/          React + TypeScript Web 工作台
backend/               FastAPI 服务端、Pydantic schema、SQLAdmin、数据库连接
backend-admin-ui/      静态管理端原型
ui:ux-web/             静态 UI/UX 原型
```

后端重点目录：

```text
backend/app/
  main.py              FastAPI 应用入口
  admin.py             SQLAdmin 注册入口
  api/v1/              REST API routers
  core/                配置和外部连接管理
  db/                  SQLAlchemy engine 和 ORM models
  repositories/        MVP 内存仓库，后续替换真实存储
  schemas/             Pydantic API schema
  services/            应用服务层预留目录
backend/docs/API.md    后端接口文档
backend/.env.example   环境变量示例
```

## 后端约定

- 后端使用 FastAPI + Pydantic v2。
- API 前缀默认是 `/api/v1`。
- 外部依赖配置从 `backend/.env` 读取，字段前缀为 `VO_MATE_`。
- PostgreSQL、MongoDB、Redis、Milvus 配置必须拆成 host、port、user、password、database 等独立字段，不要使用揉在一起的 DSN/URI/URL。
- Redis 当前可选；未配置时服务应跳过连接，不应启动失败。
- SQLAdmin 后台挂载在 `/admin`，使用 PostgreSQL 配置连接。
- `VO_MATE_SQLADMIN_AUTO_CREATE_TABLES` 默认保持 `false`，不要在未确认时自动建表或迁移 schema。
- Milvus 使用 `pymilvus.connections.connect(alias="default", host=..., port=...)` 风格连接。
- 当前业务接口仍主要返回 `repositories/memory_store.py` 的 MVP 数据；接真实库时要逐步替换 repository/service 层，不要把数据库查询散落到 router。

## 后端命令

在 `backend` 目录执行：

```bash
source .venv/bin/activate
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
python -m pytest
```

服务入口：

```text
http://127.0.0.1:8000
http://127.0.0.1:8000/docs
http://127.0.0.1:8000/admin
http://127.0.0.1:8000/api/v1/system/dependencies
```

依赖安装：

```bash
cd backend
.venv/bin/python -m pip install -r requirements.txt
```

## 后端配置

`.env.example` 只放占位或本地开发默认值。真实 `.env` 可能包含敏感配置，不要复制到文档或最终回复。

推荐配置形态：

```env
VO_MATE_POSTGRES_HOST="localhost"
VO_MATE_POSTGRES_PORT=5432
VO_MATE_POSTGRES_USER="vo_mate"
VO_MATE_POSTGRES_PASSWORD="change-me"
VO_MATE_POSTGRES_DATABASE="vo_mate"

VO_MATE_MONGO_HOST="localhost"
VO_MATE_MONGO_PORT=27017
VO_MATE_MONGO_USER=
VO_MATE_MONGO_PASSWORD=
VO_MATE_MONGO_DATABASE="vo_mate"
VO_MATE_MONGO_AUTH_SOURCE="admin"

VO_MATE_REDIS_HOST=
VO_MATE_REDIS_PORT=6379
VO_MATE_REDIS_DATABASE=0
VO_MATE_REDIS_USER=
VO_MATE_REDIS_PASSWORD=

VO_MATE_MILVUS_HOST="localhost"
VO_MATE_MILVUS_PORT=19530
VO_MATE_MILVUS_SECURE=false
VO_MATE_MILVUS_TOKEN=
VO_MATE_MILVUS_DATABASE=
```

## 数据与模型

- PostgreSQL 是标准业务数据层，核心表参考 `docs/self_media_ai_workbench_srd.md` 和 `docs/self_media_ai_workbench_architecture.md`。
- MongoDB 是 Raw 数据层，保留平台原始 JSON。
- Milvus 是向量记忆层，用于相似检索、模式记忆和 AI 生成上下文。
- Redis 是任务队列/缓存层，当前可暂不启用。
- 新增 SQLAlchemy ORM 模型时，同步考虑：
  - 是否需要 SQLAdmin 管理视图。
  - 是否需要 API schema。
  - 是否需要迁移脚本或手工建表说明。

## API 规范

- 接口文档维护在 `backend/docs/API.md`。
- 新增后端接口时同步更新：
  - `backend/docs/API.md`
  - `backend/README.md` 的接口清单，如属于公共入口。
  - `frontend-web/src/api/client.ts` 与 mock 数据，如前端会使用。
- 前端已使用的真实接口需要保持 camelCase JSON 字段，例如 `publishedAt`、`durationSeconds`、`currentStep`。
- 外部平台 ID、视频 ID、任务 ID 等均按字符串处理，避免大整数精度问题。

## 前端约定

- `frontend-web/` 内的工作以 `frontend-web/AGENTS.md` 为准。
- 前端默认 mock；接后端时使用：

```bash
VITE_USE_MOCKS=false
VITE_API_BASE_URL=http://localhost:8000/api/v1
```

## 文档约定

- 产品、架构、字段解释优先写入 `docs/`。
- 后端接口细节写入 `backend/docs/API.md`。
- README 保持为快速启动和入口说明，不要堆过长设计细节。
- 文档中的密钥、密码和 token 必须使用占位值。

## 文件卫生

- 不要编辑或提交：
  - `backend/.venv/`
  - `frontend-web/node_modules/`
  - `frontend-web/dist/`
  - `__pycache__/`
  - `.pytest_cache/`
  - `.DS_Store`
- 运行测试或编译生成缓存后，尽量清理自己产生的 `__pycache__`。
- 不要用破坏性命令清空用户文件；若必须删除真实数据或重置数据库，先明确征得用户同意。

## 验证清单

后端改动常规验证：

```bash
cd backend
.venv/bin/python -m pytest
curl http://127.0.0.1:8000/api/v1/system/dependencies
```

涉及 SQLAdmin 的改动：

```bash
curl -L -o /tmp/sqladmin_admin.html -w '%{http_code}' http://127.0.0.1:8000/admin
```

涉及前端的改动参考 `frontend-web/AGENTS.md`，通常需要：

```bash
cd frontend-web
npm run build
npm run lint
```

## 修改优先级

当需求与现有实现冲突时，按以下顺序取舍：

1. 用户当前明确需求。
2. `docs/` 中的产品、架构、接口和字段约定。
3. 本文件和更近目录的 `AGENTS.md`。
4. 现有代码风格和目录组织。

如需偏离上述规范，请在回复中简短说明原因。
