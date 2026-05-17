import { Alert, Button, Input, InputNumber, Select, Tag } from "antd";
import { useState } from "react";
import { PageHeader } from "../components/PageHeader";
import { platformLabel } from "../components/format";
import type { EvidenceQuery, Platform, TopicIdea, TopicIdeaGenerateRequest } from "../types";

const { TextArea } = Input;

const defaultConstraintsText = JSON.stringify(
  {
    tone: "克制直接",
    avoidTopics: ["裁员恐慌"],
    useHotSignals: true
  },
  null,
  2
);

export function TopicsPage({
  topics,
  generationError,
  generationLoading,
  generationProgress,
  onGenerate,
  onOpenEvidence,
  onCreateScript
}: {
  topics: TopicIdea[];
  generationError: string | null;
  generationLoading: boolean;
  generationProgress: string;
  onGenerate: (payload: TopicIdeaGenerateRequest) => void;
  onOpenEvidence: (query?: EvidenceQuery) => void;
  onCreateScript: (topic: TopicIdea, durationSeconds: number) => void;
}) {
  const [direction, setDirection] = useState("程序员 35 岁危机");
  const [goal, setGoal] = useState("followers");
  const [count, setCount] = useState(10);
  const [audience, setAudience] = useState("25-35 岁普通程序员");
  const [duration, setDuration] = useState(60);
  const [platforms, setPlatforms] = useState<Platform[]>(["douyin", "xiaohongshu"]);
  const [constraintsText, setConstraintsText] = useState(defaultConstraintsText);
  const [formError, setFormError] = useState<string | null>(null);

  const generate = () => {
    const trimmedDirection = direction.trim();
    if (!trimmedDirection) {
      setFormError("选题方向不能为空，请先填写生成主题。");
      return;
    }

    let constraints: Record<string, unknown>;
    try {
      const parsed = JSON.parse(constraintsText || "{}") as unknown;
      if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) {
        setFormError("生成约束必须是 JSON 对象，例如 {\"tone\":\"理性但有冲突感\"}。");
        return;
      }
      constraints = parsed as Record<string, unknown>;
    } catch {
      setFormError("生成约束不是合法 JSON，请检查引号、逗号和括号。");
      return;
    }

    setFormError(null);
    onGenerate({
      direction: trimmedDirection,
      platforms,
      goal,
      count,
      audience: audience.trim() || undefined,
      constraints: {
        ...constraints,
        targetDurationSeconds: duration,
      }
    });
  };

  return (
    <>
      <PageHeader
        title="选题雷达"
        subtitle="从历史数据、ASR、搜索词和记忆库中生成可拍选题"
        actions={
          <Button loading={generationLoading} onClick={generate} type="primary">
            生成选题
          </Button>
        }
      />
      <div className="layout-grid">
        <section>
          <section className="panel">
            <div className="topic-generate-grid">
              <label className="form-field form-field-wide">
                <span>选题方向</span>
                <Input
                  aria-label="选题方向"
                  onChange={(event) => setDirection(event.target.value)}
                  placeholder="比如：程序员职业成长"
                  value={direction}
                />
              </label>
              <label className="form-field">
                <span>生成数量</span>
                <InputNumber
                  aria-label="生成数量"
                  className="full-width"
                  max={20}
                  min={1}
                  onChange={(value) => setCount(typeof value === "number" ? value : 1)}
                  precision={0}
                  value={count}
                />
              </label>
              <label className="form-field">
                <span>目标</span>
                <Select
                  aria-label="目标"
                  onChange={setGoal}
                  options={[
                    { label: "涨粉", value: "followers" },
                    { label: "搜索", value: "search" },
                    { label: "互动", value: "engagement" }
                  ]}
                  value={goal}
                />
              </label>
              <label className="form-field form-field-wide">
                <span>目标受众</span>
                <Input
                  aria-label="目标受众"
                  onChange={(event) => setAudience(event.target.value)}
                  placeholder="比如：25-35 岁普通程序员"
                  value={audience}
                />
              </label>
              <label className="form-field">
                <span>视频时长</span>
                <Select
                  aria-label="时长"
                  onChange={setDuration}
                  options={[
                    { label: "60 秒", value: 60 },
                    { label: "30 秒", value: 30 },
                    { label: "90 秒", value: 90 }
                  ]}
                  value={duration}
                />
              </label>
              <label className="form-field">
                <span>目标平台</span>
                <Select
                  aria-label="目标平台"
                  mode="multiple"
                  onChange={setPlatforms}
                  options={[
                    { label: "抖音", value: "douyin" },
                    { label: "小红书", value: "xiaohongshu" },
                    { label: "视频号", value: "wechat" },
                    { label: "YouTube", value: "youtube" }
                  ]}
                  value={platforms}
                />
              </label>
              <label className="form-field form-field-full">
                <span>生成约束 JSON</span>
                <TextArea
                  aria-label="生成约束 JSON"
                  autoSize={{ minRows: 4, maxRows: 8 }}
                  onChange={(event) => setConstraintsText(event.target.value)}
                  placeholder='例如：{"tone":"理性但有冲突感","avoidTopics":["裁员恐慌"]}'
                  value={constraintsText}
                />
              </label>
            </div>
            <div className="chip-row page-gap-small">
              {platforms.map((platform) => (
                <Tag className={`platform-tag platform-${platform}`} key={platform}>
                  {platformLabel[platform]}
                </Tag>
              ))}
              <Tag>{count} 个候选</Tag>
              {audience.trim() ? <Tag>受众：{audience.trim()}</Tag> : null}
              <Tag>参考热点</Tag>
            </div>
            {formError ? <Alert className="page-gap-small" message={formError} showIcon type="warning" /> : null}
            {generationProgress ? (
              <Alert className="page-gap-small" message={generationProgress} showIcon type="info" />
            ) : null}
            {generationError ? (
              <Alert className="page-gap-small" message={generationError} showIcon type="error" />
            ) : null}
          </section>
          <div className="topic-list page-gap">
            {topics.map((topic) => (
              <article className="topic-card" key={topic.id}>
                <div>
                  <div className="chip-row">
                    <Tag color="success">预测高</Tag>
                    <Tag>参考 {topic.evidenceCount} 条历史内容</Tag>
                  </div>
                  <h2>{topic.title}</h2>
                  <p className="muted">{topic.angle}</p>
                  <div className="topic-meta">
                    <Tag>SEO {topic.seoScore}</Tag>
                    <Tag>受众 {topic.audienceScore}</Tag>
                    <Tag>难度 {topic.difficultyScore}</Tag>
                    <Tag color="error">{topic.risk}</Tag>
                    {topic.targetPlatforms.map((platform) => (
                      <Tag className={`platform-tag platform-${platform}`} key={platform}>
                        {platformLabel[platform]}
                      </Tag>
                    ))}
                  </div>
                  <div className="button-row page-gap-small">
                    <Button type="primary" onClick={() => onCreateScript(topic, duration)}>
                      生成脚本
                    </Button>
                    <Button onClick={() => onOpenEvidence(topic.generationId ? { generationId: topic.generationId, limit: 20 } : undefined)}>
                      查看依据
                    </Button>
                  </div>
                </div>
                <div className="score-box">{topic.predictedScore}</div>
              </article>
            ))}
          </div>
        </section>
        <aside className="panel ai-panel">
          <div className="panel-header">
            <div>
              <p className="eyebrow">Retrieval + Scoring</p>
              <h2>评分依据</h2>
            </div>
            <Tag color="success">可信度 86</Tag>
          </div>
          <p>系统已检索 26 条相似历史内容，其中“职业转折 + 明确步骤”的结构表现最稳定。</p>
          <div className="confidence">
            <div className="confidence-track"><span style={{ width: "86%" }} /></div>
            <strong>86%</strong>
          </div>
          <div className="evidence-factor-list">
            {[
              ["历史内容", "相似爆款与低效反例", "强"],
              ["指标", "完播、互动、涨粉贡献", "强"],
              ["关键词", "搜索词和评论热词", "中"],
              ["受众", "核心粉丝兴趣匹配", "强"],
              ["记忆模式", "已验证开头和结构", "中"],
              ["用户约束", "平台、时长、语气、禁区", "已应用"]
            ].map(([name, description, level]) => (
              <div className="evidence-factor" key={name}>
                <div>
                  <strong>{name}</strong>
                  <span>{description}</span>
                </div>
                <Tag>{level}</Tag>
              </div>
            ))}
          </div>
          <Button onClick={() => onOpenEvidence()}>查看完整依据</Button>
        </aside>
      </div>
    </>
  );
}
