import type {
  AgentTask,
  ContentItem,
  CollectorImportResponse,
  EvidenceItem,
  MemoryPattern,
  MetricSummary,
  PublishPlan,
  ScriptDraft,
  TopicIdea,
  WorkspaceContext
} from "../types";
import { composeScriptBody, createScriptBlock } from "../features/scripts/scriptBlocks";

export const workspace: WorkspaceContext = {
  workspaceId: "ws_northstar",
  workspaceName: "北极星内容组",
  accountName: "抖音 · 程序员老陈",
  platformScope: ["douyin"]
};

export const dashboardMetrics: MetricSummary[] = [
  { label: "播放量", value: "34.6w", delta: "+42%", direction: "up", description: "较账号 30 日中位数" },
  { label: "互动率", value: "7.8%", delta: "+1.2%", direction: "up", description: "点赞、评论、收藏、分享综合" },
  { label: "涨粉", value: "1,286", delta: "+36%", direction: "up", description: "本周期内容转化" },
  { label: "完播率", value: "38%", delta: "-4%", direction: "down", description: "需检查开头与中段流失" },
  { label: "搜索流量", value: "21%", delta: "+9%", direction: "up", description: "关键词承接机会增强" }
];

export const contents: ContentItem[] = [
  {
    id: "ct_7585913482206383412",
    title: "程序员 35 岁后还能不能继续写代码",
    platform: "douyin" as const,
    publishedAt: "2026-05-08",
    durationSeconds: 62,
    views: 346000,
    likes: 19000,
    comments: 892,
    saves: 4320,
    shares: 1182,
    completionRate: 0.38,
    followersGained: 1286,
    score: 89,
    status: "published",
    hasAsr: true,
    reviewed: true
  },
  {
    id: "ct_resume_hr",
    title: "为什么你的简历总被 HR 刷掉",
    platform: "douyin" as const,
    publishedAt: "2026-05-06",
    durationSeconds: 48,
    views: 182000,
    likes: 8431,
    comments: 521,
    saves: 2900,
    shares: 803,
    completionRate: 0.42,
    followersGained: 604,
    score: 82,
    status: "needs_review",
    hasAsr: true,
    reviewed: false
  },
  {
    id: "ct_ai_three_chances",
    title: "AI 时代普通程序员的三个机会",
    platform: "wechat",
    publishedAt: "2026-05-04",
    durationSeconds: 91,
    views: 97000,
    likes: 3126,
    comments: 318,
    saves: 1504,
    shares: 512,
    completionRate: 0.31,
    followersGained: 298,
    score: 76,
    status: "script_reusable",
    hasAsr: true,
    reviewed: false
  },
  {
    id: "ct_outsource_truth",
    title: "外包五年后我学到的残酷真相",
    platform: "xiaohongshu",
    publishedAt: "2026-05-02",
    durationSeconds: 55,
    views: 124000,
    likes: 5980,
    comments: 437,
    saves: 3888,
    shares: 760,
    completionRate: 0.45,
    followersGained: 781,
    score: 86,
    status: "seo_opportunity",
    hasAsr: true,
    reviewed: true
  }
];

export const collectorImportResponse: CollectorImportResponse = {
  taskId: "task_raw-import_mock",
  status: "succeeded",
  processedCount: 4,
  upsertedCount: 4,
  failedCount: 0,
  textAssetCount: 12,
  tagCount: 9,
  keywordCount: 8,
  trafficSourceCount: 3,
  asrCount: 4
};

