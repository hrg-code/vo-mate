export type Platform = "douyin" | "kuaishou" | "xiaohongshu" | "youtube" | "wechat";

export type TaskStatus = "pending" | "running" | "requires_action" | "succeeded" | "failed" | "cancelled";

export type ContentStatus = "published" | "needs_review" | "script_reusable" | "seo_opportunity";

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
  type: "content" | "keyword" | "audience" | "memory" | "metric" | "raw";
  title: string;
  description: string;
  source: string;
  score?: number;
};

export type AgentTask = {
  id: string;
  name: string;
  status: TaskStatus;
  progress: number;
  currentStep: string;
  traceId: string;
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
