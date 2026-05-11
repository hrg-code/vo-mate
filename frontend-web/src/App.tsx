import { useCallback, useEffect, useMemo, useState } from "react";
import { api } from "./api/client";
import { AppShell } from "./components/AppShell";
import { EvidenceDrawer } from "./features/evidence/EvidenceDrawer";
import { ContentsPage } from "./pages/ContentsPage";
import { DashboardPage } from "./pages/DashboardPage";
import { TopicsPage } from "./pages/TopicsPage";
import {
  AudiencePage,
  CalendarPage,
  CollectorPage,
  MemoryPage,
  RetrospectivesPage,
  ScriptsPage,
  SeoPage,
  SettingsPage
} from "./pages/WorkbenchPages";
import type {
  AgentTask,
  ContentItem,
  EvidenceItem,
  MemoryPattern,
  MetricSummary,
  PublishPlan,
  RouteId,
  TopicIdeaGenerateRequest,
  TopicIdeaStreamEvent,
  TopicIdea,
  WorkspaceContext
} from "./types";

type DashboardState = {
  metrics: MetricSummary[];
  contents: ContentItem[];
  tasks: AgentTask[];
};

const fallbackContext: WorkspaceContext = {
  workspaceId: "loading",
  workspaceName: "加载中",
  accountName: "全平台 / 全账号",
  platformScope: []
};

export function App() {
  const [route, setRoute] = useState<RouteId>("dashboard");
  const [context, setContext] = useState<WorkspaceContext>(fallbackContext);
  const [dashboard, setDashboard] = useState<DashboardState>({ metrics: [], contents: [], tasks: [] });
  const [contents, setContents] = useState<ContentItem[]>([]);
  const [topics, setTopics] = useState<TopicIdea[]>([]);
  const [evidence, setEvidence] = useState<EvidenceItem[]>([]);
  const [memories, setMemories] = useState<MemoryPattern[]>([]);
  const [plans, setPlans] = useState<PublishPlan[]>([]);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [topicGenerationLoading, setTopicGenerationLoading] = useState(false);
  const [topicGenerationProgress, setTopicGenerationProgress] = useState("");
  const [topicGenerationError, setTopicGenerationError] = useState<string | null>(null);

  useEffect(() => {
    void Promise.all([
      api.getWorkspace(),
      api.getDashboard(),
      api.getContents(),
      api.getTopicIdeas(),
      api.getEvidence(),
      api.getMemories(),
      api.getPublishPlans()
    ]).then(([workspace, dashboardData, contentRows, topicRows, evidenceRows, memoryRows, publishPlans]) => {
      setContext(workspace);
      setDashboard(dashboardData);
      setContents(contentRows);
      setTopics(topicRows);
      setEvidence(evidenceRows);
      setMemories(memoryRows);
      setPlans(publishPlans);
    });
  }, []);

  const handleGenerateTopicIdeas = useCallback(
    async (payload: TopicIdeaGenerateRequest) => {
      setTopicGenerationLoading(true);
      setTopicGenerationProgress("正在启动选题生成...");
      setTopicGenerationError(null);
      setTopics([]);

      try {
        await api.streamTopicIdeas(
          {
            workspaceId: context.workspaceId === "loading" ? "ws_northstar" : context.workspaceId,
            accountIds: ["douyin_demo"],
            count: 10,
            includeEvidence: true,
            ...payload
          },
          (event: TopicIdeaStreamEvent) => {
            switch (event.event) {
              case "progress":
                setTopicGenerationProgress(event.data.message);
                break;
              case "evidence":
                setEvidence(event.data.items.map(topicEvidenceToDrawerItem));
                break;
              case "topic_idea":
                setTopics((current) => {
                  if (current.some((topic) => topic.id === event.data.id)) return current;
                  return [...current, event.data];
                });
                break;
              case "done":
                setTopics(event.data.topicIdeas);
                setTopicGenerationProgress(`已生成 ${event.data.count} 个候选选题。`);
                break;
              case "error":
                setTopicGenerationError(event.data.message);
                setTopicGenerationProgress("");
                break;
              default:
                break;
            }
          }
        );
      } catch (error) {
        setTopicGenerationError(error instanceof Error ? error.message : "生成选题失败");
        setTopicGenerationProgress("");
      } finally {
        setTopicGenerationLoading(false);
      }
    },
    [context.workspaceId]
  );

  const page = useMemo(() => {
    const openEvidence = () => setDrawerOpen(true);

    switch (route) {
      case "dashboard":
        return (
          <DashboardPage
            metrics={dashboard.metrics}
            contents={dashboard.contents}
            tasks={dashboard.tasks}
            onOpenEvidence={openEvidence}
            onNavigateTopics={() => setRoute("topics")}
          />
        );
      case "contents":
        return <ContentsPage rows={contents} onOpenEvidence={openEvidence} />;
      case "audience":
        return <AudiencePage />;
      case "topics":
        return (
          <TopicsPage
            topics={topics}
            generationError={topicGenerationError}
            generationLoading={topicGenerationLoading}
            generationProgress={topicGenerationProgress}
            onGenerate={handleGenerateTopicIdeas}
            onOpenEvidence={openEvidence}
            onCreateScript={() => setRoute("scripts")}
          />
        );
      case "scripts":
        return <ScriptsPage onNavigateSeo={() => setRoute("seo")} onOpenEvidence={openEvidence} />;
      case "seo":
        return <SeoPage onNavigateCalendar={() => setRoute("calendar")} />;
      case "calendar":
        return <CalendarPage plans={plans} />;
      case "retrospectives":
        return <RetrospectivesPage onOpenEvidence={openEvidence} />;
      case "memory":
        return <MemoryPage memories={memories} />;
      case "collector":
        return <CollectorPage />;
      case "settings":
        return <SettingsPage />;
      default:
        return null;
    }
  }, [
    contents,
    dashboard,
    handleGenerateTopicIdeas,
    memories,
    plans,
    route,
    topicGenerationError,
    topicGenerationLoading,
    topicGenerationProgress,
    topics
  ]);

  return (
    <>
      <AppShell context={context} activeRoute={route} onNavigate={setRoute}>
        {page}
      </AppShell>
      <EvidenceDrawer open={drawerOpen} items={evidence} onClose={() => setDrawerOpen(false)} />
    </>
  );
}

function topicEvidenceToDrawerItem(item: Record<string, unknown>): EvidenceItem {
  const id = String(item.memoryId ?? item.id ?? `ev_${Date.now()}`);
  const type = typeof item.memoryType === "string" ? item.memoryType : "memory";
  return {
    id,
    type: "memory",
    title: String(item.title ?? "选题生成依据"),
    description: String(item.summary ?? item.reason ?? "来自选题生成过程的证据。"),
    source: String(type),
    score: typeof item.score === "number" ? item.score : undefined
  };
}
