import { useMemo, useState } from "react";
import { Alert, Button, Form, Input, InputNumber, Modal, Select, Statistic, Switch, Tag, message } from "antd";
import { Database, RefreshCw } from "lucide-react";
import { ContentTable } from "../components/ContentTable";
import { platformLabel } from "../components/format";
import { PageHeader } from "../components/PageHeader";
import type { CollectorImportRequest, CollectorImportResponse, ContentItem, Platform } from "../types";

type PlatformFilter = Platform | "all";
type TimeRangeFilter = "all" | "30d" | "90d";

type ContentsPageProps = {
  rows: ContentItem[];
  workspaceId: string;
  onImportContents: (payload: CollectorImportRequest) => Promise<CollectorImportResponse>;
  onOpenEvidence: () => void;
};

const platformOptions: { label: string; value: PlatformFilter }[] = [
  { label: "全部平台", value: "all" },
  ...Object.entries(platformLabel).map(([value, label]) => ({ label, value: value as Platform }))
];

const timeRangeOptions: { label: string; value: TimeRangeFilter }[] = [
  { label: "全部时间", value: "all" },
  { label: "近 30 天", value: "30d" },
  { label: "近 90 天", value: "90d" }
];

const importDefaults = {
  platform: "douyin" as Platform,
  collection: "douyin_video_raw",
  asrCollection: "douyin_video_asr_results",
  includeAsr: true,
  limit: 100
};

