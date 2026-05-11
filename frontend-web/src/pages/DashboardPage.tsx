import { Button, Segmented } from "antd";
import { ContentTable } from "../components/ContentTable";
import { MetricCard } from "../components/MetricCard";
import { PageHeader } from "../components/PageHeader";
import { TaskCenter } from "../features/tasks/TaskCenter";
import type { AgentTask, ContentItem, MetricSummary } from "../types";

export function DashboardPage({
  metrics,
  contents,
  tasks,
  onOpenEvidence,
  onNavigateTopics
}: {
  metrics: MetricSummary[];
  contents: ContentItem[];
  tasks: AgentTask[];
  onOpenEvidence: () => void;
  onNavigateTopics: () => void;
}) {
  return (
    <>
      <PageHeader
        title="首页"
        subtitle="30 秒内看到账号表现、异常和今天最值得推进的内容动作"
        actions={
          <>
            <Button>同步数据</Button>
            <Button type="primary" onClick={onNavigateTopics}>
              生成今日选题
            </Button>
          </>
        }
      />
      <div className="layout-grid">
        <section>
          <div className="metric-grid">
            {metrics.map((metric) => (
              <MetricCard metric={metric} key={metric.label} />
            ))}
          </div>
          <div className="dashboard-grid">
            <section className="panel">
              <div className="panel-header">
                <div>
                  <h2>表现趋势</h2>
                  <p className="muted">近 12 日播放与搜索流量</p>
                </div>
                <Segmented defaultValue="7 日" options={["7 日", "30 日", "90 日"]} />
              </div>
              <div className="trend-chart" aria-label="播放与搜索流量趋势">
                {[42, 58, 46, 61, 72, 64, 78, 69, 84, 76, 91, 88].map((height, index) => (
                  <div className="trend-column" key={index}>
                    <span className="plays" style={{ height: `${height}%` }} />
                    <span className="search" style={{ height: `${Math.max(20, height - 28)}%` }} />
                    <small>{index + 1}</small>
                  </div>
                ))}
              </div>
              <div className="legend"><span>播放</span><span>搜索流量</span></div>
            </section>
            <section className="panel">
              <h2>今日 AI 建议</h2>
              <div className="action-list">
                <article className="action-item">
                  <strong>继续承接 35 岁程序员话题</strong>
                  <p className="muted">预测播放 28w-41w，建议先生成 60 秒脚本。</p>
                </article>
                <article className="action-item">
                  <strong>复盘完播率下降视频</strong>
                  <p className="muted">前 5 秒留存低于账号中位数 11%。</p>
                </article>
                <article className="action-item">
                  <strong>补充小红书搜索标题</strong>
                  <p className="muted">“转码成本”“AI 程序员”搜索机会上升。</p>
                </article>
              </div>
            </section>
          </div>
          <section className="panel page-gap">
            <div className="panel-header">
              <h2>最近内容</h2>
              <Button>查看全部</Button>
            </div>
            <ContentTable rows={contents} onOpenEvidence={onOpenEvidence} />
          </section>
        </section>
        <TaskCenter tasks={tasks} />
      </div>
    </>
  );
}
