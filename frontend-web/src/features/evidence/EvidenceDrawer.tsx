import { Drawer, Empty, Tag } from "antd";
import type { EvidenceItem } from "../../types";

export function EvidenceDrawer({
  open,
  items,
  onClose
}: {
  open: boolean;
  items: EvidenceItem[];
  onClose: () => void;
}) {
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
        <div className="evidence-list">
          {items.map((item) => (
            <article className="evidence-item" key={item.id}>
              <div className="panel-header tight">
                <Tag>{item.type}</Tag>
                {item.score ? <Tag color="success">{item.score}</Tag> : null}
              </div>
              <h3>{item.title}</h3>
              <p className="muted">{item.description}</p>
              <p className="source-line">{item.source}</p>
            </article>
          ))}
        </div>
      )}
    </Drawer>
  );
}
