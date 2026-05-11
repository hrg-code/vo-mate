import { Alert, Button, Input, Select, Tag } from "antd";
import { useState } from "react";
import { PageHeader } from "../components/PageHeader";
import { platformLabel } from "../components/format";
import type { Platform, TopicIdea, TopicIdeaGenerateRequest } from "../types";

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
  onOpenEvidence: () => void;
  onCreateScript: () => void;
}) {
  const [direction, setDirection] = useState("程序员 35 岁危机");
  const [goal, setGoal] = useState("followers");
  const [duration, setDuration] = useState(60);
  const [platforms, setPlatforms] = useState<Platform[]>(["douyin", "xiaohongshu"]);

  const generate = () => {
    onGenerate({
      direction,
      platforms,
      goal,
      constraints: {
        targetDurationSeconds: duration,
        tone: "克制直接",
        useHotSignals: true
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
            <div className="input-grid">
              <Input
                aria-label="探索方向"
                onChange={(event) => setDirection(event.target.value)}
                placeholder="输入想探索的选题方向"
                value={direction}
              />
              <Select
                aria-label="目标"
                onChange={setGoal}
                options={[
                  { label: "目标：涨粉", value: "followers" },
                  { label: "目标：搜索", value: "search" },
                  { label: "目标：互动", value: "engagement" }
                ]}
                value={goal}
              />
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
            </div>
            <div className="chip-row page-gap-small">
              {platforms.map((platform) => (
                <Tag className={`platform-tag platform-${platform}`} key={platform}>
                  {platformLabel[platform]}
                </Tag>
              ))}
              <Tag>参考热点</Tag>
              <Tag>账号风格：克制直接</Tag>
            </div>
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
                    <Button type="primary" onClick={onCreateScript}>
                      生成脚本
                    </Button>
                    <Button onClick={onOpenEvidence}>查看依据</Button>
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
          <Button onClick={onOpenEvidence}>查看完整依据</Button>
        </aside>
      </div>
    </>
  );
}
