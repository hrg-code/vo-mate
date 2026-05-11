import { contents, dashboardMetrics, evidence, memories, plans, tasks, topicIdeas, workspace } from "./mockData";
import type {
  AgentTask,
  ContentItem,
  EvidenceItem,
  MemoryPattern,
  MetricSummary,
  PublishPlan,
  TopicIdeaGenerateRequest,
  TopicIdeaStreamEvent,
  TopicIdea,
  WorkspaceContext
} from "../types";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "/api/v1";
const USE_MOCKS = import.meta.env.VITE_USE_MOCKS !== "false";

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

export const api = {
  getWorkspace: (): Promise<WorkspaceContext> =>
    USE_MOCKS ? Promise.resolve(workspace) : request<WorkspaceContext>("/workspaces/current"),
  getDashboard: () =>
    USE_MOCKS
      ? Promise.resolve({ metrics: dashboardMetrics, contents: contents.slice(0, 3), tasks })
      : request<{ metrics: MetricSummary[]; contents: ContentItem[]; tasks: AgentTask[] }>("/analytics/dashboard"),
  getContents: (): Promise<ContentItem[]> => (USE_MOCKS ? Promise.resolve(contents) : request<ContentItem[]>("/contents")),
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
            title: item.title,
            summary: item.description,
            memoryType: item.type,
            score: item.score,
            reason: item.source
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
  getEvidence: (): Promise<EvidenceItem[]> => (USE_MOCKS ? Promise.resolve(evidence) : request<EvidenceItem[]>("/ai/evidence")),
  getTasks: (): Promise<AgentTask[]> => (USE_MOCKS ? Promise.resolve(tasks) : request<AgentTask[]>("/workflows/tasks")),
  getMemories: (): Promise<MemoryPattern[]> =>
    USE_MOCKS ? Promise.resolve(memories) : request<MemoryPattern[]>("/memory/patterns"),
  getPublishPlans: (): Promise<PublishPlan[]> =>
    USE_MOCKS ? Promise.resolve(plans) : request<PublishPlan[]>("/workflows/publish-plans"),
  createAiTask: (workflow: string, payload: unknown) =>
    USE_MOCKS
      ? Promise.resolve({ taskId: `task_${workflow}_${Date.now()}`, status: "pending" })
      : request(`/ai/${workflow}`, { method: "POST", body: JSON.stringify(payload) })
};
