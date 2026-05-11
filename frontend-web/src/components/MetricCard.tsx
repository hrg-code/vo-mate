import type { MetricSummary } from "../types";

const bars = [42, 58, 49, 65, 77, 62, 88, 79, 92, 84];

export function MetricCard({ metric }: { metric: MetricSummary }) {
  return (
    <article className="metric-card">
      <div className="metric-label">
        <span>{metric.label}</span>
        <span className={`delta ${metric.direction}`}>{metric.delta}</span>
      </div>
      <div className="metric-value">{metric.value}</div>
      <p className="muted">{metric.description}</p>
      <div className="mini-bars" aria-hidden="true">
        {bars.map((height, index) => (
          <span key={index} style={{ height: `${height}%` }} />
        ))}
      </div>
    </article>
  );
}
