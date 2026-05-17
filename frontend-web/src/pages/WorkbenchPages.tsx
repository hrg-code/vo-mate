import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Alert, Button, Empty, Input, InputNumber, Progress, Select, Tabs, Tag } from "antd";
import { api } from "../api/client";
import { PageHeader } from "../components/PageHeader";
import { platformLabel } from "../components/format";
import {
  composeScriptBody,
  createScriptBlock,
  createScriptBlocksFromBody,
  normalizeScriptBlocks,
  scriptBlockRoleOptions,
  serializeScriptBlocks
} from "../features/scripts/scriptBlocks";
import type {
  MemoryPattern,
  PublishPlan,
  ScriptBlock,
  ScriptBlockRole,
  ScriptCopilotAction,
  ScriptDraft,
  ScriptDraftVersion,
  EvidenceQuery,
  ScriptQualityReport,
  ScriptSeoPackage,
  TopicIdea
} from "../types";

const { TextArea } = Input;

export function AudiencePage() {
  return (
    <>
      <PageHeader
        title="粉丝画像"
        subtitle="理解粉丝是谁、何时活跃、喜欢什么"
        actions={<Button type="primary">生成画像洞察</Button>}
      />
      <div className="dashboard-grid">
        <section className="panel">
          <h2>兴趣分布</h2>
          <BarList items={[["职场成长", 82], ["AI 工具", 74], ["面试求职", 67], ["副业转型", 48]]} />
        </section>
        <section className="panel">
          <h2>活跃时间</h2>
          <div className="heatmap">
            {Array.from({ length: 28 }, (_, index) => (
              <span className="heat-cell" style={{ opacity: 0.25 + (index % 7) * 0.1 }} key={index} />
            ))}
          </div>
        </section>
      </div>
    </>
  );
}