export const topicIdeas: TopicIdea[] = [
  {
    id: "tp_role_shift",
    title: "35 岁程序员不是危机，是岗位切换信号",
    topic: "程序员职业成长",
    angle: "把年龄焦虑改写成职业策略，适合 60 秒强钩子口播。",
    category: "career_growth",
    targetAudience: "25-35 岁普通程序员",
    predictedScore: 91,
    seoScore: 86,
    audienceScore: 93,
    difficultyScore: 41,
    risk: "情绪过强会降低完播",
    recommendReason: "历史职业焦虑内容评论强，适合改写成更可执行的岗位切换策略。",
    evidenceCount: 12,
    targetPlatforms: ["douyin", "xiaohongshu"],
    suggestedTitles: ["35 岁程序员不是危机，是岗位切换信号"],
    suggestedHooks: ["如果你也在担心 35 岁，先别急着否定自己。"],
    suggestedTags: ["#程序员", "#职业规划"],
    nextActions: ["generate_titles", "generate_script", "save_to_topic_pool"]
  },
  {
    id: "tp_ai_task_split",
    title: "AI 不会淘汰程序员，但会淘汰不会拆任务的人",
    topic: "AI 协作能力",
    angle: "用真实项目拆解 AI 协作边界，承接近期搜索词。",
    category: "ai_collaboration",
    targetAudience: "AI 时代有转型焦虑的程序员",
    predictedScore: 87,
    seoScore: 92,
    audienceScore: 84,
    difficultyScore: 52,
    risk: "需要避免泛泛讲工具",
    recommendReason: "AI 与程序员关键词搜索价值高，适合用任务拆分做差异化表达。",
    evidenceCount: 8,
    targetPlatforms: ["douyin", "wechat"],
    suggestedTitles: ["AI 不会淘汰程序员，但会淘汰不会拆任务的人"],
    suggestedHooks: ["会用 AI 的第一步，不是写 Prompt。"],
    suggestedTags: ["#AI编程", "#程序员成长"],
    nextActions: ["generate_titles", "generate_script", "save_to_topic_pool"]
  },
  {
    id: "tp_career_cost",
    title: "普通人转码前先算清这三笔账",
    topic: "转码决策",
    angle: "面向泛职场人群，适合小红书搜索和收藏。",
    category: "seo_opportunity",
    targetAudience: "考虑转码的泛职场人群",
    predictedScore: 79,
    seoScore: 88,
    audienceScore: 72,
    difficultyScore: 47,
    risk: "账号人设匹配中等",
    recommendReason: "转码成本属于搜索型问题，适合用清单结构承接收藏。",
    evidenceCount: 6,
    targetPlatforms: ["xiaohongshu"],
    suggestedTitles: ["普通人转码前先算清这三笔账"],
    suggestedHooks: ["转码不是不能做，但这三笔账要先算清。"],
    suggestedTags: ["#转码", "#职业选择"],
    nextActions: ["generate_titles", "generate_script", "save_to_topic_pool"]
  }
];

