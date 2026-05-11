# Frontend Docs Sync

本目录同步自仓库根目录 `docs/`，用于让 `frontend-web` 内的编码代理和前端开发流程就近读取产品、架构、页面、交互与组件规范。

## 同步来源

- `../../docs/self_media_ai_workbench_architecture.md`
- `../../docs/self_media_ai_workbench_page_structure.md`
- `../../docs/self_media_ai_workbench_component_spec.md`
- `../../docs/self_media_ai_workbench_ui_ux_standards.md`
- `../../docs/self_media_ai_workbench_interaction_flows.md`
- `../../docs/self_media_ai_workbench_srd.md`
- `../../docs/douyin_*_fields.md`

## 前端实现优先参考

1. `self_media_ai_workbench_page_structure.md`：页面、导航和信息架构。
2. `self_media_ai_workbench_component_spec.md`：基础组件、业务组件、AI 组件和数据组件。
3. `self_media_ai_workbench_ui_ux_standards.md`：视觉密度、图标、表格、字体和状态规范。
4. `self_media_ai_workbench_architecture.md`：表现层边界、API 分组和领域模型。
5. `self_media_ai_workbench_interaction_flows.md`：关键任务流。

## 同步方式

当根目录 `docs/` 更新后，在仓库根目录执行：

```bash
cp docs/*.md frontend-web/docs/
```

同步后如规范影响前端实现，请同时更新：

- `frontend-web/AGENTS.md`
- `frontend-web/src/types.ts`
- `frontend-web/src/api/client.ts`
- 相关页面或组件
