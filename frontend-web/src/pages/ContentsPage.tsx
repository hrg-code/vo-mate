import { Button, Input, Select, Tag } from "antd";
import { ContentTable } from "../components/ContentTable";
import { PageHeader } from "../components/PageHeader";
import type { ContentItem } from "../types";

export function ContentsPage({ rows, onOpenEvidence }: { rows: ContentItem[]; onOpenEvidence: () => void }) {
  return (
    <>
      <PageHeader
        title="视频库"
        subtitle="统一查看多平台历史内容，筛选高潜力视频并进入复盘"
        actions={
          <>
            <Button>导入数据</Button>
            <Button type="primary" onClick={onOpenEvidence}>
              生成复盘
            </Button>
          </>
        }
      />
      <section className="panel">
        <div className="filter-bar">
          <Select
            aria-label="平台筛选"
            className="field compact"
            defaultValue="全部平台"
            options={[{ value: "全部平台" }, { value: "抖音" }, { value: "小红书" }]}
          />
          <Select
            aria-label="时间范围"
            className="field compact"
            defaultValue="近 30 天"
            options={[{ value: "近 30 天" }, { value: "近 90 天" }]}
          />
          <Input className="search-field" placeholder="搜索标题、标签、关键词" />
          <Tag.CheckableTag checked>有 ASR</Tag.CheckableTag>
          <Tag.CheckableTag checked={false}>未复盘</Tag.CheckableTag>
          <Tag.CheckableTag checked={false}>完播率 &gt; 30%</Tag.CheckableTag>
        </div>
        <ContentTable rows={rows} onOpenEvidence={onOpenEvidence} />
      </section>
    </>
  );
}
