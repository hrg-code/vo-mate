# 输入选题预测接口实现方法

本文记录 `POST /api/v1/evolve/input-topic-porecast` 的当前实现思路，包含接口链路、Milvus 存储逻辑、检索逻辑和核心 Prompt。

> 说明：当前接口路径中的 `porecast` 应为 `forecast`，但本文按现有代码记录。

## 1. 接口定位

这个接口用于对用户输入的初步选题做“定向推演”。

核心思想不是让大模型凭空生成选题，而是：

```text
用户初步想法
  -> Embedding 向量化
  -> Milvus 历史经验库召回相似爆款基因
  -> 拼接账号人设、内容蓝图、历史表现数据
  -> LLM 输出结构化选题建议
```

它本质上是一个 RAG 风格的选题预测器：

- `user_idea` 提供当前创作者想做的话题方向。
- `content_blueprint_id` 提供视频规格约束，例如最大时长、结构策略、核心指标。
- `experience_brain` 提供历史爆款内容中的传播基因。
- `account_configs` 提供账号人设、目标受众和核心标签。
- `topic_predict_prompt.j2` 负责把这些上下文组织成大模型可执行的推演任务。

## 2. API 定义

代码位置：

```text
live-mate-backend/app/api/endpoints/evolve.py
```

路由：

```http
POST /api/v1/evolve/input-topic-porecast
```

请求体：

```json
{
  "user_idea": "程序员如何转行做自媒体",
  "content_blueprint_id": 1
}
```

