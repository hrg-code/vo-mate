# AGENTS.md

本文件约束 `frontend-web` 目录内的前端实现。面向 Codex、Copilot、Claude Code 等编码代理；人类开发者也可作为协作规范使用。

## 项目定位

- 本目录是 VO Mate 的 React Web 工作台，负责表现层 UI、前端交互和 `/api/v1/*` API 边界适配。
- 产品形态是工作台，不是营销页。优先保证信息密度、可扫描性、任务推进效率和状态可解释性。
- 设计与页面结构需参考仓库根目录下的文档：
  - `docs/self_media_ai_workbench_architecture.md`
  - `docs/self_media_ai_workbench_page_structure.md`
  - `docs/self_media_ai_workbench_component_spec.md`
  - `docs/self_media_ai_workbench_ui_ux_standards.md`

## 技术栈

- React 19 + TypeScript
- Vite
- Ant Design 作为默认 UI 组件库
- `lucide-react` 图标
- CSS 使用 `src/styles.css` 中的现有类名体系，除非改动范围需要拆分样式文件。
- 默认使用 mock 数据；后端接入通过环境变量切换。

## 常用命令

在 `frontend-web` 目录执行：

```bash
npm install
npm run dev
npm run build
npm run lint
```

说明：

- `npm run dev` 启动 Vite，本地默认访问 `http://localhost:5173/`。
- `npm run build` 会先执行 `tsc -b`，再执行 `vite build`。
- `npm run lint` 使用 ESLint 扫描当前目录。

## 环境变量

- `VITE_USE_MOCKS`：不设置或不为 `false` 时使用 `src/api/mockData.ts`。
- `VITE_API_BASE_URL`：真实后端 API 基础地址，默认 `/api/v1`。

接入 FastAPI 示例：

```bash
VITE_USE_MOCKS=false
VITE_API_BASE_URL=http://localhost:8000/api/v1
```

## 目录职责

```text
docs/           从仓库根目录 docs 同步的前端实现规范
src/
  api/          API client、mock 数据和后端边界适配
  components/   可复用展示与布局组件
  features/     按业务能力组织的复合组件
  pages/        页面级组件
  App.tsx       顶层路由状态、数据装配和页面切换
  theme.ts      Ant Design 主题 token
  types.ts      前端共享领域类型
  styles.css    全局样式与设计 token
```

约定：

- 页面级组件放在 `src/pages`，只负责页面组合、页面动作和数据呈现。
- 复用组件放在 `src/components`，避免耦合具体页面的临时状态。
- 跨页面业务能力放在 `src/features/<feature>`，例如 evidence、tasks。
- API 返回结构和领域类型优先在 `src/types.ts` 中显式建模，不要在组件里散落匿名复杂类型。

## 编码规范

- 使用函数组件和显式 props 类型，保持 TypeScript 类型收敛。
- 复用现有 `RouteId`、`Platform`、`ContentItem` 等领域类型；新增业务对象时同步补充 `src/types.ts`。
- 保持 import 路径相对清晰：页面引用组件，组件引用类型或更小组件，避免循环依赖。
- 避免在 JSX 中堆叠复杂计算；复杂派生数据放到组件上方常量、局部函数或 `useMemo`。
- 新增基础控件优先使用 Ant Design，包括 Button、Input、Select、Table、Drawer、Modal、Tabs、Tooltip、Empty、Tag、Form。
- Ant Design 主题集中维护在 `src/theme.ts`，不要在组件内重复硬编码主色、圆角和字体 token。
- `lucide-react` 继续作为业务图标来源，可传入 Ant Design 的 `icon`、`prefix` 或自定义插槽。
- 不引入新的状态管理、路由、图表或第二套 UI 框架，除非任务明确需要，并且已说明取舍。
- 不提交 `dist`、`node_modules` 或构建产物的无关变更。
- 默认保持 ASCII；中文 UI 文案可使用中文。

## UI 与交互规范

- 工作台页面应保持克制、专业、信息密集，避免落地页式大 Hero、装饰性卡片堆叠和纯氛围背景。
- 组件优先使用 Ant Design；只有现有业务卡片、图表占位和定制布局继续使用本地 CSS。
- 图标优先使用 `lucide-react`；图标按钮必须提供 Tooltip、`title` 或 `aria-label`。
- 工具型动作优先使用熟悉图标，例如搜索、筛选、刷新、下载、保存、复制。
- 关键破坏性动作不能只用图标，必须有文字或确认流程。
- 默认圆角不超过 `8px`，除非复用现有样式已有明确设定。
- 表格、看板、抽屉、任务状态、AI 结果组件必须考虑空状态、加载状态、错误状态和权限不足状态。
- 数据图表必须辅助判断，不做装饰；需要展示单位、异常标注和空状态。
- 字体不要随视口宽度缩放，字间距保持 `0`。
- 移动和桌面视口下文本不得溢出按钮、卡片、导航项或表格单元格。

## API 规范

- 所有后端请求统一通过 `src/api/client.ts` 暴露的 `api` 对象进入，不要在页面组件里直接拼 `fetch`。
- API 路径保持 `/api/v1/*` 边界，当前主要分组包括：
  - `/workspaces/current`
  - `/analytics/dashboard`
  - `/contents`
  - `/ai/topic-ideas`
  - `/ai/evidence`
  - `/workflows/tasks`
  - `/memory/patterns`
  - `/workflows/publish-plans`
- mock 数据需要与真实 API 类型保持一致；新增接口时同步补齐 mock，以便前端可独立预览。
- 外部平台 ID、视频 ID、任务 ID 等标识符按字符串处理，避免大整数精度问题。

## 可访问性与可用性

- 交互元素使用语义化元素：按钮用 `button`，输入用 `input`/`textarea`，导航区使用 `nav`。
- 图标装饰时加 `aria-hidden="true"`；只有图标的可点击元素必须有 `aria-label`。
- 页面主内容保持可聚焦或可被辅助技术定位。
- 表格数据需要保留可读文本，不要只依赖颜色表达状态。

## 验证清单

完成改动后，根据改动范围执行：

```bash
npm run build
npm run lint
```

涉及 UI 的改动还应本地打开 Vite 页面检查：

- 页面是否能正常加载。
- 控件、文本、抽屉、表格在常见桌面宽度下不重叠、不溢出。
- mock 模式和真实 API 模式的边界没有被破坏。
- 新增页面或导航项已同步更新 `RouteId`、`AppShell` 导航和 `App.tsx` 页面切换。

## 修改优先级

当需求与现有实现冲突时，按以下顺序取舍：

1. 用户当前明确需求。
2. 产品与架构文档中的页面、组件、API 约定。
3. 本文件规范。
4. 现有代码风格和目录组织。

如需偏离上述规范，请在提交说明或回复中简短解释原因。