export function ScriptsPage({
  initialTopic,
  initialTopicDurationSeconds,
  onInitialTopicConsumed,
  onNavigateSeo,
  onOpenEvidence,
  workspaceId = "ws_northstar"
}: {
  initialTopic?: TopicIdea;
  initialTopicDurationSeconds?: number;
  onInitialTopicConsumed?: () => void;
  onNavigateSeo: () => void;
  onOpenEvidence: (query?: EvidenceQuery) => void;
  workspaceId?: string;
}) {
  const [drafts, setDrafts] = useState<ScriptDraft[]>([]);
  const [activeDraft, setActiveDraft] = useState<ScriptDraft | null>(null);
  const [scriptBlocks, setScriptBlocks] = useState<ScriptBlock[]>([]);
  const [savedBlocksSnapshot, setSavedBlocksSnapshot] = useState("");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [qualityReport, setQualityReport] = useState<ScriptQualityReport | null>(null);
  const [seoPackage, setSeoPackage] = useState<ScriptSeoPackage | null>(null);
  const [copilotLoading, setCopilotLoading] = useState(false);
  const [copilotError, setCopilotError] = useState<string | null>(null);
  const consumedInitialTopicId = useRef<string | null>(null);

  const currentVersion = activeDraft?.currentVersion;
  const editorValue = useMemo(() => composeScriptBody(scriptBlocks), [scriptBlocks]);
  const currentEvidenceGenerationId =
    currentVersion?.generationId ??
    activeDraft?.versions.find((version) => version.id === currentVersion?.parentVersionId)?.generationId;
  const charCount = editorValue.replace(/\s/g, "").length;
  const blockDurationSeconds = scriptBlocks.reduce((sum, block) => sum + (block.durationSeconds ?? 0), 0);
  const estimatedDuration = blockDurationSeconds > 0 ? blockDurationSeconds : currentVersion?.durationSeconds ?? estimateScriptDuration(editorValue);
  const currentBlocksSnapshot = useMemo(() => serializeScriptBlocks(scriptBlocks), [scriptBlocks]);
  const dirty = Boolean(currentVersion && currentBlocksSnapshot !== savedBlocksSnapshot);

  const refreshDraft = useCallback(async (draftId: string) => {
    const detail = await api.getScriptDraft(draftId);
    setActiveDraft(detail);
    setDrafts([detail]);
  }, []);

  const upsertActiveDraft = useCallback((draft: ScriptDraft) => {
    setDrafts([draft]);
    setActiveDraft(draft);
  }, []);

  const createDraftFromTopic = useCallback(
    async (topic?: TopicIdea, durationSeconds = 60) => {
      const targetPlatform = topic?.targetPlatforms?.[0] ?? "douyin";
      const topicText = topic?.title ?? "35 岁程序员不是危机，是岗位切换信号";
      const draft = await api.createScriptDraft({
        workspaceId,
        topicIdeaId: topic?.id,
        topic: topicText,
        title: topic?.title,
        platform: targetPlatform,
        durationSeconds
      });
      upsertActiveDraft(draft);
      return draft;
    },
    [upsertActiveDraft, workspaceId]
  );

  const loadDrafts = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      if (initialTopic) {
        setDrafts([]);
        setActiveDraft(null);
        return;
      }
      const rows = await api.getScriptDrafts();
      if (rows.length > 0) {
        await refreshDraft(rows[0].id);
      } else {
        setDrafts([]);
        setActiveDraft(null);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "加载脚本草稿失败");
    } finally {
      setLoading(false);
    }
  }, [initialTopic, refreshDraft]);

  useEffect(() => {
    void loadDrafts();
  }, [loadDrafts]);

  useEffect(() => {
    if (!initialTopic || consumedInitialTopicId.current === initialTopic.id) return;
    setDrafts([]);
    setActiveDraft(null);
    consumedInitialTopicId.current = initialTopic.id;
    setSaving(true);
    setError(null);
    void createDraftFromTopic(initialTopic, initialTopicDurationSeconds ?? 60)
      .then(() => {
        onInitialTopicConsumed?.();
      })
      .catch((err) => {
        setError(err instanceof Error ? err.message : "生成脚本失败");
      })
      .finally(() => {
        setSaving(false);
        setLoading(false);
      });
  }, [createDraftFromTopic, initialTopic, initialTopicDurationSeconds, onInitialTopicConsumed]);

  useEffect(() => {
    if (!currentVersion) {
      setScriptBlocks([]);
      setSavedBlocksSnapshot("");
      return;
    }
    const normalizedBlocks = normalizeScriptBlocks(currentVersion.blocks, currentVersion.body, currentVersion.durationSeconds);
    setScriptBlocks(normalizedBlocks);
    setSavedBlocksSnapshot(serializeScriptBlocks(normalizedBlocks));
  }, [currentVersion]);

  useEffect(() => {
    if (!activeDraft || !currentVersion) {
      setQualityReport(null);
      setSeoPackage(null);
      return;
    }

    let active = true;
    const timeoutId = window.setTimeout(() => {
      setCopilotLoading(true);
      setCopilotError(null);
      void Promise.all([
        api.getScriptQualityReport(activeDraft.id, currentVersion.id, editorValue),
        api.getScriptSeoPackage(activeDraft.id, currentVersion.id, editorValue)
      ])
        .then(([report, seo]) => {
          if (!active) return;
          setQualityReport(report);
          setSeoPackage(seo);
        })
        .catch((err) => {
          if (!active) return;
          setCopilotError(err instanceof Error ? err.message : "加载 Copilot 失败");
        })
        .finally(() => {
          if (active) setCopilotLoading(false);
        });
    }, 250);

    return () => {
      active = false;
      window.clearTimeout(timeoutId);
    };
  }, [activeDraft, currentVersion, editorValue]);

  const groupedVersions = useMemo(() => {
    const versions = activeDraft?.versions ?? [];
    return {
      adopted: versions.filter((version) => version.status === "adopted"),
      candidate: versions.filter((version) => version.status === "candidate"),
      history: versions.filter((version) => version.status === "discarded")
    };
  }, [activeDraft?.versions]);

  const handleCreateDraft = async () => {
    setSaving(true);
    setError(null);
    try {
      await createDraftFromTopic();
    } catch (err) {
      setError(err instanceof Error ? err.message : "创建脚本失败");
    } finally {
      setSaving(false);
    }
  };

  const handleSelectDraft = async (draftId: string) => {
    setError(null);
    try {
      await refreshDraft(draftId);
    } catch (err) {
      setError(err instanceof Error ? err.message : "切换脚本失败");
    }
  };

  const handleSelectVersion = async (versionId: string) => {
    if (!activeDraft) return;
    setSaving(true);
    setError(null);
    try {
      const draft = await api.updateScriptCurrentVersion(activeDraft.id, versionId);
      setActiveDraft(draft);
      setDrafts([draft]);
    } catch (err) {
      setError(err instanceof Error ? err.message : "切换版本失败");
    } finally {
      setSaving(false);
    }
  };

  const handleSaveVersion = async () => {
    if (!activeDraft || !currentVersion || !editorValue.trim()) return;
    setSaving(true);
    setError(null);
    try {
      const nextVersionNo = activeDraft.versions.length + 1;
      const draft = await api.createScriptVersion(activeDraft.id, {
        body: editorValue,
        blocks: scriptBlocks,
        label: `v${nextVersionNo} 用户修改`,
        platform: currentVersion.platform ?? activeDraft.platform,
        durationSeconds: estimatedDuration,
        description: currentVersion.description,
        tags: currentVersion.tags,
        titleCandidates: currentVersion.titleCandidates,
        sourceType: "user_save",
        parentVersionId: currentVersion.id
      });
      setActiveDraft(draft);
      setDrafts([draft]);
    } catch (err) {
      setError(err instanceof Error ? err.message : "保存版本失败");
    } finally {
      setSaving(false);
    }
  };

  const handleRunCopilotAction = async (actionId: ScriptCopilotAction["id"]) => {
    if (!activeDraft || !currentVersion || !editorValue.trim()) return;
    setCopilotLoading(true);
    setCopilotError(null);
    try {
      const suggestion = await api.runScriptCopilotAction(activeDraft.id, currentVersion.id, actionId, editorValue);
      setScriptBlocks(createScriptBlocksFromBody(suggestion.body, currentVersion.durationSeconds));
    } catch (err) {
      setCopilotError(err instanceof Error ? err.message : "生成 Copilot 建议失败");
    } finally {
      setCopilotLoading(false);
    }
  };

  const handleAddBlock = () => {
    setScriptBlocks((current) => [...current, createScriptBlock("point")]);
  };

  const handleUpdateBlock = (blockId: string, patch: Partial<ScriptBlock>) => {
    setScriptBlocks((current) => current.map((block) => (block.id === blockId ? { ...block, ...patch } : block)));
  };

  const handleChangeBlockRole = (blockId: string, role: ScriptBlockRole) => {
    const option = scriptBlockRoleOptions.find((item) => item.role === role);
    setScriptBlocks((current) =>
      current.map((block) =>
        block.id === blockId
          ? {
              ...block,
              role,
              label: option?.label ?? block.label,
              visualHint: block.visualHint || option?.visualHint
            }
          : block
      )
    );
  };

  const handleMoveBlock = (blockId: string, direction: -1 | 1) => {
    setScriptBlocks((current) => {
      const index = current.findIndex((block) => block.id === blockId);
      const targetIndex = index + direction;
      if (index < 0 || targetIndex < 0 || targetIndex >= current.length) return current;
      const next = [...current];
      [next[index], next[targetIndex]] = [next[targetIndex], next[index]];
      return next;
    });
  };

  const handleRemoveBlock = (blockId: string) => {
    setScriptBlocks((current) => (current.length <= 1 ? current : current.filter((block) => block.id !== blockId)));
  };

  const handleOpenCurrentEvidence = useCallback(() => {
    onOpenEvidence(currentEvidenceGenerationId ? { generationId: currentEvidenceGenerationId, limit: 20 } : undefined);
  }, [currentEvidenceGenerationId, onOpenEvidence]);

  return (
    <>
      <PageHeader
        title="脚本工作台"
        subtitle="把选题转为可拍、可改、可发布的口播内容"
        actions={
          <>
            <Button onClick={handleCreateDraft} loading={saving}>
              生成脚本
            </Button>
            <Button onClick={handleSaveVersion} disabled={!dirty || !editorValue.trim()} loading={saving}>
              保存版本
            </Button>
            <Button type="primary" onClick={onNavigateSeo}>
              生成 SEO
            </Button>
          </>
        }
      />
      {error ? <Alert className="page-gap" type="error" showIcon message={error} /> : null}
      <ScriptDraftToolbar
        activeDraft={activeDraft}
        drafts={drafts}
        groupedVersions={groupedVersions}
        loading={loading}
        saving={saving}
        onCreateDraft={handleCreateDraft}
        onSelectDraft={handleSelectDraft}
        onSelectVersion={handleSelectVersion}
      />
      <section className="split-page">

        <ScriptProductionSheet
          blocks={scriptBlocks}
          charCount={charCount}
          currentVersion={currentVersion}
          estimatedDuration={estimatedDuration}
          loading={copilotLoading}
          seoPackage={seoPackage}
          onAddBlock={handleAddBlock}
          onChangeBlockRole={handleChangeBlockRole}
          onOpenEvidence={handleOpenCurrentEvidence}
          onOptimize={handleRunCopilotAction}
          onMoveBlock={handleMoveBlock}
          onRemoveBlock={handleRemoveBlock}
          onUpdateBlock={handleUpdateBlock}
        />

        <QualityInspector
          loading={copilotLoading}
          error={copilotError}
          qualityReport={qualityReport}
          onRunAction={handleRunCopilotAction}
        />
      </section>
    </>
  );
}