export const evidence: EvidenceItem[] = [
  {
    id: "ev_content_1",
    type: "content",
    title: "程序员 35 岁后还能不能继续写代码",
    description: "播放 34.6w，完播 38%，涨粉 1,286，相关性 94%。",
    source: "PostgreSQL content_items + douyin_video_raw",
    score: 94,
    metrics: ["播放 34.6w", "完播 38%", "涨粉 1,286"],
    action: "复用“年龄焦虑 -> 岗位切换”的叙事，但降低恐慌表达。"
  },
  {
    id: "ev_content_2",
    type: "content",
    title: "转码三年后，我最后悔没早点做这件事",
    description: "收藏率高于账号均值 31%，但评论争议集中在“不可复制”。",
    source: "relatedContents / llmRelevanceLevel=same_topic",
    score: 89,
    metrics: ["收藏率 +31%", "评论 2,418"],
    action: "建议把个人经历改成普通人可执行清单，减少个案感。"
  },
  {
    id: "ev_metric_1",
    type: "metric",
    title: "职业转折类内容的稳定表现",
    description: "近 90 天同类内容平均完播和涨粉贡献都高于账号均值。",
    source: "content_lifetime_metrics",
    score: 91,
    metrics: ["完播 +12%", "互动 +18%", "涨粉 +24%"],
    action: "预测分主要由历史表现和受众匹配抬升。"
  },
  {
    id: "ev_keyword_1",
    type: "keyword",
    title: "35 岁危机 / AI 程序员 / 转型",
    description: "近 7 日搜索流量占比从 12% 升至 21%。",
    source: "creator_seo_vectors",
    score: 88,
    metrics: ["搜索占比 21%", "环比 +9%"],
    action: "标题保留“35 岁”“程序员”两个搜索锚点。"
  },
  {
    id: "ev_audience_1",
    type: "audience",
    title: "25-35 岁普通程序员",
    description: "评论区高频问题集中在年龄、转管理、AI 替代和收入稳定性。",
    source: "douyin_fans_summary + comment_keywords",
    score: 86,
    metrics: ["核心受众匹配", "焦虑问题高频"],
    action: "开头先承认焦虑，主体必须给出第一步判断标准。"
  },
  {
    id: "ev_memory_1",
    type: "memory",
    title: "先承认焦虑，再给可执行步骤",
    description: "来源于 9 条高收藏内容，适合抖音与小红书双平台改写。",
    source: "creator_pattern_vectors",
    score: 82,
    metrics: ["9 条样本", "收藏稳定"],
    action: "结构建议：共情一句 -> 反转判断 -> 三个动作。"
  },
  {
    id: "ev_constraint_1",
    type: "constraint",
    title: "生成约束",
    description: "语气要求克制直接，避免裁员恐慌，目标时长 60 秒。",
    source: "TopicIdeaGenerateRequest.constraints",
    metrics: ["tone: 克制直接", "avoid: 裁员恐慌", "duration: 60 秒"],
    action: "风险提示会优先拦截夸张焦虑和泛泛鸡汤表达。"
  }
];

export const tasks: AgentTask[] = [
  { id: "task_topic_001", name: "AI 选题生成", status: "running", progress: 68, currentStep: "Analyze Performance Pattern", traceId: "tr_9a23_topic" },
  { id: "task_etl_001", name: "抖音历史 ETL", status: "succeeded", progress: 100, currentStep: "Completed", traceId: "tr_7b11_etl" },
  { id: "task_memory_001", name: "Milvus 向量化", status: "pending", progress: 12, currentStep: "Waiting for Worker", traceId: "tr_5d10_vec" }
];

export const memories: MemoryPattern[] = [
  { id: "mem_success_1", type: "success", summary: "职场焦虑类内容必须在 15 秒内给出第一个解决动作。", confidence: 0.82, sourceCount: 14, lastVerifiedAt: "2026-05-09" },
  { id: "mem_seo_1", type: "seo", summary: "“不是 X，而是 Y”标题结构在程序员转型内容中收藏率更高。", confidence: 0.76, sourceCount: 9, lastVerifiedAt: "2026-05-08" },
  { id: "mem_failure_1", type: "failure", summary: "纯工具清单如果没有真实场景，评论多但完播偏低。", confidence: 0.69, sourceCount: 6, lastVerifiedAt: "2026-05-06" }
];

export const plans: PublishPlan[] = [
  { id: "plan_1", title: "AI 时代程序员机会", platform: "douyin", scheduledAt: "今天 18:30", stage: "idea" },
  { id: "plan_2", title: "35 岁岗位切换", platform: "xiaohongshu", scheduledAt: "明天 11:00", stage: "script" },
  { id: "plan_3", title: "面试项目难点", platform: "wechat", scheduledAt: "5 月 12 日", stage: "editing" },
  { id: "plan_4", title: "转码前算三笔账", platform: "youtube", scheduledAt: "5 月 14 日", stage: "ready" }
];

