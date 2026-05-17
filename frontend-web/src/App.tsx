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
  CollectorImportRequest,
  CollectorImportResponse,
  ContentItem,
  EvidenceItem,
  EvidenceQuery,
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

type PendingScriptTopic = {
  topic: TopicIdea;
  durationSeconds: number;
};

const fallbackContext: WorkspaceContext = {
  workspaceId: "loading",
  workspaceName: "加载中",
  accountName: "全平台 / 全账号",
  platformScope: []
};

const routePaths: Record<RouteId, string> = {
  dashboard: "",
  contents: "contents",
  audience: "audience",
  topics: "topics",
  scripts: "scripts",
  seo: "seo",
  calendar: "calendar",
  retrospectives: "retrospectives",
  memory: "memory",
  collector: "collector",
  settings: "settings"
};

const pathRoutes = Object.fromEntries(
  Object.entries(routePaths).map(([routeId, path]) => [path, routeId])
) as Record<string, RouteId>;

export function App() {
  const [route, setRoute] = useState<RouteId>(getRouteFromLocation);
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
  const [pendingScriptTopic, setPendingScriptTopic] = useState<PendingScriptTopic | null>(null);
  const [lastTopicGenerationId, setLastTopicGenerationId] = useState<string | null>(null);
  const [lastEvidenceQuery, setLastEvidenceQuery] = useState<EvidenceQuery>({
    workspaceId: "ws_northstar",
    accountId: "douyin_demo",
    platform: "douyin",
    direction: "程序员职业成长",
    limit: 20
  });

  const navigateToRoute = useCallback((nextRoute: RouteId) => {
    setRoute(nextRoute);
    if (typeof window === "undefined") return;

    const nextHash = `#/${routePaths[nextRoute]}`;
    if (window.location.hash !== nextHash) {
      window.location.hash = nextHash;
    }
  }, []);

  useEffect(() => {
    const syncRouteFromLocation = () => {
      const nextRoute = getRouteFromLocation();
      setRoute(nextRoute);

      if (typeof window === "undefined") return;
      const expectedHash = `#/${routePaths[nextRoute]}`;
      if (window.location.hash !== expectedHash) {
        window.history.replaceState(null, "", expectedHash);
      }
    };

    syncRouteFromLocation();
    window.addEventListener("hashchange", syncRouteFromLocation);
    return () => window.removeEventListener("hashchange", syncRouteFromLocation);
  }, []);

  const refreshContentData = useCallback(async () => {
    const [dashboardData, contentRows] = await Promise.all([api.getDashboard(), api.getContents()]);
    setDashboard(dashboardData);
    setContents(contentRows);
  }, []);

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

  const handleImportContents = useCallback(
    async (payload: CollectorImportRequest): Promise<CollectorImportResponse> => {
      const result = await api.importContents(payload);
      await refreshContentData();
      return result;
    },
    [refreshContentData]
  );

  const handleGenerateTopicIdeas = useCallback(
    async (payload: TopicIdeaGenerateRequest) => {
      setTopicGenerationLoading(true);
      setTopicGenerationProgress("正在启动选题生成...");
      setTopicGenerationError(null);
      setTopics([]);
      setLastTopicGenerationId(null);
      const requestPayload = {
        workspaceId: context.workspaceId === "loading" ? "ws_northstar" : context.workspaceId,
        accountIds: ["douyin_demo"],
        count: 10,
        includeEvidence: true,
        ...payload
      };
      setLastEvidenceQuery({
        workspaceId: requestPayload.workspaceId,
        accountId: requestPayload.accountIds?.[0] ?? "douyin_demo",
        platform: requestPayload.platforms?.[0] ?? "douyin",
        direction: requestPayload.direction,
        limit: 20
      });

      try {
        await api.streamTopicIdeas(
          requestPayload,
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
                setLastTopicGenerationId(event.data.generationId);
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

  const openEvidence = useCallback((queryOverride?: EvidenceQuery) => {
    setDrawerOpen(true);
    const query = queryOverride ?? (lastTopicGenerationId ? { generationId: lastTopicGenerationId, limit: 20 } : lastEvidenceQuery);
    void api
      .getEvidence(query)
      .then(setEvidence)
      .catch((error) => {
        console.error("Failed to load evidence", error);
      });
  }, [lastEvidenceQuery, lastTopicGenerationId]);

  const page = useMemo(() => {
    switch (route) {
      case "dashboard":
        return (
          <DashboardPage
            metrics={dashboard.metrics}
            contents={dashboard.contents}
            tasks={dashboard.tasks}
            onOpenEvidence={openEvidence}
            onNavigateTopics={() => navigateToRoute("topics")}
          />
        );
      case "contents":
        return (
          <ContentsPage
            rows={contents}
            workspaceId={context.workspaceId === "loading" ? "ws_northstar" : context.workspaceId}
            onImportContents={handleImportContents}
            onOpenEvidence={openEvidence}
          />
        );
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
            onCreateScript={(topic, durationSeconds) => {
              setPendingScriptTopic({ topic, durationSeconds });
              navigateToRoute("scripts");
            }}
          />
        );
      case "scripts":
        return (
          <ScriptsPage
            initialTopic={pendingScriptTopic?.topic}
            initialTopicDurationSeconds={pendingScriptTopic?.durationSeconds}
            workspaceId={context.workspaceId === "loading" ? "ws_northstar" : context.workspaceId}
            onInitialTopicConsumed={() => setPendingScriptTopic(null)}
            onNavigateSeo={() => navigateToRoute("seo")}
            onOpenEvidence={openEvidence}
          />
        );
      case "seo":
        return <SeoPage onNavigateCalendar={() => navigateToRoute("calendar")} />;
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
    context.workspaceId,
    handleGenerateTopicIdeas,
    handleImportContents,
    navigateToRoute,
    openEvidence,
    memories,
    pendingScriptTopic,
    plans,
    route,
    topicGenerationError,
    topicGenerationLoading,
    topicGenerationProgress,
    topics
  ]);

  return (
    <>
      <AppShell context={context} activeRoute={route} onNavigate={navigateToRoute}>
        {page}
      </AppShell>
      <EvidenceDrawer open={drawerOpen} items={evidence} onClose={() => setDrawerOpen(false)} />
    </>
  );
}

function getRouteFromLocation(): RouteId {
  if (typeof window === "undefined") return "dashboard";

  const hashPath = window.location.hash.replace(/^#\/?/, "").replace(/\/$/, "");
  return pathRoutes[hashPath] ?? "dashboard";
}

function topicEvidenceToDrawerItem(item: Record<string, unknown>): EvidenceItem {
  const id = String(item.memoryId ?? item.id ?? `ev_${Date.now()}`);
  const rawType = String(item.type ?? item.evidenceType ?? item.sourceType ?? item.memoryType ?? "memory");
  const type = normalizeEvidenceType(rawType);
  const metrics = Array.isArray(item.metrics)
    ? item.metrics.map((metric) => String(metric))
    : typeof item.metric === "string"
      ? [item.metric]
      : undefined;
  return {
    id,
    type,
    title: String(item.title ?? "选题生成依据"),
    description: String(item.summary ?? item.description ?? item.reason ?? "来自选题生成过程的证据。"),
    source: String(item.source ?? item.retrievalSource ?? rawType),
    score: typeof item.score === "number" ? item.score : undefined,
    metrics,
    action: typeof item.action === "string" ? item.action : undefined
  };
}

function normalizeEvidenceType(type: string): EvidenceItem["type"] {
  if (type === "content" || type === "history" || type === "video" || type === "related_content") return "content";
  if (type === "metric" || type === "metrics" || type === "performance") return "metric";
  if (type === "keyword" || type === "seo" || type === "search") return "keyword";
  if (type === "audience" || type === "fans" || type === "persona") return "audience";
  if (type === "constraint" || type === "setting" || type === "user_setting") return "constraint";
  if (type === "raw" || type === "diagnostic" || type === "retrieval") return "raw";
  return "memory";
}