当前响应统一包在 `ApiResponse` 中：

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "cluster_summary": "当前数据簇的核心场景与观众痛点分析",
    "topics": [
      {
        "title": "选题标题",
        "angle": "切入角度",
        "outline": "核心大纲",
        "hook": "黄金3秒开场"
      }
    ]
  }
}
```

## 3. 主流程

核心方法：

```text
ContentBrainService.input_topic_porecast(user_idea, content_blueprint_id)
```

流程如下：

1. 校验 `content_blueprint_id` 是否存在。
2. 通过 `ContentBlueprintService.get_by_id_content_blueprint()` 查询内容蓝图。
3. 使用 `AliyunEmbeddingService.get_embeddings([user_idea])` 将用户想法转成 1024 维向量。
4. 检查向量维度必须为 1024。
5. 使用该向量搜索 Milvus 集合 `experience_brain`。
6. 取 Top 5 历史相似切片。
7. 从检索结果中提取传播模型、情绪基调、核心逻辑、互动引信、搜索缺口词、播放和留存指标。
8. 组装 `history_context`。
9. 读取 `account_id = 1` 的账号配置。
10. 渲染 `prompt/topic_predict_prompt.j2`。
11. 调用 `deepseek-v3`。
12. 使用 `_parse_llm_json_with_repair()` 修复并解析模型 JSON 输出。

## 4. Milvus 存储设计

当前主要涉及两个 Milvus 集合：

```text
experience_brain       历史内容传播基因库，用于选题预测召回
experience_extractor   九维运营军规库，用于流量矫正/规则召回
```

集合初始化位置：

```text
live-mate-backend/app/services/content_brain_service.py
live-mate-backend/app/db/milvus_handler.py
```

### 4.1 通用 Schema

`experience_brain` 和 `experience_extractor` 当前都使用 `_build_experience_gene_schema(dim=1024)`。

核心字段：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `original_id` | VARCHAR | 主键，通常为 `video_id_idx` |
| `embeddings` | FLOAT_VECTOR(1024) | 阿里云 Embedding 向量 |
| `content` | VARCHAR | 可检索的核心文本 |
| `video_id` | VARCHAR | 来源视频 ID |
| `search_ratio` | FLOAT | 搜索流量占比 |
| `play_count` | INT64 | 播放数 |

集合开启了 `enable_dynamic_field=True`，因此可以额外写入业务字段，例如：

```text
title
description
narrative_model
audience_evolution
comment_igniter
search_gap_keyword
vibe_score
finish_rate_5s
finish_rate
bounce_rate_2s
comment_rate
full_logic_context
target_metric
reasoning
weight
created_at
```

### 4.2 向量索引

当前索引策略：

```python
index_params = {
    "index_type": "HNSW",
    "metric_type": "IP",
    "params": {"M": 16, "efConstruction": 200},
}
```

搜索参数：

```python
search_params = {
    "metric_type": "IP",
    "params": {"ef": 64},
}
```

注意：`IP` 是内积相似度，通常分数越高越相似。当前预测接口里存在 `if dist > 0.7: continue` 的过滤逻辑，这更像 L2 距离的写法，后续需要结合实际 Milvus 分数校准。

## 5. experience_brain 入库逻辑

`experience_brain` 是输入选题预测接口的主要召回库。

入库入口：

```http
POST /api/v1/evolve/{video_id}
```

核心方法：

```text
ContentBrainService.extract_video_soul(video_id)
```

### 5.1 数据来源

从 MongoDB 读取：

```text
douyin_video_raw
douyin_video_asr_results
```

使用的数据包括：

- 视频标题
- 视频简介
- ASR 口播文本
- 看前搜索词
- 看后搜索词
- 评论热词
- 播放、评论、分享、涨粉、完播、跳失等 creator_stats
- 搜索流量占比

### 5.2 LLM 提取传播基因

使用模板：

```text
prompt/scripts/script_prompt.j2
```

模型需要从 ASR、搜索词和评论热词中提取：

```json
{
  "logic_atoms": [
    "核心信息点1",
    "核心信息点2"
  ],
  "narrative_model": "叙事模型",
  "audience_evolution": "受众意图跃迁",
  "comment_igniter": "互动引信",
  "search_gap_keyword": "看后搜核心词",
  "vibe_score": "情绪基调"
}
```

### 5.3 切片策略

`logic_atoms` 中的每一个核心信息原子都会成为一条 Milvus 向量记录。

例如：

```text
logic_atoms = [
  "大龄程序员转行不是缺方向，而是缺可迁移资产",
  "自媒体不是退路，而是表达和信任的长期复利"
]
```

会写入两条记录：

```text
original_id = "{video_id}_0"
original_id = "{video_id}_1"
```

### 5.4 写入 Row Object

每条记录大致结构：

```python
row = {
    "original_id": f"{video_id}_{idx}",
    "embeddings": embeddings[i],
    "content": logic_atom,
    "video_id": str(video_id),
    "search_ratio": float(search_ratio),
    "play_count": int(play_count),
    "title": title,
    "description": description,
    "new_followers": follow_count,
    "comment_count": comment_count,
    "share_count": share_count,
    "narrative_model": narrative_model,
    "audience_evolution": audience_evolution,
    "comment_igniter": comment_igniter,
    "search_gap_keyword": search_gap_keyword,
    "vibe_score": vibe_score,
    "full_logic_context": "所有 logic_atoms 拼接文本",
    "chunk_index": idx,
    "...creator_stats": "原始指标动态字段"
}
```

写入后会执行：

```python
collection.insert(insert_list)
collection.flush()
```

开发阶段使用 `flush()` 是为了确保入库后马上可以搜索到。

## 6. experience_extractor 入库逻辑

`experience_extractor` 是九维运营军规库，主要服务于后续的流量矫正和规则召回。

入库入口：

```http
GET /api/v1/evolve/add-experience-extractor/{video_id}
```

核心方法：

```text
ContentBrainService.add_experience_extractor(video_id)
ContentBrainService.ingest_9d_experience(video_info, extracted_rules)
```

### 6.1 规则提取 Prompt

使用模板：

```text
prompt/experience_extractor.j2
```

模型需要输出 1 到 3 条可执行军规，每条规则绑定一个目标指标：

```json
[
  {
    "target_metric": "2s_survival",
    "actionable_rule": "面对大龄受众，前2秒必须用具体年龄和具体损失开场",
    "reasoning": "数据与ASR推导依据"
  }
]
```

`target_metric` 只能从以下 9 个维度中选择：

```text
2s_survival
5s_retention
total_finish
engagement_like
engagement_collect
engagement_share
engagement_comment
conversion_follow
seo_after_search
```

### 6.2 九维规则向量化文本

每条规则入库前会先组装一个语义上下文：

```text
视频话题：{title}。针对维度：{target_metric}。规则指令：{actionable_rule}
```

这个文本会被转成 1024 维向量。

这样做的目的是让后续检索不仅能匹配规则本身，还能匹配：

- 视频话题
- 运营指标
- 可执行动作

### 6.3 写入 Row Object

每条九维规则写入结构：

```python
row = {
    "original_id": f"{video_id}_{idx}",
    "embeddings": vector,
    "content": rule["actionable_rule"],
    "weight": performance_weight,
    "target_metric": rule["target_metric"],
    "reasoning": rule.get("reasoning", "无推理逻辑"),
    "video_id": str(video_id),
    "title": title,
    "search_ratio": search_ratio,
    "description": description,
    "created_at": int(time.time()),
    "...creator_stats": "原始指标动态字段"
}
```

其中：

```python
performance_weight = finish_rate * 0.6 + finish_rate_5s * 0.4
```

这个权重用于表达该条规则背后视频的留存表现。

## 7. 输入选题预测的检索逻辑

预测接口只检索 `experience_brain`。

### 7.1 用户想法向量化

```python
raw_vector = await self.embedding_service.get_embeddings([user_idea])
clean_vector = raw_vector[0]
final_vector = [float(x) for x in clean_vector]
```

维度必须为 1024：

```python
if len(clean_vector) != 1024:
    return None
