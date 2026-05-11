# VO Mate Frontend Web

React Web 工作台实现，按 `docs/self_media_ai_workbench_architecture.md` 中的表现层要求组织。

## 技术栈

- React + TypeScript
- Vite production build
- Ant Design 组件体系与主题 token
- `lucide-react` 图标
- API 边界对齐 `/api/v1/*`
- 默认启用 mock adapter，便于在 FastAPI 未接入前独立预览

## 本地运行

```bash
npm install
npm run dev
```

默认访问：

```text
http://localhost:5173/
```

## 构建

```bash
npm run build
```

## 前端规范文档

根目录 `docs/` 已同步到 `frontend-web/docs/`，前端实现优先参考：

- `docs/self_media_ai_workbench_page_structure.md`
- `docs/self_media_ai_workbench_component_spec.md`
- `docs/self_media_ai_workbench_ui_ux_standards.md`
- `docs/self_media_ai_workbench_architecture.md`

UI 基础控件默认使用 Ant Design；项目主题集中维护在 `src/theme.ts`。

## API 接入

默认 `VITE_USE_MOCKS` 不设或不为 `false` 时使用 `src/api/mockData.ts`。
接入 FastAPI 后可配置：

```bash
VITE_USE_MOCKS=false
VITE_API_BASE_URL=http://localhost:8000/api/v1
```

主要 API 分组与架构文档保持一致：

- `/workspaces/current`
- `/analytics/dashboard`
- `/contents`
- `/ai/topic-ideas`
- `/ai/evidence`
- `/workflows/tasks`
- `/memory/patterns`
- `/workflows/publish-plans`
