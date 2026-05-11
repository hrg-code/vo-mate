# AGENTS.md

本文件约束 `backend/` 目录内的 Python 服务端实现。更上层的仓库规范见 `../AGENTS.md`；若两者冲突，以本文件对 `backend/` 的具体约定为准。

## 后端定位

- 本目录是 VO Mate / AI 自媒体工作台的 FastAPI 服务端。
- 当前阶段是 MVP 模块化单体，负责：
  - `/api/v1/*` REST API。
  - PostgreSQL、MongoDB、Redis、Milvus 连接管理。
  - SQLAdmin 后台管理。
  - 与 `frontend-web/src/api/client.ts` 对齐的数据契约。
- 当前业务接口大多仍从 `app/repositories/memory_store.py` 返回样例数据；接真实库时应逐步新增真实 repository/service，并保持 API 响应契约稳定。
- 不要直接在 router 中绕过现有分层读取数据库。
- 不要一次性删除 `memory_store.py`，除非用户明确要求并已有替代实现。

## 命名规范
- Python 文件、模块、函数、变量统一使用 snake_case。
- Python 类名统一使用 PascalCase。
- 常量统一使用 UPPER_SNAKE_CASE。
- API 路径统一使用小写名词路径，不使用 camelCase 路径。
- Python 内部字段优先使用 snake_case。
- 面向前端的 JSON 响应字段按既有契约保持 camelCase。
- 数据库表名统一使用既有表名；新增表默认使用小写复数名词。
- 外部平台 ID、视频 ID、任务 ID、trace ID 等跨系统标识统一使用字符串。
- 不要混用 id、xxx_id、xxxId：
  - Python 内部使用 xxx_id。
  - API 响应使用 xxxId。
  - 数据库字段优先使用 xxx_id，除非既有表结构不同。
- 不要随意缩写，除非是 API、URL、ID、JSON、SQL 等通用缩写。
- 新增文件名应表达领域含义，例如：
  - content_topic_service.py
  - workspace_repository.py
  - publish_plan.py
  - collector_task.py
- `app/services/` 下所有业务服务文件必须使用 `xx_xx_service.py` 形式，文件名需要包含清晰领域名和 `_service` 后缀，例如 `topic_idea_service.py`、`memory_record_service.py`；不要使用仅表示业务对象的文件名。包标记文件 `__init__.py` 除外。
- `app/services/` 下的业务逻辑采用面向对象方式组织：服务行为放在 `PascalCase` service 类中，并按需在模块底部导出单例实例供 router 调用；避免新增只有一组裸函数的 service 模块。

## 技术栈

- Python 3.10
- FastAPI
- Pydantic v2
- SQLAlchemy 2
- SQLAdmin
- asyncpg / psycopg
- motor
- redis-py
- pymilvus
- pytest

不要擅自引入与当前技术栈冲突的大型框架，例如 Django、Flask、Celery、React 后台等，除非用户明确要求。

## 常用命令

在 `backend/` 目录执行：

```bash
source .venv/bin/activate
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
python -m pytest
```

依赖安装：

```bash
.venv/bin/python -m pip install -r requirements.txt
```

常用入口：

```text
http://127.0.0.1:8000
http://127.0.0.1:8000/docs
http://127.0.0.1:8000/admin
http://127.0.0.1:8000/api/v1/system/dependencies
```

## 目录职责

```text
app/
  main.py              FastAPI app factory 和应用挂载入口
  admin.py             SQLAdmin 后台注册
  api/v1/              API router，薄路由层
  core/config.py       .env 配置读取
  core/connections.py  PostgreSQL / MongoDB / Redis / Milvus 连接生命周期
  db/models.py         SQLAlchemy ORM 模型
  db/session.py        SQLAdmin/SQLAlchemy 同步 engine
  repositories/        数据访问层，MVP 阶段含内存仓库
  schemas/             Pydantic 请求/响应 schema
  services/            应用服务层，复杂业务逻辑放这里
docs/API.md            后端接口文档
tests/                 pytest 测试
requirements.txt       Python 依赖
.env.example           环境变量示例
```

约定：

- Router 只做参数接收、响应模型声明、HTTP 错误转换和调用 service/repository。
- 复杂业务逻辑不要写在 router。
- 数据库查询不要散落在 router；新查询优先放到 repository 或 service。
- Pydantic schema 放 `app/schemas/`，不要在多个 router 中重复匿名复杂类型。
- SQLAlchemy ORM 模型放 `app/db/models.py`；如果文件变大，再按领域拆分。
- 新增 router 后必须在 app/api/v1/router.py 注册。
- 新增领域模块时，优先按现有目录风格扩展，不要重构无关目录。

## 环境变量

服务读取 `backend/.env`，配置类在 `app/core/config.py`。

重要规则：

- PostgreSQL、MongoDB、Redis、Milvus 配置必须拆成独立字段。
- 不要使用一条揉在一起的 DSN、URI、URL。
- `.env` 可能包含真实密钥和密码，修改时只改必要字段，不要复制到日志、文档或回复。
- `.env.example` 使用本地默认值或占位值，不放真实账号密码。

推荐格式：

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

## 外部依赖连接