function ScriptDraftToolbar({
  activeDraft,
  drafts,
  groupedVersions,
  loading,
  saving,
  onCreateDraft,
  onSelectDraft,
  onSelectVersion
}: {
  activeDraft: ScriptDraft | null;
  drafts: ScriptDraft[];
  groupedVersions: {
    adopted: ScriptDraftVersion[];
    candidate: ScriptDraftVersion[];
    history: ScriptDraftVersion[];
  };
  loading: boolean;
  saving: boolean;
  onCreateDraft: () => Promise<void>;
  onSelectDraft: (draftId: string) => Promise<void>;
  onSelectVersion: (versionId: string) => Promise<void>;
}) {
  const versionOptions = [
    ...groupedVersions.adopted.map((version) => ({ value: version.id, label: `当前采用 · ${version.label}` })),
    ...groupedVersions.candidate.map((version) => ({ value: version.id, label: `候选 · ${version.label}` })),
    ...groupedVersions.history.map((version) => ({ value: version.id, label: `历史 · ${version.label}` }))
  ];

  return (
    <section className="panel script-draft-toolbar">
      <label className="toolbar-field toolbar-field-wide">
        <span>脚本草稿</span>
        <Select
          aria-label="脚本草稿"
          loading={loading}
          disabled={drafts.length === 0}
          value={activeDraft?.id}
          placeholder={loading ? "正在加载脚本草稿" : "暂无脚本草稿"}
          options={drafts.map((draft) => ({
            value: draft.id,
            label: draft.title
          }))}
          onChange={(draftId) => void onSelectDraft(draftId)}
        />
      </label>
      <label className="toolbar-field">
        <span>版本</span>
        <Select
          aria-label="脚本版本"
          disabled={versionOptions.length === 0}
          value={activeDraft?.currentVersionId}
          placeholder="暂无版本"
          options={versionOptions}
          onChange={(versionId) => void onSelectVersion(versionId)}
        />
      </label>
      <div className="toolbar-current">
        <span>当前状态</span>
        <strong>{activeDraft?.currentVersion ? sourceTypeLabel(activeDraft.currentVersion.sourceType) : "未生成"}</strong>
        <p>{activeDraft?.platform ? platformLabel[activeDraft.platform] : "未定平台"}</p>
      </div>
      <Button onClick={() => void onCreateDraft()} loading={saving}>
        新建脚本
      </Button>
    </section>
  );
}

