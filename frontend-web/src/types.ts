export type Platform = "douyin" | "kuaishou" | "xiaohongshu" | "youtube" | "wechat";

export type TaskStatus = "pending" | "running" | "requires_action" | "succeeded" | "failed" | "cancelled";

export type ContentStatus = "published" | "needs_review" | "script_reusable" | "seo_opportunity";

export type ScriptVersionSourceType = "ai_initial" | "user_save" | "ai_rewrite" | "platform_adaptation";

export type ScriptVersionStatus = "candidate" | "adopted" | "discarded";

export type ScriptBlockRole = "hook" | "pain" | "point" | "proof" | "method" | "turn" | "summary" | "cta";

export type ScriptBlock = {
  id: string;
  role: ScriptBlockRole;
  label: string;
  voiceover: string;
  visualHint?: string;
  startSeconds?: number;
  endSeconds?: number;
  durationSeconds?: number;
};

export type RouteId =
  | "dashboard"
  | "contents"
  | "audience"
  | "topics"
  | "scripts"
  | "seo"
  | "calendar"
  | "retrospectives"
  | "memory"
  | "collector"
  | "settings";

export type WorkspaceContext = {
  workspaceId: string;
  workspaceName: string;
  accountName: string;
  platformScope: Platform[];
};

export type MetricSummary = {
  label: string;
  value: string;
  delta: string;
  direction: "up" | "down" | "flat";
  description: string;
};

export type ContentItem = {
  id: string;
  title: string;
  platform: Platform;
  publishedAt: string;
  durationSeconds: number;
  views: number;
  likes: number;
  comments: number;
  saves: number;
  shares: number;
  completionRate: number;
  followersGained: number;
  score: number;
  status: ContentStatus;
  hasAsr: boolean;
  reviewed: boolean;
};

export type CollectorImportRequest = {
  workspaceId: string;
  platform: Platform;
  collection: string;
  asrCollection: string;
  includeAsr: boolean;
  limit: number;
};

export type CollectorImportResponse = {
  taskId: string;
  status: string;
  processedCount: number;
  upsertedCount: number;
  failedCount: number;
  textAssetCount: number;
  tagCount: number;
  keywordCount: number;
  trafficSourceCount: number;
  asrCount: number;
};

export type TopicIdea = {
  id: string;
  title: string;
  topic?: string;
  angle: string;
  category?: string;
  targetAudience?: string;
  predictedScore: number;
  seoScore: number;
  audienceScore: number;
  difficultyScore: number;
  risk: string;
  recommendReason?: string;
  evidenceCount: number;
  targetPlatforms: Platform[];
  evidence?: Record<string, unknown>[];
  suggestedTitles?: string[];
  suggestedHooks?: string[];
  suggestedTags?: string[];
  nextActions?: string[];
  generationId?: string;
};

export type TopicIdeaGenerateRequest = {
  workspaceId?: string;
  accountIds?: string[];
  direction: string;
  platforms?: Platform[];
  goal?: string;
  count?: number;
  audience?: string;
  constraints?: Record<string, unknown>;
  includeEvidence?: boolean;
};

export type TopicIdeaStreamEvent =
  | { event: "start"; data: Record<string, unknown> }
  | { event: "progress"; data: { step: string; message: string } }
  | { event: "evidence"; data: { items: Record<string, unknown>[] } }
  | { event: "topic_idea"; data: TopicIdea }
  | { event: "done"; data: { generationId: string; count: number; topicIdeas: TopicIdea[] } }
  | { event: "error"; data: { generationId?: string; code: string; message: string } };

export type EvidenceItem = {
  id: string;
  type: "content" | "keyword" | "audience" | "memory" | "metric" | "constraint" | "raw";
  title: string;
  description: string;
  source: string;
  score?: number;
  metrics?: string[];
  action?: string;
};

export type EvidenceQuery = {
  generationId?: string;
  workspaceId?: string;
  accountId?: string;
  platform?: Platform;
  direction?: string;
  limit?: number;
};

export type AgentTask = {
  id: string;
  name: string;
  status: TaskStatus;
  progress: number;
  currentStep: string;
  traceId: string;
};