const roleShiftInitialBlocks = [
  createScriptBlock("hook", {
    id: "sb_role_shift_1_hook",
    voiceover: "如果你也在担心这个问题，先别急着否定自己。",
    visualHint: "正面半身，第一句直接看镜头，字幕突出“别急着否定自己”。",
    durationSeconds: 8
  }),
  createScriptBlock("point", {
    id: "sb_role_shift_1_point",
    voiceover: "真正的问题不是年龄或工具，而是你还停留在只执行需求的岗位形态里。",
    visualHint: "屏幕打出“年龄/工具”与“岗位形态”的对比。",
    durationSeconds: 18
  }),
  createScriptBlock("turn", {
    id: "sb_role_shift_1_turn",
    voiceover: "普通人要做的是把经验变成可迁移能力。",
    visualHint: "语速放慢，用一条粗体字幕承接反转。",
    durationSeconds: 14
  }),
  createScriptBlock("cta", {
    id: "sb_role_shift_1_cta",
    voiceover: "如果你想看具体路线，我下一条拆给你。",
    visualHint: "收尾看镜头，给出下一条内容承诺。",
    durationSeconds: 10
  })
];

const roleShiftDouyinBlocks = [
  createScriptBlock("hook", {
    id: "sb_role_shift_2_hook",
    voiceover: "如果你担心 35 岁以后写不动代码，先别急着否定自己。",
    visualHint: "开场 3 秒保持正面半身，屏幕左侧放“35 岁以后？”",
    durationSeconds: 8
  }),
  createScriptBlock("point", {
    id: "sb_role_shift_2_point",
    voiceover: "真正的问题不是年龄，而是你还停留在“只接需求”的岗位形态里。35 岁以后，企业更需要的是能拆问题、控风险、带人交付的人。",
    visualHint: "用三段字幕依次打出：拆问题、控风险、带人交付。",
    durationSeconds: 26
  }),
  createScriptBlock("turn", {
    id: "sb_role_shift_2_turn",
    voiceover: "所以这不是退出信号，而是岗位切换信号。",
    visualHint: "切近景，强调“不是退出，是切换”。",
    durationSeconds: 10
  }),
  createScriptBlock("cta", {
    id: "sb_role_shift_2_cta",
    voiceover: "如果你想知道怎么从执行型程序员转到方案型角色，我下一条讲具体路径。",
    visualHint: "结尾字幕保留“执行型 -> 方案型”。",
    durationSeconds: 14
  })
];

const roleShiftVersions: ScriptDraft["versions"] = [
  {
    id: "sv_role_shift_1",
    draftId: "scr_role_shift",
    versionNo: 1,
    label: "v1 AI 初稿",
    platform: "douyin",
    durationSeconds: 60,
    body: composeScriptBody(roleShiftInitialBlocks),
    blocks: roleShiftInitialBlocks,
    description: "一个普通程序员视角，聊聊 35 岁焦虑背后的职业选择。",
    tags: ["#程序员", "#职业规划", "#35岁危机"],
    titleCandidates: [{ text: "35 岁程序员不是危机，是岗位切换信号", score: 88 }],
    sourceType: "ai_initial",
    status: "candidate",
    generationId: "gen_mock_script",
    createdAt: "2026-05-12T10:30:00"
  },
  {
    id: "sv_role_shift_2",
    draftId: "scr_role_shift",
    versionNo: 2,
    label: "v2 抖音版",
    platform: "douyin",
    durationSeconds: 58,
    body: composeScriptBody(roleShiftDouyinBlocks),
    blocks: roleShiftDouyinBlocks,
    description: "强化开头钩子和岗位切换表达。",
    tags: ["#程序员", "#职业规划", "#AI时代"],
    titleCandidates: [{ text: "35 岁程序员不是危机，是岗位切换信号", score: 91 }],
    sourceType: "user_save",
    parentVersionId: "sv_role_shift_1",
    status: "candidate",
    createdAt: "2026-05-12T10:42:00"
  }
];

export const scriptDrafts: ScriptDraft[] = [
  {
    id: "scr_role_shift",
    workspaceId: "ws_northstar",
    topicIdeaId: "tp_role_shift",
    title: "35 岁程序员不是危机，是岗位切换信号",
    body: composeScriptBody(roleShiftDouyinBlocks),
    platform: "douyin",
    status: "draft",
    currentVersionId: "sv_role_shift_2",
    adoptedVersionId: undefined,
    updatedAt: "2026-05-12T10:42:00",
    currentVersion: roleShiftVersions[1],
    versions: roleShiftVersions
  }
];
