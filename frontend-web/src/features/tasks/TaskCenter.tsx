import { Progress, Tag } from "antd";
import type { AgentTask } from "../../types";

export function TaskCenter({ tasks }: { tasks: AgentTask[] }) {
  return (
    <section className="panel task-center">
      <div className="panel-header">
        <div>
          <p className="eyebrow">Async Workflows</p>
          <h2>任务中心</h2>
        </div>
        <Tag color="warning">{tasks.filter((task) => task.status === "running").length} 运行中</Tag>
      </div>
      <div className="task-list">
        {tasks.map((task) => (
          <article className="task-item" key={task.id}>
            <div className="panel-header tight">
              <strong>{task.name}</strong>
              <Tag className={`status-tag ${task.status}`}>{task.status}</Tag>
            </div>
            <p className="muted">{task.currentStep}</p>
            <Progress percent={task.progress} size="small" />
            <p className="source-line">{task.traceId}</p>
          </article>
        ))}
      </div>
    </section>
  );
}