export type ScriptDraftVersion = {
  id: string;
  draftId: string;
  versionNo: number;
  label: string;
  platform?: Platform;
  durationSeconds?: number;
  body: string;
  blocks?: ScriptBlock[];
  description?: string;
  tags: string[];
  titleCandidates: Record<string, unknown>[];
  sourceType: ScriptVersionSourceType;
  parentVersionId?: string;
  generationId?: string;
  status: ScriptVersionStatus;
  createdAt?: string;
};

export type ScriptDraft = {
  id: string;
  workspaceId: string;
  topicIdeaId?: string;
  title: string;
  body?: string;
  platform?: Platform;
  status: string;
  currentVersionId?: string;
  adoptedVersionId?: string;
  currentVersion?: ScriptDraftVersion;
  versions: ScriptDraftVersion[];
  updatedAt?: string;
};

export type ScriptDraftCreateRequest = {
  workspaceId?: string;
  topicIdeaId?: string;
  topic: string;
  title?: string;
  platform?: Platform;
  durationSeconds?: number;
};

export type ScriptDraftVersionCreateRequest = {
  body: string;
  blocks?: ScriptBlock[];
  label?: string;
  platform?: Platform;
  durationSeconds?: number;
  description?: string;
  tags?: string[];
  titleCandidates?: Record<string, unknown>[];
  sourceType?: ScriptVersionSourceType;
  parentVersionId?: string;
};

export type ScriptCopilotAction = {
  id:
    | "strengthen_hook"
    | "compress_45"
    | "generate_30"
    | "add_case"
    | "adapt_xiaohongshu"
    | "teleprompter"
    | "fix_hook"
    | "fix_seo"
    | "fix_risk"
    | "fix_cta";
  name: string;
  description: string;
  targetPlatform?: Platform;
  outputType: "rewrite" | "platform_adaptation" | "teleprompter" | "quality_fix";
};

export type ScriptCopilotEvidenceRef = {
  id: string;
  title: string;
  type: EvidenceItem["type"] | MemoryPattern["type"];
  score?: number;
};

export type ScriptCopilotSuggestion = {
  id: string;
  actionId: ScriptCopilotAction["id"];
  title: string;
  body: string;
  changeSummary: string;
  confidence: number;
  evidenceRefs: ScriptCopilotEvidenceRef[];
  riskNote?: string;
  targetPlatform?: Platform;
};

export type ScriptQualityMetricKey =
  | "persona"
  | "hook"
  | "retention"
  | "seo"
  | "oral"
  | "risk"
  | "conversion"
  | "duration";

export type ScriptQualityFix = {
  id: string;
  actionId: ScriptCopilotAction["id"];
  title: string;
  description: string;
};

export type ScriptQualityReport = {
  overallScore: number;
  metrics: Record<ScriptQualityMetricKey, number>;
  mustFix: ScriptQualityFix[];
  niceToHave: ScriptQualityFix[];
  summary: string;
};

export type ScriptSeoCandidate = {
  text: string;
  score: number;
  reason: string;
};

export type ScriptKeywordCoverage = {
  keyword: string;
  coveredInTitle: boolean;
  coveredInOpening: boolean;
  coveredInTags: boolean;
};

export type ScriptSeoPackage = {
  titleCandidates: ScriptSeoCandidate[];
  descriptionCandidates: ScriptSeoCandidate[];
  tagCandidates: string[];
  keywordCoverage: ScriptKeywordCoverage[];
};

export type ScriptCopilotContext = {
  actions: ScriptCopilotAction[];
  evidence: ScriptCopilotEvidenceRef[];
  confidence: number;
  platform: Platform;
};

export type MemoryPattern = {
  id: string;
  type: "success" | "failure" | "seo" | "hook" | "script" | "persona";
  summary: string;
  confidence: number;
  sourceCount: number;
  lastVerifiedAt: string;
};

export type PublishPlan = {
  id: string;
  title: string;
  platform: Platform;
  scheduledAt: string;
  stage: "idea" | "script" | "shooting" | "editing" | "ready" | "published";
};