- 连接生命周期集中在 `app/core/connections.py`。
- 未配置的依赖应跳过连接，不应导致服务启动失败。
- `/api/v1/system/dependencies` 用于查看依赖状态。
- Redis 当前可选；用户要求暂不使用时保持空配置。
- Milvus 使用 `pymilvus.connections.connect(alias="default", host=..., port=...)`。
- PostgreSQL API 异步访问优先使用 `asyncpg`；SQLAdmin 使用 SQLAlchemy 同步 engine。
- MongoDB Raw 数据访问优先使用 `motor`。

## SQLAdmin

- SQLAdmin 在 `app/admin.py` 注册，默认路径 `/admin`。
- SQLAdmin 使用 `app/db/session.py` 中的 PostgreSQL SQLAlchemy engine。
- `VO_MATE_SQLADMIN_ENABLED=true` 时启用。
- `VO_MATE_SQLADMIN_AUTH_ENABLED=true` 时必须配置后台用户名、密码或密码 SHA256、session secret。
- SQLAdmin 角色支持 `owner`、`admin`、`viewer`：`owner` 可删除，`admin` 可新增/编辑不可删除，`viewer` 只读。
- `VO_MATE_SQLADMIN_AUTO_CREATE_TABLES` 默认必须保持 `false`。
- 不要在未得到用户明确同意时自动建表、删表、重建表或迁移 schema。
- 新增 ORM 模型时，如需要后台管理，同步新增 `ModelView` 并注册到 `setup_sqladmin()`。

当前已注册管理视图：

```text
workspaces
users
workspace_members
platform_accounts
content_items
topic_ideas
script_drafts
publish_plans
memory_patterns
collector_tasks
```

## API 规范

- API 路径统一挂在 `/api/v1`。
- 路由文件按领域放在 `app/api/v1/`。
- 新增 router 后必须在 `app/api/v1/router.py` 注册。
- 响应字段需要兼容前端 TypeScript 类型，前端已使用字段保持 camelCase：
  - `workspaceId`
  - `publishedAt`
  - `durationSeconds`
  - `completionRate`
  - `followersGained`
  - `currentStep`
  - `traceId`
- 外部平台 ID、视频 ID、任务 ID 一律按字符串处理。
- 新增接口同步更新 `docs/API.md`。
- 若前端会使用该接口，同步更新 `frontend-web/src/api/client.ts` 和 mock 数据。

## 分层调用规则

后端采用轻量分层架构：

```text
router -> service -> repository -> database / external dependency

- router 可以调用 service，必要时可调用简单 repository，但优先通过 service。
- service 可以调用 repository、连接管理和其他 service。
- repository 只负责数据访问、样例数据读取、数据转换，不包含复杂业务决策。
- schemas 不应依赖 routers、services 或 repositories。
- models 不应依赖 routers、services 或 repositories。
- 禁止反向依赖，例如 repository 调用 router、model 调用 service。
- 复杂业务流程必须放在 services/，不要散落在多个 router。
- 不要引入复杂的 DDD、Clean Architecture、Repository 抽象基类或依赖注入容器，除非用户明确要求。
- 当前项目优先保持可读、可运行、可渐进替换。
```

## 数据层约定

- PostgreSQL：标准业务数据、权限、工作流和 SQLAdmin 管理对象。
- MongoDB：平台 Raw JSON、采集原始数据、字段追溯。
- Milvus：向量记忆、相似检索、模式记忆。
- Redis：队列、缓存、任务状态，当前可以不启用。

接真实数据库时：

- 不要直接删除 `memory_store.py`；先平滑增加新的 repository，并让 router/service 可切换。
- 不要在接口层拼 SQL。
- 不要在没有迁移方案时修改 ORM 表结构并要求自动建表。
- 字段定义优先参考 `../docs/self_media_ai_workbench_srd.md` 和 `../docs/self_media_ai_workbench_architecture.md`。

## 测试

常规后端改动至少执行：

```bash
.venv/bin/python -m pytest
```

涉及应用启动、配置或连接管理时，再检查：

```bash
curl http://127.0.0.1:8000/api/v1/system/dependencies
```

涉及 SQLAdmin 时检查：

```bash
curl -L -o /tmp/sqladmin_admin.html -w '%{http_code}' http://127.0.0.1:8000/admin
```

测试约定：

- API contract 测试放 `tests/`。
- 新增前端依赖接口时，测试应覆盖关键字段名是否保持 camelCase。
- 外部服务不可用时，测试不应硬依赖真实数据库，除非用户明确要求做集成测试。

## 文档

- 后端启动、配置和接口入口写 `README.md`。
- 完整接口说明写 `docs/API.md`。
- 重要配置新增后，同步更新 `.env.example`。
- 文档示例不得包含真实密钥、真实 token 或真实密码。

## 文件卫生

不要编辑、提交或批量扫描无关内容：

```text
.venv/
.pytest_cache/
__pycache__/
.DS_Store
```

运行测试、编译或启动后，尽量清理自己产生的 `__pycache__`。

## 变更优先级

当需求与现有实现冲突时，按以下顺序取舍：

1. 用户当前明确需求。
2. `../docs/` 中的产品、架构、接口和字段约定。
3. 本文件。
4. `../AGENTS.md`。
5. 现有代码风格。

如需偏离上述规范，请在回复中简短说明原因。
