# AI 自媒体工作台页面结构设计

版本：v0.1  
日期：2026-05-09  
目标：定义 React Web 工作台的信息架构、页面层级、路由和页面内容结构。

## 1. 页面结构原则

- 首页直接进入工作台，不做落地页。
- 导航围绕创作者工作流，而不是数据库结构。
- 每个页面必须有主任务。
- 数据页优先支持筛选、排序、对比、钻取。
- AI 页优先支持输入、生成、查看依据、保存版本。
- 复盘和记忆页必须支持“确认/驳回”，让系统学习可控。

## 2. 一级导航

建议左侧主导航：

| 导航 | 路由 | 主要目的 |
| --- | --- | --- |
| 首页 | `/dashboard` | 查看表现、待办和今日 AI 建议 |
| 视频库 | `/contents` | 管理和分析历史内容 |
| 粉丝画像 | `/audience` | 查看粉丝趋势、画像和兴趣 |
| 选题雷达 | `/topics` | 生成、评分和管理选题 |
| 脚本工作台 | `/scripts` | 生成和编辑口播脚本 |
| SEO 优化 | `/seo` | 标题、简介、标签、关键词优化 |
| 发布日历 | `/calendar` | 管理内容排期 |
| 复盘中心 | `/retrospectives` | 查看视频复盘和周/月报 |
| 记忆库 | `/memory` | 管理 Milvus 学到的模式 |
| 采集管理 | `/collector` | 管理 Electron/插件采集任务 |
| 设置 | `/settings` | 工作区、账号、模型、权限配置 |

## 3. 全局 App Shell

```text
AppShell
  TopBar
    WorkspaceSwitcher
    PlatformAccountSelector
    GlobalSearch
    TaskCenter
    NotificationCenter
    UserMenu
  SideNav
    PrimaryNav
    CollapseButton
  Main
    PageHeader
    PageContent
  Optional
    RightPanel / Drawer
```

### TopBar 内容

- 当前 workspace。
- 当前账号范围。
- 全局搜索。
- 正在运行的任务。
- 通知。
- 用户菜单。

### SideNav 内容

- 一级模块。
- 当前选中状态。
- 收起/展开。
- 采集状态小提示。

### PageHeader 内容

- 页面标题。
- 说明性副标题。
- 时间范围。
- 平台/账号筛选。
- 主要操作按钮。

## 4. 首页 `/dashboard`

### 页面目标

让用户 30 秒内知道账号现状和今天该做什么。

### 页面结构

```text
Dashboard
  PageHeader
  TodayActionPanel
  MetricOverviewGrid
  PerformanceTrend
  OpportunityPanel
  RecentContentTable
  AlertsPanel
```

### 模块说明

| 模块 | 内容 |
| --- | --- |
| 今日 AI 建议 | 推荐操作：复盘某条视频、继续某个选题、补充采集 |
| 指标概览 | 播放、互动、涨粉、完播、搜索流量 |
| 表现趋势 | 7/30/90 日趋势 |
| 机会面板 | 高潜力选题、搜索机会、可承接内容 |
| 最近内容 | 最新发布视频表现 |
| 异常提醒 | 播放异常、涨粉异常、采集失败 |

### 主要操作

- 生成今日选题。
- 查看异常视频。
- 同步数据。
- 进入复盘。

## 5. 视频库 `/contents`

### 页面目标

统一查看所有平台内容，支持筛选、排序、分析和进入详情。

### 页面结构

```text
ContentsPage
  PageHeader
  FilterBar
  SegmentTabs: All / Douyin / Kuaishou / Xiaohongshu / YouTube / WeChat
  ContentTable
  BulkActionBar
  RightDrawer: QuickInsight
```

### 表格字段

- 封面。
- 标题。
- 平台。
- 发布时间。
- 时长。
- 播放量。
- 点赞。
- 评论。
- 收藏。
- 分享。
- 完播率。
- 平均观看。
- 涨粉。
- 综合评分。
- 状态。