function ScriptProductionSheet({
  blocks,
  charCount,
  currentVersion,
  estimatedDuration,
  loading,
  seoPackage,
  onAddBlock,
  onChangeBlockRole,
  onOpenEvidence,
  onOptimize,
  onMoveBlock,
  onRemoveBlock,
  onUpdateBlock
}: {
  blocks: ScriptBlock[];
  charCount: number;
  currentVersion?: ScriptDraftVersion;
  estimatedDuration: number;
  loading: boolean;
  seoPackage: ScriptSeoPackage | null;
  onAddBlock: () => void;
  onChangeBlockRole: (blockId: string, role: ScriptBlockRole) => void;
  onOpenEvidence: () => void;
  onOptimize: (actionId: ScriptCopilotAction["id"]) => Promise<void>;
  onMoveBlock: (blockId: string, direction: -1 | 1) => void;
  onRemoveBlock: (blockId: string) => void;
  onUpdateBlock: (blockId: string, patch: Partial<ScriptBlock>) => void;
}) {
  if (!currentVersion) {
    return (
      <section className="panel script-editor">
        <h2>内容生产表</h2>
        <Empty description="选择或生成一个脚本版本后开始编辑" />
      </section>
    );
  }

  const titleText = readCandidateText(currentVersion.titleCandidates[0]) || "点击优化生成标题";
  const descriptionText = currentVersion.description || seoPackage?.descriptionCandidates[0]?.text || "点击优化生成简介";
  const tagText = currentVersion.tags.length > 0 ? currentVersion.tags.join("，") : seoPackage?.tagCandidates.join("，") || "点击优化生成标签";
  const seoText = seoPackage?.keywordCoverage.map((item) => item.keyword).join("，") || "点击优化生成 SEO 词";

  return (
    <section className="panel script-editor script-production">
      <div className="panel-header script-production-header">
        <div>
          <h2>内容生产表</h2>
          <p className="muted">{currentVersion.label} · 标题、简介、标签、SEO 和口播脚本在一张表里完成。</p>
        </div>
        <Tag color="success">预计 {estimatedDuration} 秒</Tag>
      </div>

      <div className="script-meta-bar">
        <label>
          <span>平台</span>
          <Select
            aria-label="平台"
            options={[
              { value: "douyin", label: "抖音" },
              { value: "kuaishou", label: "快手" },
              { value: "xiaohongshu", label: "小红书" },
              { value: "youtube", label: "YouTube Shorts" },
              { value: "wechat", label: "视频号" }
            ]}
            value={currentVersion.platform ?? "douyin"}
            disabled
          />
        </label>
        <label>
          <span>时长</span>
          <Select
            aria-label="目标时长"
            options={[
              { value: 45, label: "45秒" },
              { value: 60, label: "60秒" },
              { value: 90, label: "90秒" }
            ]}
            value={nearestDurationOption(estimatedDuration)}
            disabled
          />
        </label>
      </div>

      <div className="production-table">
        <ProductionAssetRow label="标题" value={titleText} action="title" loading={loading} onOpenEvidence={onOpenEvidence} onOptimize={onOptimize} />
        <ProductionAssetRow label="简介" value={descriptionText} action="teleprompter" loading={loading} onOpenEvidence={onOpenEvidence} onOptimize={onOptimize} multiline />
        <ProductionAssetRow label="标签" value={tagText} action="adapt_xiaohongshu" loading={loading} onOpenEvidence={onOpenEvidence} onOptimize={onOptimize} />
        <ProductionAssetRow label="SEO词" value={seoText} action="fix_seo" loading={loading} onOpenEvidence={onOpenEvidence} onOptimize={onOptimize} />
      </div>

      <div className="script-block-list production-script-list">
        {blocks.map((block, index) => (
          <article className="production-script-row" key={block.id}>
            <div className="production-time">
              <strong>{timeRangeForBlock(blocks, index)}</strong>
              <Select
                aria-label="脚本段落类型"
                options={scriptBlockRoleOptions.map((option) => ({ value: option.role, label: productionRoleLabel[option.role] }))}
                value={block.role}
                onChange={(role) => onChangeBlockRole(block.id, role)}
              />
            </div>
            <label className="production-content">
              <span>{productionRoleLabel[block.role]}</span>
              <TextArea
                value={block.voiceover}
                autoSize={{ minRows: 3, maxRows: 8 }}
                onChange={(event) => onUpdateBlock(block.id, { voiceover: event.target.value })}
                placeholder="写这一段要说出口的内容"
              />
            </label>
            <div className="production-actions">
              <Button size="small" onClick={onOpenEvidence}>
                证据
              </Button>
              <Button size="small" type="primary" ghost loading={loading} onClick={() => void onOptimize(roleOptimizeAction[block.role])}>
                优化
              </Button>
              <div className="production-row-tools">
                <Button size="small" disabled={index === 0} onClick={() => onMoveBlock(block.id, -1)}>
                  上移
                </Button>
                <Button size="small" disabled={index === blocks.length - 1} onClick={() => onMoveBlock(block.id, 1)}>
                  下移
                </Button>
                <Button size="small" danger disabled={blocks.length <= 1} onClick={() => onRemoveBlock(block.id)}>
                  删除
                </Button>
              </div>
              <InputNumber
                aria-label="预计秒数"
                min={1}
                max={180}
                value={block.durationSeconds}
                onChange={(value) => onUpdateBlock(block.id, { durationSeconds: typeof value === "number" ? value : undefined })}
              />
            </div>
          </article>
        ))}
      </div>

      <Button className="page-gap-small" onClick={onAddBlock}>
        新增段落
      </Button>
      <div className="word-count">
        <span>字数 {charCount}</span>
        <span>段落 {blocks.length}</span>
        <span>结构：标题 / 简介 / 标签 / SEO / 开头 / 痛点 / 洞察 / 案例 / 互动</span>
      </div>
    </section>
  );
}