```

### 7.2 搜索 experience_brain

```python
results = self.milvus.search(
    collection_name="experience_brain",
    vectors=[final_vector],
    search_params={"metric_type": "IP", "params": {"ef": 64}},
    limit=5,
    output_fields=[
        "content",
        "logic_atoms",
        "narrative_model",
        "audience_evolution",
        "comment_igniter",
        "search_gap_keyword",
        "vibe_score",
        "play_count",
        "finish_rate_5s",
        "finish_rate",
        "bounce_rate_2s",
        "comment_rate",
        "full_logic_context"
    ],
)
```

### 7.3 组装历史上下文

每条命中结果会被整理成类似文本：

```text
### 历史参考基因 1 (相似度: 0.82)
【传播模型】：认知重塑 | 【情绪基调】：清醒
【核心逻辑】：大龄程序员不是缺出路，而是缺可迁移资产
【受众跃迁】：从转行焦虑跃迁到资产复用意识
【互动炸弹】：观众在评论区讨论年龄、学历、收入下滑
【实战战绩】：
  - 流量：100000 播放 | 完播率 45.0%
  - 留存：2秒留存 68.0% | 5秒跳失 42.0%
  - 下一期截流词：大龄程序员转行
---------------------------------
```

如果没有有效命中，则兜底为：

```text
基因库未命中高度相关案例，请基于通用爆款逻辑与行业常识进行零基建推演。
```

## 8. Prompt：选题预测

文件：

```text
prompt/topic_predict_prompt.j2
```

当前模板：

```jinja2
{# 顶级短视频内容战略引擎模版 #}
你是一个顶级短视频内容战略师。
请严格遵守以下【创作者核心约束】：
- 创作者人设：{{ account_configs.persona_background }}
- 目标受众：{{ account_configs.target_audience }}
- 核心标签：{{ account_configs.core_tags | join('、') }}

【当前任务】：
我向你输入了从数据库中提取的【历史高潜切片】（它们属于同一个未知的数据簇）。
{% if user_idea %}
- 定向引导：创作者当前有一个初步想法，请优先结合此想法与历史数据进行碰撞。
- 想法：{{ user_idea }}
{% endif %}
{% if content_blueprint %}
- 预期视频时长：{{ content_blueprint.max_duration }}秒
- 内容类型：口播
{% endif %}

请作为理性的分析引擎，执行以下步骤：
---
{{ history_context }}
---

【步骤 1：无监督抽象】
请分析这些散乱的切片，用一句话总结：这个数据簇探讨的核心业务场景是什么？观众在当前场景下最根本的痛点或认知偏差是什么？

【步骤 2：底线对齐与推演】
基于步骤 1 请根据数据质量输出 1-3 个 选题。如果数据高度一致，请只给一个‘重锤级’选题并配上深度脚本；如果数据散乱，请给出三个不同维度的切入点供我筛选。
- 要求：无论数据反映出的观众欲望有多离谱（比如想找捷径），你都必须用创作者的价值观（真实、泼冷水、说真话）去进行降维纠偏。
- 不要迎合观众的虚假希望，要给出该业务场景下的残酷真相或务实建议。

请按以下 JSON 格式输出：
{
    "cluster_summary": "当前数据簇的核心场景与观众痛点分析（客观总结）",
    "topics": [
        {
            "title": "符合价值观的犀利标题",
            "angle": "切入角度：为何用这种方式回应观众痛点",
            "outline": "核心大纲必须符合人设，设计逻辑上的‘语言陷阱’或‘情绪反转’**，每一句话都有信息增量。",
            "hook": "黄金3秒开场"
        }
    ]
}
```

## 9. Prompt：传播基因提取

文件：

```text
prompt/scripts/script_prompt.j2
```

用途：从单条历史视频中提取 `experience_brain` 所需的传播基因。

输出格式：

```json
{
  "logic_atoms": [
    "核心信息点1...",
    "核心信息点2..."
  ],
  "narrative_model": "叙事模型类型（如：认知重塑/痛点共鸣/实操交付）",
  "audience_evolution": "精准描述受众从‘模糊需求A’到‘具体需求B’的思维跃迁",
  "comment_igniter": "触发互动的核心爆点（观众在评论区最关注什么）",
  "search_gap_keyword": "看后搜中权重最高、最具选题复利价值的那个核心词",
  "vibe_score": "用一个词形容该视频的整体情绪基调（如：清醒、激进、治愈、压抑）"
}
```

关键输入：

```jinja2
【ASR口播原文】：
{{ asr_text }}

【多维数据上下文】：
- 初始搜索（基准意图）：{{ pre_search_list }}
- 启发搜索（意图转移）：{{ post_search_list }}
- 评论热词（群体反馈）：{{ comment_words_list }}
```

## 10. Prompt：九维军规提取

文件：

```text
prompt/experience_extractor.j2
```

用途：从历史视频中提炼可复用于下一次脚本生成或流量矫正的运营铁律。

核心要求：

- 结合 ASR 时间轴和漏斗数据，找出开场留人或赶客的话术结构。
- 结合评论、搜索词和互动数据，找出刺痛观众的具体表达。
- 输出必须是可执行动作，而不是“要吸引人”“要有共鸣”这种泛化建议。
- 如果视频数据平庸，可以返回空数组，避免污染规则库。

输出格式：

```json
[
  {
    "target_metric": "2s_survival",
    "actionable_rule": "提炼出的具体执行动作指令",
    "reasoning": "数据与ASR推导依据"
  }
]
```

允许的 `target_metric`：

```text
2s_survival
5s_retention
total_finish
engagement_like
engagement_collect
engagement_share
engagement_comment
conversion_follow
seo_after_search
```

## 11. 当前方案优缺点

### 优点

- 不是纯 LLM 生成，而是基于历史数据召回，选题更贴近账号真实表现。
- `logic_atoms` 切片粒度较细，有利于复用历史内容里的传播结构。
- `content_blueprint` 可以把生成约束到具体视频时长和内容规格。
- Milvus 动态字段让早期原型迭代很快，可以不断补充指标字段。
- 同时沉淀 `experience_brain` 和 `experience_extractor`，分别覆盖选题召回和运营矫正。

### 缺点和风险

- 预测效果高度依赖历史视频入库质量。
- `account_id = 1` 当前写死，不适合多账号场景。
- `IP` 相似度的过滤阈值需要重新校准，当前 `dist > 0.7` 的过滤方向可能不合理。
- LLM JSON 输出靠修复函数兜底，缺少强 schema 校验。
- 错误场景目前会返回字符串并包成 `200 success`，不利于前端区分失败原因。
- 召回只基于 `user_idea` 单向量，容易陷入语义相似，跨领域迁移能力有限。

## 12. 后续优化方向

建议后续按以下顺序增强：

1. 新增正确路径 `/api/v1/evolve/input-topic-forecast`，旧路径保留兼容。
2. 请求体增加 `account_id` 或从登录态解析账号。
3. 为返回值定义 Pydantic response schema。
4. 校准 Milvus `IP` 分数阈值，并记录召回分数。
5. 返回 `evidence` 字段，展示每个选题引用了哪些历史基因。
6. 给每个选题增加 `confidence_score`、`risk_points`、`recommended_blueprint`。
7. 将用户想法拆成多个检索 query，例如痛点 query、场景 query、情绪 query，提高跨域召回能力。
8. 将发布后的真实表现回写到 Milvus 和关系库，形成选题预测闭环。
