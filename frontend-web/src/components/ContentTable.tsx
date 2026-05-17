import { Button, Table, Tag } from "antd";
import type { TableColumnsType } from "antd";
import { compactNumber, percent, platformLabel } from "./format";
import type { ContentItem } from "../types";

const statusLabel: Record<ContentItem["status"], string> = {
  published: "已发布",
  needs_review: "待复盘",
  script_reusable: "脚本可复用",
  seo_opportunity: "高搜索"
};

export function ContentTable({
  loading = false,
  rows,
  onOpenEvidence
}: {
  loading?: boolean;
  rows: ContentItem[];
  onOpenEvidence: () => void;
}) {
  const columns: TableColumnsType<ContentItem> = [
    {
      title: "内容",
      dataIndex: "title",
      fixed: "left",
      width: 300,
      sorter: (a, b) => a.title.localeCompare(b.title),
      render: (_, row) => (
        <div className="video-cell">
          <span className={`cover platform-${row.platform}`} aria-hidden="true" />
          <strong>{row.title}</strong>
        </div>
      )
    },
    {
      title: "平台",
      dataIndex: "platform",
      width: 96,
      filters: Object.entries(platformLabel).map(([value, text]) => ({ value, text })),
      onFilter: (value, row) => row.platform === value,
      render: (_, row) => <Tag className={`platform-tag platform-${row.platform}`}>{platformLabel[row.platform]}</Tag>
    },
    {
      title: "发布",
      dataIndex: "publishedAt",
      width: 112,
      sorter: (a, b) => Date.parse(a.publishedAt) - Date.parse(b.publishedAt)
    },
    {
      title: "时长",
      dataIndex: "durationSeconds",
      width: 82,
      sorter: (a, b) => a.durationSeconds - b.durationSeconds,
      render: (value: ContentItem["durationSeconds"]) => `${value}s`
    },
    {
      title: "播放",
      dataIndex: "views",
      width: 92,
      sorter: (a, b) => a.views - b.views,
      render: (value: ContentItem["views"]) => compactNumber(value)
    },
    {
      title: "点赞",
      dataIndex: "likes",
      width: 92,
      sorter: (a, b) => a.likes - b.likes,
      render: (value: ContentItem["likes"]) => compactNumber(value)
    },
    {
      title: "评论",
      dataIndex: "comments",
      width: 92,
      sorter: (a, b) => a.comments - b.comments,
      render: (value: ContentItem["comments"]) => compactNumber(value)
    },
    {
      title: "收藏",
      dataIndex: "saves",
      width: 92,
      sorter: (a, b) => a.saves - b.saves,
      render: (value: ContentItem["saves"]) => compactNumber(value)
    },
    {
      title: "完播",
      dataIndex: "completionRate",
      width: 92,
      sorter: (a, b) => a.completionRate - b.completionRate,
      render: (value: ContentItem["completionRate"]) => percent(value)
    },
    {
      title: "涨粉",
      dataIndex: "followersGained",
      width: 92,
      sorter: (a, b) => a.followersGained - b.followersGained,
      render: (value: ContentItem["followersGained"]) => compactNumber(value)
    },
    {
      title: "评分",
      dataIndex: "score",
      width: 82,
      sorter: (a, b) => a.score - b.score,
      render: (value: ContentItem["score"]) => (
        <Tag color={value >= 80 ? "success" : "warning"} className="score-tag">
          {value}
        </Tag>
      )
    },
    {
      title: "状态",
      dataIndex: "status",
      width: 112,
      render: (value: ContentItem["status"]) => statusLabel[value]
    },
    {
      title: "操作",
      key: "action",
      fixed: "right",
      width: 92,
      render: () => (
        <Button type="link" onClick={onOpenEvidence}>
          复盘
        </Button>
      )
    }
  ];

  return (
    <Table
      columns={columns}
      dataSource={rows}
      loading={loading}
      locale={{ emptyText: "暂无匹配视频" }}
      pagination={{ pageSize: 10, showSizeChanger: false }}
      rowKey="id"
      scroll={{ x: 1240 }}
      size="middle"
    />
  );
}