function ProductionAssetRow({
  label,
  value,
  action,
  loading,
  multiline = false,
  onOpenEvidence,
  onOptimize
}: {
  label: string;
  value: string;
  action: ScriptCopilotAction["id"] | "title";
  loading: boolean;
  multiline?: boolean;
  onOpenEvidence: () => void;
  onOptimize: (actionId: ScriptCopilotAction["id"]) => Promise<void>;
}) {
  return (
    <article className="production-asset-row">
      <strong>{label}</strong>
      {multiline ? <TextArea value={value} autoSize={{ minRows: 2, maxRows: 4 }} readOnly /> : <Input value={value} readOnly />}
      <div className="production-actions">
        <Button size="small" onClick={onOpenEvidence}>
          证据
        </Button>
        <Button
          size="small"
          type="primary"
          ghost
          loading={loading}
          onClick={() => void onOptimize(action === "title" ? "strengthen_hook" : action)}
        >
          优化
        </Button>
      </div>
    </article>
  );
}

const productionRoleLabel: Record<ScriptBlockRole, string> = {
  hook: "开头钩子",
  pain: "痛点共鸣",
  point: "核心洞察",
  proof: "案例证明",
  method: "方法步骤",
  turn: "反转冲突",
  summary: "总结收束",
  cta: "互动引导"
};

