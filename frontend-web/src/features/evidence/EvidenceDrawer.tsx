import { BarChart3, Brain, Database, History, Search, SlidersHorizontal, Users } from "lucide-react";
import { Drawer, Empty, Tag } from "antd";
import type { ReactNode } from "react";
import type { EvidenceItem } from "../../types";

const evidenceMeta: Record<
  EvidenceItem["type"],
  { label: string; description: string; icon: ReactNode; color: string }
> = {
  content: {
    label: "历史内容",
    description: "相似选题、爆款结构和低效反例",
    icon: <History size={16} />,
    color: "blue"
  },
  metric: {
    label: "指标",
    description: "播放、完播、互动、涨粉等表现信号",
    icon: <BarChart3 size={16} />,
    color: "green"
  },
  keyword: {
    label: "关键词",
    description: "搜索、标签和评论热词机会",
    icon: <Search size={16} />,
    color: "gold"
  },
  audience: {
    label: "受众",
    description: "核心受众、粉丝兴趣和平台人群匹配",
    icon: <Users size={16} />,
    color: "cyan"
  },
  memory: {
    label: "记忆模式",
    description: "已验证的成功结构和避坑经验",
    icon: <Brain size={16} />,
    color: "purple"
  },
  constraint: {
    label: "用户约束",
    description: "目标、平台、时长、语气和禁区",
    icon: <SlidersHorizontal size={16} />,
    color: "default"
  },
  raw: {
    label: "原始诊断",
    description: "召回链路、数据源和兜底状态",
    icon: <Database size={16} />,
    color: "default"
  }
};

const evidenceOrder: EvidenceItem["type"][] = ["content", "metric", "keyword", "audience", "memory", "constraint", "raw"];

export function EvidenceDrawer({
  open,
  items,
  onClose
}: {
  open: boolean;
  items: EvidenceItem[];
  onClose: () => void;
}) {
  const groupedItems = evidenceOrder
    .map((type) => ({ type, items: items.filter((item) => item.type === type) }))
    .filter((group) => group.items.length > 0);

  return (
    <Drawer
      aria-label="AI 建议依据"
      className="evidence-drawer"
      onClose={onClose}
      open={open}
      title={
        <div>
          <p className="eyebrow">Evidence Drawer</p>
          <span>AI 建议依据</span>
        </div>
      }
      width={460}
    >
      {items.length === 0 ? (
        <Empty description="暂无依据" />
      ) : (
        <div className="evidence-drawer-body">
          <div className="evidence-summary">
            <strong>{items.length} 条依据</strong>
            <span>用于解释选题推荐、预测分和风险判断。</span>
          </div>
          {groupedItems.map((group) => {
            const meta = evidenceMeta[group.type];
            return (
              <section className="evidence-group" key={group.type}>
                <div className="evidence-group-header">
                  <div className="evidence-group-title">
                    <span className="evidence-group-icon">{meta.icon}</span>
                    <div>
                      <h3>{meta.label}</h3>
                      <p>{meta.description}</p>
                    </div>
                  </div>
                  <Tag>{group.items.length}</Tag>
                </div>
                <div className="evidence-list">
                  {group.items.map((item) => (
                    <article className="evidence-item" key={item.id}>
                      <div className="panel-header tight">
                        <Tag color={meta.color}>{meta.label}</Tag>
                        {item.score ? <Tag color="success">{item.score}</Tag> : null}
                      </div>
                      <h4>{item.title}</h4>
                      <p className="muted">{item.description}</p>
                      {item.metrics?.length ? (
                        <div className="evidence-metrics">
                          {item.metrics.map((metric) => (
                            <Tag key={metric}>{metric}</Tag>
                          ))}
                        </div>
                      ) : null}
                      {item.action ? <p className="evidence-action">{item.action}</p> : null}
                      <p className="source-line">{item.source}</p>
                    </article>
                  ))}
                </div>
              </section>
            );
          })}
        </div>
      )}
    </Drawer>
  );
}