### 筛选条件

- 平台。
- 账号。
- 发布时间。
- 视频时长。
- 话题。
- 标签。
- 播放量区间。
- 完播率区间。
- 是否有 ASR。
- 是否已复盘。

### 主要操作

- 查看详情。
- 生成复盘。
- 找相似内容。
- 生成承接选题。
- 加入内容实验。

## 6. 视频详情 `/contents/:contentId`

### 页面目标

解释一条内容表现，并提供下一步动作。

### 页面结构

```text
ContentDetailPage
  ContentDetailHeader
  MetricSummary
  Tabs
    Overview
    Traffic
    Audience
    ASR
    SEO
    Retrospective
    Raw Data
  RightPanel: AI Insight / Evidence
```

### Header 内容

- 封面。
- 标题。
- 平台。
- 发布时间。
- 时长。
- 内容状态。
- 主要操作：生成复盘、生成承接选题、复制链接。

### Overview Tab

- 核心指标。
- 表现评分。
- 指标对比：账号中位数、同类内容均值。
- AI 一句话结论。

### Traffic Tab

- 流量来源占比。
- 搜索关键词。
- 推荐/关注/主页等来源趋势。

### Audience Tab

- 性别。
- 年龄。
- 地域。
- 兴趣。
- 新老用户。
- 粉丝/非粉丝。

### ASR Tab

- 完整口播文本。
- 分段时间轴。
- 高亮开头 3 秒、转折句、CTA。
- 一键生成脚本结构分析。

### SEO Tab

- 标题关键词覆盖。
- 简介关键词覆盖。
- 标签。
- 搜索词表现。

### Raw Data Tab

- MongoDB 原始数据引用。
- JSON Viewer。
- 字段字典链接。

## 7. 粉丝画像 `/audience`

### 页面目标

帮助用户理解粉丝是谁、何时活跃、喜欢什么。

### 页面结构

```text
AudiencePage
  PageHeader
  FansSummary
  FansTrendChart
  DemographicGrid
  InterestPanel
  ActiveTimeHeatmap
  FanSourceTable
  AIInsightPanel
```

### 模块说明

- 粉丝总数。
- 净增/取关趋势。
- 性别年龄地域。
- 兴趣分布。
- 活跃时间。
- 粉丝来源。
- 高互动粉丝。
- AI 人群洞察。

## 8. 选题雷达 `/topics`

### 页面目标

从历史数据和用户输入中发现可拍选题。

### 页面结构

```text
TopicRadarPage
  PageHeader
  TopicInputPanel
  StrategyControls
  TopicCandidateList
  TopicScoreDetail
  SimilarContentPanel
```

### 输入区

- 想探索的方向。
- 目标平台。
- 内容目标：播放、涨粉、搜索、互动、转化。
- 视频长度。
- 人设语气。
- 是否参考热点。

### 输出区

- 选题卡片。
- 预测分。
- 推荐理由。
- 风险。
- 相似历史内容。
- 一键生成脚本。

### 选题详情页 `/topics/:topicId`

```text
TopicDetailPage
  TopicHeader
  ScoreBreakdown
  EvidenceList
  TitleCandidates
  ScriptEntry
  PlatformFit
  ActionHistory
```

## 9. 脚本工作台 `/scripts`

### 页面目标

把选题转为可拍、可改、可发布的口播内容。

### 页面结构

```text
ScriptStudioPage
  LeftPanel: Topic / References / Versions
  Center: ScriptEditor
  RightPanel: AI Copilot / SEO / Platform
```

### 左侧

- 当前选题。
- 历史相似视频。
- 版本列表。
- 素材引用。

### 中间

- 脚本正文编辑器。
- 段落结构标注。
- 字数和预计时长。
- 分段字幕预览。

### 右侧

- AI 改写。
- 生成标题。
- 生成简介。
- 生成标签。
- 平台适配检查。
- 风险检查。