const roleOptimizeAction: Record<ScriptBlockRole, ScriptCopilotAction["id"]> = {
  hook: "strengthen_hook",
  pain: "teleprompter",
  point: "compress_45",
  proof: "add_case",
  method: "teleprompter",
  turn: "strengthen_hook",
  summary: "compress_45",
  cta: "fix_cta"
};

function nearestDurationOption(duration: number) {
  if (duration <= 52) return 45;
  if (duration <= 75) return 60;
  return 90;
}

function timeRangeForBlock(blocks: ScriptBlock[], index: number) {
  const start = blocks.slice(0, index).reduce((sum, block) => sum + (block.durationSeconds ?? 0), 0);
  const current = blocks[index]?.durationSeconds ?? 0;
  if (current <= 0) return "未估时";
  return `${start}-${start + current}s`;
}

function readCandidateText(candidate: Record<string, unknown> | undefined) {
  if (!candidate) return "";
  const text = candidate.text ?? candidate.title ?? candidate.value;
  return typeof text === "string" ? text : "";
}

function QualityInspector({
  error,
  loading,
  qualityReport,
  onRunAction
}: {
  error: string | null;
  loading: boolean;
  qualityReport: ScriptQualityReport | null;
  onRunAction: (actionId: ScriptCopilotAction["id"]) => Promise<void>;
}) {
  return (
    <aside className="panel quality-inspector">
      <h2>质检</h2>
      {error ? <Alert className="page-gap-small" type="error" showIcon message={error} /> : null}
      <QualityTab loading={loading} report={qualityReport} onRunAction={onRunAction} />
    </aside>
  );
}

function sourceTypeLabel(sourceType?: string) {
  const labels: Record<string, string> = {
    ai_initial: "AI 初稿",
    user_save: "用户保存",
    ai_rewrite: "AI 改写",
    platform_adaptation: "平台适配"
  };
  return sourceType ? labels[sourceType] ?? sourceType : "未定来源";
}

function QualityTab({
  loading,
  report,
  onRunAction
}: {
  loading: boolean;
  report: ScriptQualityReport | null;
  onRunAction: (actionId: ScriptCopilotAction["id"]) => Promise<void>;
}) {
  if (!report) {
    return <Empty description={loading ? "正在生成质检报告" : "暂无质检报告"} />;
  }

  return (
    <div className="copilot-tab">
      <div className="quality-score">
        <Progress type="circle" percent={report.overallScore} size={76} strokeColor={scoreColor(report.overallScore)} />
        <div>
          <strong>综合评分</strong>
          <p className="muted">{report.summary}</p>
        </div>
      </div>
      <div className="quality-grid">
        {qualityMetricEntries.map(([key, label]) => (
          <div className="quality-metric" key={key}>
            <span>{label}</span>
            <Progress percent={report.metrics[key]} size="small" strokeColor={scoreColor(report.metrics[key])} />
          </div>
        ))}
      </div>
      <FixList title="优先修复" fixes={report.mustFix} onRunAction={onRunAction} />
      <FixList title="可以优化" fixes={report.niceToHave} onRunAction={onRunAction} />
    </div>
  );
}

