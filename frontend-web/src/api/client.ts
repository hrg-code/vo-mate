import { collectorImportResponse, contents, dashboardMetrics, evidence, memories, plans, scriptDrafts, tasks, topicIdeas, workspace } from "./mockData";
import { composeScriptBody, createScriptBlocksFromBody, createTemplateScriptBlocks } from "../features/scripts/scriptBlocks";
import type {
  AgentTask,
  ContentItem,
  CollectorImportRequest,
  CollectorImportResponse,
  EvidenceItem,
  EvidenceQuery,
  MemoryPattern,
  MetricSummary,
  PublishPlan,
  ScriptCopilotAction,
  ScriptCopilotContext,
  ScriptCopilotEvidenceRef,
  ScriptCopilotSuggestion,
  ScriptDraft,
  ScriptDraftCreateRequest,
  ScriptDraftVersionCreateRequest,
  ScriptQualityReport,
  ScriptSeoPackage,
  ScriptVersionStatus,
  TopicIdeaGenerateRequest,
  TopicIdeaStreamEvent,
  TopicIdea,
  WorkspaceContext
} from "../types";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "/api/v1";
const USE_MOCKS = import.meta.env.VITE_USE_MOCKS === "true";
let mockScriptDrafts: ScriptDraft[] = scriptDrafts.map((draft) => ({ ...draft, versions: draft.versions.map((version) => ({ ...version })) }));

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...init?.headers
    }
  });

  if (!response.ok) {
    throw new Error(`API ${response.status}: ${await response.text()}`);
  }

  return response.json() as Promise<T>;
}

function parseSseChunk(chunk: string): TopicIdeaStreamEvent[] {
  return chunk
    .split("\n\n")
    .filter(Boolean)
    .map((rawEvent) => {
      const event = rawEvent
        .split("\n")
        .find((line) => line.startsWith("event: "))
        ?.slice("event: ".length);
      const data = rawEvent
        .split("\n")
        .find((line) => line.startsWith("data: "))
        ?.slice("data: ".length);
      return { event, data: data ? JSON.parse(data) : {} } as TopicIdeaStreamEvent;
    });
}

function queryString(params: Record<string, string | number | undefined>): string {
  const searchParams = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== "") searchParams.set(key, String(value));
  });
  const value = searchParams.toString();
  return value ? `?${value}` : "";
}