export function ContentsPage({ rows, workspaceId, onImportContents, onOpenEvidence }: ContentsPageProps) {
  const [form] = Form.useForm<CollectorImportRequest>();
  const [messageApi, contextHolder] = message.useMessage();
  const [platform, setPlatform] = useState<PlatformFilter>("all");
  const [timeRange, setTimeRange] = useState<TimeRangeFilter>("all");
  const [query, setQuery] = useState("");
  const [onlyAsr, setOnlyAsr] = useState(false);
  const [onlyUnreviewed, setOnlyUnreviewed] = useState(false);
  const [onlyHighCompletion, setOnlyHighCompletion] = useState(false);
  const [importOpen, setImportOpen] = useState(false);
  const [importing, setImporting] = useState(false);
  const [importResult, setImportResult] = useState<CollectorImportResponse | null>(null);
  const [importError, setImportError] = useState<string | null>(null);

  const filteredRows = useMemo(() => {
    const trimmedQuery = query.trim().toLowerCase();
    const newestTimestamp = Math.max(...rows.map((row) => Date.parse(row.publishedAt)).filter(Number.isFinite), Date.now());

    return rows.filter((row) => {
      if (platform !== "all" && row.platform !== platform) return false;
      if (onlyAsr && !row.hasAsr) return false;
      if (onlyUnreviewed && row.reviewed) return false;
      if (onlyHighCompletion && row.completionRate <= 0.3) return false;
      if (trimmedQuery && !row.title.toLowerCase().includes(trimmedQuery)) return false;
      if (timeRange === "all") return true;

      const publishedTimestamp = Date.parse(row.publishedAt);
      if (!Number.isFinite(publishedTimestamp)) return false;
      const maxAgeDays = timeRange === "30d" ? 30 : 90;
      return newestTimestamp - publishedTimestamp <= maxAgeDays * 24 * 60 * 60 * 1000;
    });
  }, [onlyAsr, onlyHighCompletion, onlyUnreviewed, platform, query, rows, timeRange]);

  const summary = useMemo(() => {
    const asrCount = rows.filter((row) => row.hasAsr).length;
    const unreviewedCount = rows.filter((row) => !row.reviewed).length;
    const highScoreCount = rows.filter((row) => row.score >= 80).length;
    return { asrCount, highScoreCount, total: rows.length, unreviewedCount };
  }, [rows]);

  const openImportModal = () => {
    setImportError(null);
    form.setFieldsValue({ workspaceId, ...importDefaults });
    setImportOpen(true);
  };

  const handleImport = async (values: CollectorImportRequest) => {
    setImporting(true);
    setImportError(null);
    try {
      const result = await onImportContents(values);
      setImportResult(result);
      setImportOpen(false);
      messageApi.success(`已入库 ${result.upsertedCount} 条视频`);
    } catch (error) {
      const reason = error instanceof Error ? error.message : "视频入库失败";
      setImportError(reason);
      messageApi.error(reason);
    } finally {
      setImporting(false);
    }
  };

  return (
    <>
      {contextHolder}
      <PageHeader
        title="视频库"
        subtitle="统一查看多平台历史内容，筛选高潜力视频并进入复盘"
        actions={
          <>
            <Button icon={<Database size={16} />} onClick={openImportModal}>
              导入数据
            </Button>
            <Button type="primary" onClick={onOpenEvidence}>
              生成复盘
            </Button>
          </>
        }
      />

      {importResult ? (
        <Alert
          className="page-gap-small"
          type={importResult.failedCount > 0 ? "warning" : "success"}
          showIcon
          closable
          onClose={() => setImportResult(null)}
          message={`入库完成：处理 ${importResult.processedCount} 条，写入 ${importResult.upsertedCount} 条，失败 ${importResult.failedCount} 条`}
          description={`文本资产 ${importResult.textAssetCount}，标签 ${importResult.tagCount}，关键词 ${importResult.keywordCount}，流量来源 ${importResult.trafficSourceCount}，ASR ${importResult.asrCount}。`}
        />
      ) : null}

      <section className="content-summary-grid">
        <Statistic title="当前视频" value={summary.total} />
        <Statistic title="高评分" value={summary.highScoreCount} suffix="条" />
        <Statistic title="有 ASR" value={summary.asrCount} suffix="条" />
        <Statistic title="待复盘" value={summary.unreviewedCount} suffix="条" />
      </section>

      <section className="panel">
        <div className="filter-bar">
          <Select
            aria-label="平台筛选"
            className="field compact"
            options={platformOptions}
            value={platform}
            onChange={setPlatform}
          />
          <Select
            aria-label="时间范围"
            className="field compact"
            options={timeRangeOptions}
            value={timeRange}
            onChange={setTimeRange}
          />
          <Input
            allowClear
            className="search-field"
            placeholder="搜索标题"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
          />
          <Tag.CheckableTag checked={onlyAsr} onChange={setOnlyAsr}>
            有 ASR
          </Tag.CheckableTag>
          <Tag.CheckableTag checked={onlyUnreviewed} onChange={setOnlyUnreviewed}>
            未复盘
          </Tag.CheckableTag>
          <Tag.CheckableTag checked={onlyHighCompletion} onChange={setOnlyHighCompletion}>
            完播率 &gt; 30%
          </Tag.CheckableTag>
          <Button
            icon={<RefreshCw size={15} />}
            onClick={() => {
              setPlatform("all");
              setTimeRange("all");
              setQuery("");
              setOnlyAsr(false);
              setOnlyUnreviewed(false);
              setOnlyHighCompletion(false);
            }}
          >
            重置
          </Button>
        </div>
        <ContentTable rows={filteredRows} onOpenEvidence={onOpenEvidence} />
      </section>

      <Modal
        destroyOnHidden
        okText="开始入库"
        open={importOpen}
        title="导入 Raw 视频数据"
        confirmLoading={importing}
        onCancel={() => setImportOpen(false)}
        onOk={() => form.submit()}
      >
        <Form<CollectorImportRequest>
          form={form}
          layout="vertical"
          initialValues={{ workspaceId, ...importDefaults }}
          onFinish={handleImport}
        >
          {importError ? <Alert className="modal-alert" type="error" showIcon message={importError} /> : null}
          <Form.Item name="workspaceId" label="工作区 ID" rules={[{ required: true, message: "请输入工作区 ID" }]}>
            <Input />
          </Form.Item>
          <Form.Item name="platform" label="平台" rules={[{ required: true, message: "请选择平台" }]}>
            <Select options={[{ label: platformLabel.douyin, value: "douyin" }]} />
          </Form.Item>
          <Form.Item name="collection" label="Raw 集合" rules={[{ required: true, message: "请输入 Raw 集合名" }]}>
            <Input />
          </Form.Item>
          <Form.Item name="asrCollection" label="ASR 集合" rules={[{ required: true, message: "请输入 ASR 集合名" }]}>
            <Input />
          </Form.Item>
          <div className="import-form-grid">
            <Form.Item name="limit" label="导入上限" rules={[{ required: true, message: "请输入导入上限" }]}>
              <InputNumber min={1} max={1000} precision={0} className="full-width" />
            </Form.Item>
            <Form.Item name="includeAsr" label="包含 ASR" valuePropName="checked">
              <Switch checkedChildren="是" unCheckedChildren="否" />
            </Form.Item>
          </div>
        </Form>
      </Modal>
    </>
  );
}