function FixList({
  title,
  fixes,
  onRunAction
}: {
  title: string;
  fixes: ScriptQualityReport["mustFix"];
  onRunAction: (actionId: ScriptCopilotAction["id"]) => Promise<void>;
}) {
  if (fixes.length === 0) return null;
  return (
    <div className="page-gap">
      <h3>{title}</h3>
      <div className="evidence-list">
        {fixes.map((fix) => (
          <article className="evidence-item" key={fix.id}>
            <strong>{fix.title}</strong>
            <p className="muted">{fix.description}</p>
            <Button onClick={() => void onRunAction(fix.actionId)}>一键修复</Button>
          </article>
        ))}
      </div>
    </div>
  );
}

const qualityMetricEntries: Array<[keyof ScriptQualityReport["metrics"], string]> = [
  ["persona", "人设匹配"],
  ["hook", "开头强度"],
  ["retention", "留存节奏"],
  ["seo", "SEO/GEO"],
  ["oral", "口播自然度"],
  ["risk", "风险表达"],
  ["conversion", "转化潜力"],
  ["duration", "时长匹配"]
];

function estimateScriptDuration(body: string) {
  return Math.max(15, Math.round(body.replace(/\s/g, "").length / 4));
}

function scoreColor(score: number) {
  if (score >= 85) return "#0f766e";
  if (score >= 70) return "#2563eb";
  return "#d97706";
}

export function SeoPage({ onNavigateCalendar }: { onNavigateCalendar: () => void }) {
  return (
    <>
      <PageHeader
        title="SEO 优化"
        subtitle="生成平台适配标题、简介、标签与关键词布局"
        actions={
          <Button type="primary" onClick={onNavigateCalendar}>
            加入发布计划
          </Button>
        }
      />
      <section className="panel">
        <Tabs
          defaultActiveKey="douyin"
          items={[
            { key: "douyin", label: "抖音" },
            { key: "xiaohongshu", label: "小红书" },
            { key: "youtube", label: "YouTube Shorts" },
            { key: "wechat", label: "视频号" }
          ]}
        />
        <h2>标题实验</h2>
        <div className="action-list">
          <article className="action-item">
            <div className="panel-header tight">
              <strong>35 岁程序员最该换的不是行业，而是岗位形态</strong>
              <Tag color="success">92</Tag>
            </div>
            <p className="muted">覆盖关键词：35 岁、程序员、岗位、转型</p>
          </article>
          <article className="action-item">
            <div className="panel-header tight">
              <strong>程序员 35 岁危机，其实是一个误解</strong>
              <Tag color="warning">78</Tag>
            </div>
            <p className="muted">冲突明确，但搜索词覆盖偏弱。</p>
          </article>
        </div>
        <h2 className="page-gap">简介</h2>
        <TextArea defaultValue="这条视频聊程序员 35 岁后的职业切换：从只写代码，到能拆问题、控风险、交付方案。" />
        <div className="chip-row page-gap-small">
          <Tag>#程序员</Tag>
          <Tag>#35岁危机</Tag>
          <Tag>#AI时代</Tag>
          <Tag>#职场成长</Tag>
        </div>
      </section>
    </>
  );
}

export function CalendarPage({ plans }: { plans: PublishPlan[] }) {
  const stages: PublishPlan["stage"][] = ["idea", "script", "editing", "ready"];
  const labels: Record<PublishPlan["stage"], string> = {
    idea: "灵感",
    script: "已生成脚本",
    shooting: "待拍摄",
    editing: "待剪辑",
    ready: "待发布",
    published: "已发布"
  };

  return (
    <>
      <PageHeader title="发布日历" subtitle="管理内容从脚本到发布的计划" actions={<Button type="primary">新建计划</Button>} />
      <section className="kanban">
        {stages.map((stage) => (
          <div className="kanban-column" key={stage}>
            <h3>{labels[stage]}</h3>
            {plans
              .filter((plan) => plan.stage === stage)
              .map((plan) => (
                <article className="calendar-item" key={plan.id}>
                  <Tag className={`platform-tag platform-${plan.platform}`}>{platformLabel[plan.platform]}</Tag>
                  <h3>{plan.title}</h3>
                  <p className="muted">{plan.scheduledAt}</p>
                </article>
              ))}
          </div>
        ))}
      </section>
    </>
  );
}