## 10. SEO 优化 `/seo`

### 页面目标

为内容生成平台适配的标题、简介、标签、关键词布局。

### 页面结构

```text
SEOPage
  PageHeader
  ContentSelector
  PlatformTabs
  TitleLab
  DescriptionEditor
  TagPanel
  SEOChecklist
  HistoryBenchmark
```

### 功能

- 标题评分。
- 关键词覆盖。
- 平台长度限制。
- 标签推荐。
- 相似标题表现对照。
- A/B 标题版本。

## 11. 发布日历 `/calendar`

### 页面目标

管理内容从脚本到发布的计划。

### 页面结构

```text
PublishCalendarPage
  PageHeader
  CalendarView
  KanbanView
  ContentQueue
  PublishDetailDrawer
```

### 视图

- 日历视图。
- 看板视图。
- 列表视图。

### 状态列

- 灵感。
- 已生成脚本。
- 待拍摄。
- 待剪辑。
- 待发布。
- 已发布。
- 已复盘。

## 12. 复盘中心 `/retrospectives`

### 页面目标

管理单条视频复盘、周期报告和可沉淀经验。

### 页面结构

```text
RetrospectivePage
  PageHeader
  ReportTabs: Videos / Weekly / Monthly / Patterns
  RetrospectiveList
  RetrospectiveDetail
  MemoryCandidatePanel
```

### 复盘详情

- 一句话结论。
- 指标表现。
- 主要问题。
- 成功点。
- 口播分析。
- SEO 分析。
- 受众分析。
- 下一条建议。
- 是否写入记忆库。

## 13. 记忆库 `/memory`

### 页面目标

让用户查看、确认、删除和调整系统学到的经验。

### 页面结构

```text
MemoryPage
  PageHeader
  MemoryFilters
  MemoryPatternList
  MemoryDetailDrawer
  SourceEvidencePanel
```

### 记忆类型

- 成功模式。
- 失败模式。
- 标题模式。
- 口播结构。
- SEO 关键词。
- 受众偏好。
- 账号人设。

### 操作

- 确认有效。
- 标记过期。
- 降低权重。
- 删除。
- 查看来源。

## 14. 采集管理 `/collector`

### 页面目标

管理 Electron 和浏览器插件的数据采集状态。

### 页面结构

```text
CollectorPage
  PageHeader
  CollectorStatusGrid
  TaskTable
  PlatformConnectorList
  ImportHistory
  LogDrawer
```

### 模块

- 采集端在线状态。
- 平台连接状态。
- 同步任务。
- 最近采集日志。
- 手动导入。
- 错误重试。

## 15. 设置 `/settings`

### 设置分组

| 分组 | 内容 |
| --- | --- |
| 工作区 | 名称、成员、权限 |
| 平台账号 | 抖音、快手、小红书、YouTube、视频号 |
| AI 模型 | LLM、Embedding、Reranker、成本限制 |
| 人设风格 | 语气、禁用词、品牌词、CTA |
| 数据采集 | 频率、保留策略、采集端 |
| 记忆策略 | 入库阈值、置信度、审核规则 |
| 安全 | 密码、API key、日志脱敏 |

## 16. 路由结构

```text
/login
/dashboard
/contents
/contents/:contentId
/audience
/topics
/topics/:topicId
/scripts
/scripts/:scriptId
/seo
/calendar
/retrospectives
/retrospectives/:reportId
/memory
/collector
/settings
/settings/workspace
/settings/accounts
/settings/ai
/settings/style
/settings/security
```

## 17. MVP 页面优先级

### P0

- `/dashboard`
- `/contents`
- `/contents/:contentId`
- `/topics`
- `/scripts`
- `/retrospectives`
- `/memory`

### P1

- `/audience`
- `/seo`
- `/collector`
- `/settings`

### P2

- `/calendar`
- 多平台专属子页面。
- 团队协作页面。