export const api = {
  getWorkspace: (): Promise<WorkspaceContext> =>
    USE_MOCKS ? Promise.resolve(workspace) : request<WorkspaceContext>("/workspaces/current"),
  getDashboard: () =>
    USE_MOCKS
      ? Promise.resolve({ metrics: dashboardMetrics, contents: contents.slice(0, 3), tasks })
      : request<{ metrics: MetricSummary[]; contents: ContentItem[]; tasks: AgentTask[] }>("/analytics/dashboard"),
  getContents: (): Promise<ContentItem[]> => (USE_MOCKS ? Promise.resolve(contents) : request<ContentItem[]>("/contents")),
  importContents: (payload: CollectorImportRequest): Promise<CollectorImportResponse> =>
    USE_MOCKS
      ? Promise.resolve({ ...collectorImportResponse, taskId: `task_raw-import_${Date.now()}` })
      : request<CollectorImportResponse>("/collector/import", { method: "POST", body: JSON.stringify(payload) }),
  getTopicIdeas: (): Promise<TopicIdea[]> =>
    USE_MOCKS ? Promise.resolve(topicIdeas) : request<TopicIdea[]>("/ai/topic-ideas"),
  streamTopicIdeas: async (payload: TopicIdeaGenerateRequest, onEvent: (event: TopicIdeaStreamEvent) => void): Promise<void> => {
    if (USE_MOCKS) {
      onEvent({ event: "start", data: { workflow: "topic-ideas", generationId: "gen_mock" } });
      onEvent({ event: "progress", data: { step: "generate_candidates", message: "mock 模式已生成选题候选。" } });
      onEvent({
        event: "evidence",
        data: {
          items: evidence.map((item) => ({
            id: item.id,
            type: item.type,
            title: item.title,
            summary: item.description,
            memoryType: item.type,
            score: item.score,
            reason: item.source,
            metrics: item.metrics,
            action: item.action
          }))
        }
      });
      topicIdeas.forEach((idea) => onEvent({ event: "topic_idea", data: idea }));
      onEvent({ event: "done", data: { generationId: "gen_mock", count: topicIdeas.length, topicIdeas } });
      return;
    }

    const response = await fetch(`${API_BASE_URL}/ai/topic-ideas`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    if (!response.ok || !response.body) {
      throw new Error(`API ${response.status}: ${await response.text()}`);
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const boundary = buffer.lastIndexOf("\n\n");
      if (boundary === -1) continue;
      const ready = buffer.slice(0, boundary + 2);
      buffer = buffer.slice(boundary + 2);
      parseSseChunk(ready).forEach(onEvent);
    }
    if (buffer.trim()) {
      parseSseChunk(buffer).forEach(onEvent);
    }
  },
  getEvidence: (query: EvidenceQuery = {}): Promise<EvidenceItem[]> =>
    request<EvidenceItem[]>(
      `/ai/evidence${queryString({
        generationId: query.generationId,
        workspaceId: query.workspaceId,
        accountId: query.accountId,
        platform: query.platform,
        direction: query.direction,
        limit: query.limit
      })}`
    ),
  getTasks: (): Promise<AgentTask[]> => (USE_MOCKS ? Promise.resolve(tasks) : request<AgentTask[]>("/workflows/tasks")),
  getMemories: (): Promise<MemoryPattern[]> =>
    USE_MOCKS ? Promise.resolve(memories) : request<MemoryPattern[]>("/memory/patterns"),
  getPublishPlans: (): Promise<PublishPlan[]> =>
    USE_MOCKS ? Promise.resolve(plans) : request<PublishPlan[]>("/workflows/publish-plans"),
  getScriptDrafts: (): Promise<ScriptDraft[]> =>
    USE_MOCKS ? Promise.resolve(mockScriptDrafts.map(withCurrentVersion)) : request<ScriptDraft[]>("/scripts"),
  getScriptDraft: (draftId: string): Promise<ScriptDraft> => {
    if (!USE_MOCKS) return request<ScriptDraft>(`/scripts/${draftId}`);
    const draft = mockScriptDrafts.find((item) => item.id === draftId);
    if (!draft) return Promise.reject(new Error("Script draft not found"));
    return Promise.resolve(withCurrentVersion(draft));
  },
  createScriptDraft: (payload: ScriptDraftCreateRequest): Promise<ScriptDraft> => {
    if (!USE_MOCKS) return request<ScriptDraft>("/scripts", { method: "POST", body: JSON.stringify(payload) });
    const draftId = `scr_mock_${Date.now()}`;
    const versionId = `sv_mock_${Date.now()}`;
    const blocks = createTemplateScriptBlocks(payload.topic, payload.durationSeconds ?? 60);
    const body = composeScriptBody(blocks);
    const version = {
      id: versionId,
      draftId,
      versionNo: 1,
      label: "v1 AI 初稿",
      platform: payload.platform ?? "douyin",
      durationSeconds: payload.durationSeconds ?? 60,
      body,
      blocks,
      description: `围绕“${payload.topic}”生成的一版口播脚本。`,
      tags: ["#程序员", "#职业成长"],
      titleCandidates: [{ text: payload.title ?? payload.topic, score: 88 }],
      sourceType: "ai_initial" as const,
      generationId: `gen_mock_${Date.now()}`,
      status: "candidate" as const,
      createdAt: new Date().toISOString()
    };
    const draft: ScriptDraft = {
      id: draftId,
      workspaceId: payload.workspaceId ?? "ws_northstar",
      topicIdeaId: payload.topicIdeaId,
      title: payload.title ?? payload.topic,
      body,
      platform: payload.platform ?? "douyin",
      status: "draft",
      currentVersionId: versionId,
      versions: [version],
      currentVersion: version,
      updatedAt: new Date().toISOString()
    };
    mockScriptDrafts = [draft, ...mockScriptDrafts];
    return Promise.resolve(withCurrentVersion(draft));
  },
  createScriptVersion: (draftId: string, payload: ScriptDraftVersionCreateRequest): Promise<ScriptDraft> => {
    if (!USE_MOCKS) {
      const { blocks: _blocks, ...requestPayload } = payload;
      return request<ScriptDraft>(`/scripts/${draftId}/versions`, { method: "POST", body: JSON.stringify(requestPayload) });
    }
    const draft = mockScriptDrafts.find((item) => item.id === draftId);
    if (!draft) return Promise.reject(new Error("Script draft not found"));
    const versionNo = Math.max(...draft.versions.map((version) => version.versionNo), 0) + 1;
    const blocks = payload.blocks ?? createScriptBlocksFromBody(payload.body, payload.durationSeconds);
    const version = {
      id: `sv_mock_${Date.now()}`,
      draftId,
      versionNo,
      label: payload.label ?? `v${versionNo} 用户修改`,
      platform: payload.platform ?? draft.platform,
      durationSeconds: payload.durationSeconds,
      body: payload.body,
      blocks,
      description: payload.description,
      tags: payload.tags ?? [],
      titleCandidates: payload.titleCandidates ?? [],
      sourceType: payload.sourceType ?? "user_save",
      parentVersionId: payload.parentVersionId ?? draft.currentVersionId,
      status: "candidate" as const,
      createdAt: new Date().toISOString()
    };
    draft.versions = [...draft.versions, version];
    draft.currentVersionId = version.id;
    draft.currentVersion = version;
    draft.body = payload.body;
    draft.platform = version.platform;
    draft.updatedAt = new Date().toISOString();
    return Promise.resolve(withCurrentVersion(draft));
  },
  updateScriptVersionStatus: (draftId: string, versionId: string, status: ScriptVersionStatus): Promise<ScriptDraft> => {
    if (!USE_MOCKS) {
      return request<ScriptDraft>(`/scripts/${draftId}/versions/${versionId}/status`, {
        method: "PATCH",
        body: JSON.stringify({ status })
      });
    }
    const draft = mockScriptDrafts.find((item) => item.id === draftId);
    const version = draft?.versions.find((item) => item.id === versionId);
    if (!draft || !version) return Promise.reject(new Error("Script draft version not found"));
    version.status = status;
    if (status === "adopted") draft.adoptedVersionId = versionId;
    draft.updatedAt = new Date().toISOString();
    return Promise.resolve(withCurrentVersion(draft));
  },
  updateScriptCurrentVersion: (draftId: string, versionId: string): Promise<ScriptDraft> => {
    if (!USE_MOCKS) {
      return request<ScriptDraft>(`/scripts/${draftId}/current-version`, {
        method: "PATCH",
        body: JSON.stringify({ versionId })
      });
    }
    const draft = mockScriptDrafts.find((item) => item.id === draftId);
    const version = draft?.versions.find((item) => item.id === versionId);
    if (!draft || !version) return Promise.reject(new Error("Script draft version not found"));
    draft.currentVersionId = versionId;
    draft.currentVersion = version;
    draft.body = version.body;
    draft.platform = version.platform;
    draft.updatedAt = new Date().toISOString();
    return Promise.resolve(withCurrentVersion(draft));
  },
  getScriptCopilotContext: async (draftId: string, versionId: string): Promise<ScriptCopilotContext> => {
    if (USE_MOCKS) return createMockCopilotContext(draftId, versionId);
    try {
      return await request<ScriptCopilotContext>(`/scripts/${draftId}/versions/${versionId}/copilot/context`);
    } catch (error) {
      if (shouldUseCopilotFallback(error)) return createMockCopilotContext(draftId, versionId);
      throw error;
    }
  },
  runScriptCopilotAction: (
    draftId: string,
    versionId: string,
    actionId: ScriptCopilotAction["id"],
    body: string
  ): Promise<ScriptCopilotSuggestion> => {
    if (USE_MOCKS) return Promise.resolve(createMockCopilotSuggestion(draftId, versionId, actionId, body));
    return request<ScriptCopilotSuggestion>(`/scripts/${draftId}/versions/${versionId}/copilot/actions`, {
          method: "POST",
          body: JSON.stringify({ actionId, body })
        }).catch((error) => {
          if (shouldUseCopilotFallback(error)) return createMockCopilotSuggestion(draftId, versionId, actionId, body);
          throw error;
        });
  },
  getScriptQualityReport: async (draftId: string, versionId: string, body: string): Promise<ScriptQualityReport> => {
    if (USE_MOCKS) return createMockQualityReport(draftId, versionId, body);
    try {
      return await request<ScriptQualityReport>(`/scripts/${draftId}/versions/${versionId}/copilot/quality`, {
          method: "POST",
          body: JSON.stringify({ body })
        });
    } catch (error) {
      if (shouldUseCopilotFallback(error)) return createMockQualityReport(draftId, versionId, body);
      throw error;
    }
  },
  getScriptSeoPackage: async (draftId: string, versionId: string, body: string): Promise<ScriptSeoPackage> => {
    if (USE_MOCKS) return createMockSeoPackage(draftId, versionId, body);
    try {
      return await request<ScriptSeoPackage>(`/scripts/${draftId}/versions/${versionId}/copilot/seo`, {
          method: "POST",
          body: JSON.stringify({ body })
        });
    } catch (error) {
      if (shouldUseCopilotFallback(error)) return createMockSeoPackage(draftId, versionId, body);
      throw error;
    }
  },
  createAiTask: (workflow: string, payload: unknown) =>
    USE_MOCKS
      ? Promise.resolve({ taskId: `task_${workflow}_${Date.now()}`, status: "pending" })
      : request(`/ai/${workflow}`, { method: "POST", body: JSON.stringify(payload) })
};

function withCurrentVersion(draft: ScriptDraft): ScriptDraft {
  const currentVersion = draft.versions.find((version) => version.id === draft.currentVersionId) ?? draft.versions[0];
  return {
    ...draft,
    currentVersion: currentVersion ? cloneScriptVersion(currentVersion) : currentVersion,
    versions: draft.versions.map(cloneScriptVersion)
  };
}

function cloneScriptVersion<T extends ScriptDraft["versions"][number]>(version: T): T {
  return { ...version, blocks: version.blocks?.map((block) => ({ ...block })) };
}

function shouldUseCopilotFallback(error: unknown) {
  if (!(error instanceof Error)) return false;
  return error.message.startsWith("API 404:") || error.message.startsWith("API 405:");
}

const copilotActions: ScriptCopilotAction[] = [
  {
    id: "strengthen_hook",
    name: "强化开头",
    description: "把前 3 秒改成更明确的冲突判断。",
    targetPlatform: "douyin",
    outputType: "rewrite"
  },
  {
    id: "compress_45",
    name: "压缩到 45 秒",
    description: "保留核心观点，删掉重复铺垫。",
    targetPlatform: "douyin",
    outputType: "rewrite"
  },
  {
    id: "generate_30",
    name: "生成 30 秒版",
    description: "改成短视频快节奏口播版本。",
    targetPlatform: "douyin",
    outputType: "rewrite"
  },
  {
    id: "add_case",
    name: "加真实案例",
    description: "补一个贴近历史内容的人设案例。",
    outputType: "rewrite"
  },
  {
    id: "adapt_xiaohongshu",
    name: "转小红书口吻",
    description: "改成更适合收藏和搜索的经验清单。",
    targetPlatform: "xiaohongshu",
    outputType: "platform_adaptation"
  },
  {
    id: "teleprompter",
    name: "拍摄提词版",
    description: "拆短句，减少书面表达，方便照读。",
    outputType: "teleprompter"
  }
];

function createMockCopilotContext(draftId: string, versionId: string): ScriptCopilotContext {
  const draft = mockScriptDrafts.find((item) => item.id === draftId);
  const version = draft?.versions.find((item) => item.id === versionId);
  return {
    actions: copilotActions,
    evidence: createEvidenceRefs(),
    confidence: 0.84,
    platform: version?.platform ?? draft?.platform ?? "douyin"
  };
}

function createMockCopilotSuggestion(
  _draftId: string,
  versionId: string,
  actionId: ScriptCopilotAction["id"],
  body: string
): ScriptCopilotSuggestion {
  const safeBody = body.trim() || "开头：先给出一个明确判断。\n主体：说明问题和解决动作。\n结尾：引导用户评论。";
  const action = [...copilotActions, ...qualityFixActions].find((item) => item.id === actionId);
  const rewritten = rewriteScriptByAction(actionId, safeBody);
  return {
    id: `sg_${actionId}_${Date.now()}`,
    actionId,
    title: action?.name ?? "AI 改写建议",
    body: rewritten,
    changeSummary: createChangeSummary(actionId),
    confidence: actionId === "adapt_xiaohongshu" ? 0.79 : 0.86,
    evidenceRefs: createEvidenceRefs(),
    riskNote: actionId === "fix_risk" ? "已降低绝对化表达，但仍建议人工检查平台敏感词。" : "建议人工保留最符合本人表达习惯的句子。",
    targetPlatform: actionId === "adapt_xiaohongshu" ? "xiaohongshu" : undefined
  };
}

function createMockQualityReport(_draftId: string, _versionId: string, body: string): ScriptQualityReport {
  const compactLength = body.replace(/\s/g, "").length;
  const hasConflict = /不是|而是|危机|淘汰|信号|先别/.test(body);
  const hasSeo = /程序员|AI|35|转型|岗位/.test(body);
  const hasCta = /评论|关注|下一条|收藏|留言/.test(body);
  const durationScore = compactLength > 280 ? 72 : compactLength < 90 ? 68 : 86;
  const hookScore = hasConflict ? 84 : 62;
  const seoScore = hasSeo ? 86 : 65;
  const conversionScore = hasCta ? 82 : 66;
  const metrics = {
    persona: 88,
    hook: hookScore,
    retention: compactLength > 220 ? 74 : 82,
    seo: seoScore,
    oral: /。/.test(body) && compactLength < 260 ? 84 : 76,
    risk: /一定|绝对|废了|没救/.test(body) ? 58 : 88,
    conversion: conversionScore,
    duration: durationScore
  };
  const mustFix = [
    ...(hookScore < 75 ? [{ id: "qf_hook", actionId: "fix_hook" as const, title: "开头冲突不够明确", description: "前 3 秒需要更快说出问题或反常识判断。" }] : []),
    ...(seoScore < 75 ? [{ id: "qf_seo", actionId: "fix_seo" as const, title: "关键词进入太晚", description: "把核心关键词提前到标题和前 10 秒。" }] : []),
    ...(metrics.risk < 75 ? [{ id: "qf_risk", actionId: "fix_risk" as const, title: "风险表达偏强", description: "减少绝对化和攻击性表述。" }] : [])
  ];
  const niceToHave = [
    { id: "qf_cta", actionId: "fix_cta" as const, title: "结尾互动可更自然", description: "把模板化关注引导改成下一条内容承诺。" },
    { id: "qf_case", actionId: "add_case" as const, title: "可以补一个真实案例", description: "用账号经历增强可信度。" }
  ];
  const total = Object.values(metrics).reduce((sum, score) => sum + score, 0);
  return {
    overallScore: Math.round(total / Object.keys(metrics).length),
    metrics,
    mustFix,
    niceToHave,
    summary: mustFix.length ? "当前脚本可用，但建议先修开头、关键词或风险表达。" : "当前版本结构完整，可以继续做标题和平台适配。"
  };
}

function createMockSeoPackage(_draftId: string, _versionId: string, body: string): ScriptSeoPackage {
  const baseTopic = body.includes("AI") ? "AI 时代程序员" : "35 岁程序员";
  return {
    titleCandidates: [
      { text: `${baseTopic}最该换的不是行业，而是岗位形态`, score: 92, reason: "覆盖人群、冲突和解决方向。" },
      { text: "程序员 35 岁危机，其实是一个岗位切换信号", score: 88, reason: "搜索词明确，适合抖音强钩子。" },
      { text: "普通程序员过了 35 岁，真正要补的是这项能力", score: 83, reason: "悬念更强，但关键词覆盖略弱。" }
    ],
    descriptionCandidates: [
      { text: "这条视频聊普通程序员 35 岁后的岗位切换：从只接需求，到能拆问题、控风险、交付方案。", score: 90, reason: "适合平台搜索和 AI 摘要引用。" },
      { text: "年龄不是退出信号，岗位形态才是关键。用 60 秒拆清程序员下一步该怎么转。", score: 84, reason: "更适合短视频简介。" }
    ],
    tagCandidates: ["#程序员", "#35岁危机", "#职业规划", "#AI时代", "#岗位转型"],
    keywordCoverage: [
      { keyword: "程序员", coveredInTitle: true, coveredInOpening: body.includes("程序员"), coveredInTags: true },
      { keyword: "35 岁", coveredInTitle: true, coveredInOpening: body.includes("35"), coveredInTags: true },
      { keyword: "岗位转型", coveredInTitle: false, coveredInOpening: body.includes("岗位"), coveredInTags: true },
      { keyword: "AI 时代", coveredInTitle: body.includes("AI"), coveredInOpening: body.includes("AI"), coveredInTags: true }
    ]
  };
}

const qualityFixActions: ScriptCopilotAction[] = [
  { id: "fix_hook", name: "修复开头", description: "补充前 3 秒冲突。", outputType: "quality_fix" },
  { id: "fix_seo", name: "修复关键词", description: "提前核心搜索词。", outputType: "quality_fix" },
  { id: "fix_risk", name: "风险降噪", description: "降低绝对化表达。", outputType: "quality_fix" },
  { id: "fix_cta", name: "优化互动", description: "改成自然 CTA。", outputType: "quality_fix" }
];

function createEvidenceRefs(): ScriptCopilotEvidenceRef[] {
  return [
    ...evidence.slice(0, 3).map((item) => ({ id: item.id, title: item.title, type: item.type, score: item.score })),
    ...memories.slice(0, 2).map((item) => ({ id: item.id, title: item.summary, type: item.type, score: Math.round(item.confidence * 100) }))
  ];
}

function rewriteScriptByAction(actionId: ScriptCopilotAction["id"], body: string) {
  const normalized = body.trim();
  switch (actionId) {
    case "strengthen_hook":
    case "fix_hook":
      return `开头 3 秒：\n很多程序员不是被年龄淘汰，而是先被自己的岗位形态卡住。\n\n${stripOpening(normalized)}`;
    case "compress_45":
      return `开头：35 岁不是退出信号，是岗位切换信号。\n\n主体：如果你还只是在接需求、写功能，风险会越来越高。下一步要补的是拆问题、控风险、交付方案的能力。\n\n结尾：想看具体怎么转，我下一条直接拆路径。`;
    case "generate_30":
      return `35 岁程序员最该换的不是行业，而是岗位形态。\n\n只会接需求，年龄越大越被动；能拆问题、控风险、交付方案，经验才会变成优势。\n\n评论区打“路径”，我下一条讲具体怎么转。`;
    case "add_case":
      return `${normalized}\n\n真实案例：我见过一个做了十几年业务系统的同事，后来不是靠追新框架翻身，而是把自己最熟的订单、库存、财务流程拆成方案能力，反而更容易拿到关键项目。`;
    case "adapt_xiaohongshu":
      return `标题：35 岁程序员别急着转行，先看这 3 个岗位信号\n\n1. 如果你还只是在接需求，风险确实会变高。\n2. 如果你能拆问题、控风险、推动交付，年龄反而会变成经验资产。\n3. 真正要切换的不是行业，而是从执行型角色变成方案型角色。\n\n适合收藏的判断：先看自己有没有“业务理解 + 方案交付 + 沟通推进”这三件事。`;
    case "teleprompter":
      return normalized
        .replace(/[。！？]/g, "\n")
        .split("\n")
        .map((line) => line.trim())
        .filter(Boolean)
        .join("\n\n");
    case "fix_seo":
      return normalized.replace("开头 3 秒：", "开头 3 秒：\n程序员、35 岁、AI 时代，这三个词放在一起，真正的问题不是年龄。");
    case "fix_risk":
      return normalized.replace(/一定|绝对/g, "更可能").replace(/废了|没救/g, "会比较被动");
    case "fix_cta":
      return `${normalized}\n\n结尾互动：如果你也在做岗位切换，评论区留一个“路径”，我下一条把执行型到方案型的 3 步拆清楚。`;
    default:
      return normalized;
  }
}

function stripOpening(body: string) {
  return body.replace(/^开头\s*\d*\s*秒：[\s\S]*?(?=\n\n|主体：|转折：)/, "").trim();
}

function createChangeSummary(actionId: ScriptCopilotAction["id"]) {
  const summaries: Record<ScriptCopilotAction["id"], string> = {
    strengthen_hook: "重写前 3 秒，让冲突和核心判断更早出现。",
    compress_45: "压缩铺垫，保留观点、原因和下一步承诺。",
    generate_30: "生成更短的高密度口播版本。",
    add_case: "追加一个贴合账号经历的案例段落。",
    adapt_xiaohongshu: "改成小红书清单表达，强化收藏价值。",
    teleprompter: "拆分短句，方便拍摄时照读。",
    fix_hook: "补强开头冲突。",
    fix_seo: "提前核心关键词。",
    fix_risk: "降低绝对化和攻击性表达。",
    fix_cta: "把模板互动改成下一条内容承诺。"
  };
  return summaries[actionId];
}