export function RetrospectivesPage({ onOpenEvidence }: { onOpenEvidence: () => void }) {
  return (
    <>
      <PageHeader
        title="复盘中心"
        subtitle="管理单条视频复盘、周期报告和可沉淀经验"
        actions={
          <Button type="primary" onClick={onOpenEvidence}>
            生成周报
          </Button>
        }
      />
      <section className="panel">
        <Tabs
          defaultActiveKey="single"
          items={[
            { key: "single", label: "单条视频" },
            { key: "weekly", label: "周报" },
            { key: "monthly", label: "月报" },
            { key: "patterns", label: "模式" }
          ]}
        />
        <div className="action-list">
          <article className="action-item">
            <h2>程序员 35 岁后还能不能继续写代码</h2>
            <p className="muted">结论：开头问题命中强，但中段缺少反例，评论转化高于收藏。</p>
            <div className="button-row">
              <Button type="primary">写入记忆库</Button>
              <Button>驳回结论</Button>
            </div>
          </article>
          <article className="action-item">
            <h2>为什么你的简历总被 HR 刷掉</h2>
            <p className="muted">结论：标题搜索价值高，完播稳定，适合承接面试系列。</p>
            <Button onClick={onOpenEvidence}>查看依据</Button>
          </article>
        </div>
      </section>
    </>
  );
}

export function MemoryPage({ memories }: { memories: MemoryPattern[] }) {
  return (
    <>
      <PageHeader title="记忆库" subtitle="查看、确认、降低权重或删除系统学到的经验" actions={<Button type="primary">审核候选记忆</Button>} />
      <section className="memory-grid">
        {memories.map((memory) => (
          <article className="memory-card" key={memory.id}>
            <Tag>{memory.type}</Tag>
            <h2>{memory.summary}</h2>
            <p className="muted">
              权重 {memory.confidence} · 来源 {memory.sourceCount} 条内容 · {memory.lastVerifiedAt}
            </p>
            <div className="button-row">
              <Button type="primary">确认</Button>
              <Button>降权</Button>
              <Button danger>删除</Button>
            </div>
          </article>
        ))}
      </section>
    </>
  );
}

export function CollectorPage() {
  return (
    <>
      <PageHeader
        title="采集管理"
        subtitle="管理 Electron、浏览器插件、手动导入与采集任务状态"
        actions={
          <>
            <Button>手动导入</Button>
            <Button type="primary">立即同步</Button>
          </>
        }
      />
      <section>
        <div className="connector-grid">
          {["抖音", "快手", "小红书", "YouTube", "视频号"].map((name, index) => (
            <article className="connector" key={name}>
              <span className="status-dot" />
              <h2>{name}</h2>
              <p className="muted">{index === 0 ? "已连接，2 分钟前同步" : "待配置采集方式"}</p>
            </article>
          ))}
        </div>
        <section className="panel page-gap">
          <h2>任务队列</h2>
          <div className="task-list">
            <article className="task-item">
              <strong>标准化 douyin_video_raw</strong>
              <p className="muted">运行中 · 68%</p>
            </article>
            <article className="task-item">
              <strong>关联 ASR 口播文本</strong>
              <p className="muted">等待中</p>
            </article>
            <article className="task-item">
              <strong>写入 Milvus 向量库</strong>
              <p className="muted">等待中</p>
            </article>
          </div>
        </section>
      </section>
    </>
  );
}

export function SettingsPage() {
  return (
    <>
      <PageHeader title="设置" subtitle="配置工作区、平台账号、AI 风格、权限和采集策略" actions={<Button type="primary">保存设置</Button>} />
      <section className="panel">
        <div className="input-grid">
          <Input defaultValue="北极星内容组" aria-label="工作区名称" />
          <Select aria-label="模型路由" defaultValue="默认模型路由" options={[{ value: "默认模型路由" }]} />
          <Select aria-label="采集频率" defaultValue="采集频率：每 6 小时" options={[{ value: "采集频率：每 6 小时" }]} />
        </div>
        <h2 className="page-gap">AI 语气</h2>
        <TextArea defaultValue="克制、直接、给方法，不制造焦虑；避免“必爆”“全网最强”等夸张表达。" />
        <div className="chip-row page-gap-small">
          <Tag>禁用词：必爆</Tag>
          <Tag>品牌词：VO Mate</Tag>
          <Tag>CTA：关注后续路径</Tag>
        </div>
      </section>
    </>
  );
}

function BarList({ items }: { items: Array<[string, number]> }) {
  return (
    <div className="bar-list">
      {items.map(([label, value]) => (
        <div className="bar-row" key={label}>
          <span>{label}</span>
          <span className="bar-track">
            <span className="bar-fill" style={{ width: `${value}%` }} />
          </span>
          <strong>{value}</strong>
        </div>
      ))}
    </div>
  );
}
