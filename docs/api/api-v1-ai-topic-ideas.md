这个接口目前不是“纯 LLM 随口生成”，而是一条 选题生成流水线。

入口在 backend/app/api/v1/ai.py (line 19)：

POST /api/v1/ai/topic-ideas 接收 TopicIdeaGenerateRequest，然后返回 text/event-stream，也就是 SSE 流式事件。



核心流程在 backend/app/services/topic_idea_service.py (line 25)：

先创建 generationId，记录一次生成审计。
读取 workspace / 账号上下文。
读取历史内容表现数据。
召回相似长期记忆和历史证据。
简单分析 pattern，例如最高分内容、证据数量、推荐方向。
调用 AI Provider 生成候选。
对候选做字段补齐、数量兜底、分数归一。
按 predictedScore 降序排序。
保存到 PostgreSQL；如果不可用则保存到内存仓库。
通过 SSE 依次吐出 start、progress、evidence、topic_idea、done。

证据召回在 backend/app/services/topic_evidence_service.py (line 65)：优先级是：

Milvus 向量召回记忆 ID。
用 PostgreSQL 或内存仓库补全记忆证据。
Milvus 不可用时，回退 PostgreSQL 关键词/标准层数据。
PostgreSQL 也不可用时，回退 MVP 内存样例。

生成本身在 backend/app/services/topic_idea_service.py (line 125)：它把这些上下文传给 provider：

text



direction
workspace
accountIds
platforms
goal
count
audience
constraints
contentMetrics
evidence
patternSummary
dataSourceMode



Provider 有两种：


如果 VO_MATE_LLM_PROVIDER=deepseek 且配置了 VO_MATE_DEEPSEEK_API_KEY，会请求 DeepSeek，要求返回 JSON。

否则走 mock provider。


mock provider 在 backend/app/services/ai_provider_service.py (line 66)，它基于固定模板生成，比如“岗位切换”“AI 协作”“搜索承接”“失败复盘”“爆款结构”等，再把用户传入的 direction 拼进去。所以开发环境里看起来像“AI 生成”，但多数情况下其实是稳定模板生成。

一个关键细节：即使真实模型返回字段不完整，服务也会在 _coerce_candidates() 里兜底补齐标题、角度、受众、平台、评分、风险、推荐理由、hooks、tags、nextActions 等字段，位置在 backend/app/services/topic_idea_service.py (line 151)。

所以现在的本质是：

方向输入 + 历史内容表现 + 记忆证据 + 简单 pattern summary + LLM/mock JSON 候选 + 后处理排序持久化。

目前比较 MVP 的地方是评分和 pattern 分析还偏浅：patternSummary 只取了 top content 和 evidence count，mock 评分也主要是模板分数加证据数量。后面如果要做得更像真正的选题策略 Agent，可以增强这几块：历史爆款结构归因、低表现避坑、评论问题聚类、搜索词机会、平台差异评分，以及让 predictedScore 明确由几个可解释因子加权算出来。



完善这个
我建议的 MVP 落地顺序

第一版先不要急着上 embedding，先把结构做对：

阶段 1：
- load_content_metrics 改名或新增 load_topic_content_evidence
- 加 accountIds/platform_account_id 过滤
- 拆成 relatedContents / topPerformers / contrastContents
- relatedContents 用 title/description/tags/keywords/text_assets 关键词命中
- topPerformers 保留当前高表现逻辑
第二版再加 embedding：

阶段 2：
- 给 content item 建 embedding 文本
- Milvus 按 workspace/account/platform metadata filter
- embedding topK 与关键词候选合并
- 加 relevance gate
第三版再上 LLM rerank：

阶段 3：
- 对候选做 same_topic / adjacent_topic / weak / unrelated 判断
- 输出 reason
- 让审计记录保存 retrievalDiagnostics
我的推荐结论是：

先做“证据分层 + 相关性门控”，再做 embedding。
因为如果证据结构不分层，embedding 也只是让“跑偏内容”变得更隐蔽。
最优路线不是“先智能”，而是先把证据语义分清楚：哪些是当前方向证据，哪些只是风格参考，哪些是反例。