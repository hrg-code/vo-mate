import { Button, Input, Select, Tabs, Tag } from "antd";
import { PageHeader } from "../components/PageHeader";
import { platformLabel } from "../components/format";
import type { MemoryPattern, PublishPlan } from "../types";

const { TextArea } = Input;

export function AudiencePage() {
  return (
    <>
      <PageHeader
        title="粉丝画像"
        subtitle="理解粉丝是谁、何时活跃、喜欢什么"
        actions={<Button type="primary">生成画像洞察</Button>}
      />
      <div className="dashboard-grid">
        <section className="panel">
          <h2>兴趣分布</h2>
          <BarList items={[["职场成长", 82], ["AI 工具", 74], ["面试求职", 67], ["副业转型", 48]]} />
        </section>
        <section className="panel">
          <h2>活跃时间</h2>
          <div className="heatmap">
            {Array.from({ length: 28 }, (_, index) => (
              <span className="heat-cell" style={{ opacity: 0.25 + (index % 7) * 0.1 }} key={index} />
            ))}
          </div>
        </section>
      </div>
    </>
  );
}

export function ScriptsPage({
  onNavigateSeo,
  onOpenEvidence
}: {
  onNavigateSeo: () => void;
  onOpenEvidence: () => void;
}) {
  return (
    <>
      <PageHeader
        title="脚本工作台"
        subtitle="把选题转为可拍、可改、可发布的口播内容"
        actions={
          <>
            <Button>保存草稿</Button>
            <Button type="primary" onClick={onNavigateSeo}>
              生成 SEO
            </Button>
          </>
        }
      />
      <section className="split-page">
        <aside className="panel">
          <h2>当前选题</h2>
          <p>
            <strong>35 岁程序员不是危机，是岗位切换信号</strong>
          </p>
          <p className="muted">参考 12 条历史内容，推荐 60 秒结构。</p>
          <h3>版本</h3>
          <div className="action-list">
            <article className="action-item">
              <strong>v1 AI 初稿</strong>
              <p className="muted">10:42 生成</p>
            </article>
            <article className="action-item">
              <strong>v2 抖音版</strong>
              <p className="muted">强化开头钩子</p>
            </article>
          </div>
        </aside>

        <section className="panel script-editor">
          <div className="panel-header">
            <h2>口播脚本</h2>
            <Tag color="success">预计 58 秒</Tag>
          </div>
          <TextArea
            className="script-textarea"
            defaultValue={
              "开头 3 秒：\n如果你担心 35 岁以后写不动代码，先别急着否定自己。\n\n主体：\n真正的问题不是年龄，而是你还停留在“只接需求”的岗位形态里。35 岁以后，企业更需要的是能拆问题、控风险、带人交付的人。\n\n转折：\n所以这不是退出信号，而是岗位切换信号。\n\n结尾 CTA：\n如果你想知道怎么从执行型程序员转到方案型角色，我下一条讲具体路径。"
            }
          />
          <div className="word-count">
            <span>字数 226</span>
            <span>结构：钩子 / 解释 / 转折 / CTA</span>
          </div>
        </section>

        <aside className="panel">
          <h2>AI Copilot</h2>
          <div className="task-list">
            <Button>改强开头</Button>
            <Button>缩短到 30 秒</Button>
            <Button>加真实案例</Button>
            <Button>转小红书口吻</Button>
          </div>
          <div className="evidence-list page-gap">
            <article className="evidence-item">
              <strong>当前判断</strong>
              <p className="muted">开头清晰，但中段案例不足，建议加入一条真实项目场景。</p>
            </article>
            <Button onClick={onOpenEvidence}>查看依据</Button>
          </div>
        </aside>
      </section>
    </>
  );
}

export function SeoPage({ onNavigateCalendar }: { onNavigateCalendar: () => void }) {
  return (
    <>
      <PageHeader
        title="SEO 优化"
        subtitle="生成平台适配标题、简介、标签与关键词布局"
        actions={
          <Button type="primary" onClick={onNavigateCalendar}>
            加入发布计划
          </Button>
        }
      />
      <section className="panel">
        <Tabs
          defaultActiveKey="douyin"
          items={[
            { key: "douyin", label: "抖音" },
            { key: "xiaohongshu", label: "小红书" },
            { key: "youtube", label: "YouTube Shorts" },
            { key: "wechat", label: "视频号" }
          ]}
        />
        <h2>标题实验</h2>
        <div className="action-list">
          <article className="action-item">
            <div className="panel-header tight">
              <strong>35 岁程序员最该换的不是行业，而是岗位形态</strong>
              <Tag color="success">92</Tag>
            </div>
            <p className="muted">覆盖关键词：35 岁、程序员、岗位、转型</p>
          </article>
          <article className="action-item">
            <div className="panel-header tight">
              <strong>程序员 35 岁危机，其实是一个误解</strong>
              <Tag color="warning">78</Tag>
            </div>
            <p className="muted">冲突明确，但搜索词覆盖偏弱。</p>
          </article>
        </div>
        <h2 className="page-gap">简介</h2>
        <TextArea defaultValue="这条视频聊程序员 35 岁后的职业切换：从只写代码，到能拆问题、控风险、交付方案。" />
        <div className="chip-row page-gap-small">
          <Tag>#程序员</Tag>
          <Tag>#35岁危机</Tag>
          <Tag>#AI时代</Tag>
          <Tag>#职场成长</Tag>
        </div>
      </section>
    </>
  );
}

export function CalendarPage({ plans }: { plans: PublishPlan[] }) {
  const stages: PublishPlan["stage"][] = ["idea", "script", "editing", "ready"];
  const labels: Record<PublishPlan["stage"], string> = {
    idea: "灵感",
    script: "已生成脚本",
    shooting: "待拍摄",
    editing: "待剪辑",
    ready: "待发布",
    published: "已发布"
  };

  return (
    <>
      <PageHeader title="发布日历" subtitle="管理内容从脚本到发布的计划" actions={<Button type="primary">新建计划</Button>} />
      <section className="kanban">
        {stages.map((stage) => (
          <div className="kanban-column" key={stage}>
            <h3>{labels[stage]}</h3>
            {plans
              .filter((plan) => plan.stage === stage)
              .map((plan) => (
                <article className="calendar-item" key={plan.id}>
                  <Tag className={`platform-tag platform-${plan.platform}`}>{platformLabel[plan.platform]}</Tag>
                  <h3>{plan.title}</h3>
                  <p className="muted">{plan.scheduledAt}</p>
                </article>
              ))}
          </div>
        ))}
      </section>
    </>
  );
}

export function RetrospectivesPage({ onOpenEvidence }: { onOpenEvidence: () => void }) {
  return (
    <>
      <PageHeader
        title="复盘中心"
        subtitle="管理单条视频复盘、周期报告和可沉淀经验"
        actions={
          <Button type="primary" onClick={onOpenEvidence}>
            生成周报
          </Button>
        }
      />
      <section className="panel">
        <Tabs
          defaultActiveKey="single"
          items={[
            { key: "single", label: "单条视频" },
            { key: "weekly", label: "周报" },
            { key: "monthly", label: "月报" },
            { key: "patterns", label: "模式" }
          ]}
        />
        <div className="action-list">
          <article className="action-item">
            <h2>程序员 35 岁后还能不能继续写代码</h2>
            <p className="muted">结论：开头问题命中强，但中段缺少反例，评论转化高于收藏。</p>
            <div className="button-row">
              <Button type="primary">写入记忆库</Button>
              <Button>驳回结论</Button>
            </div>
          </article>
          <article className="action-item">
            <h2>为什么你的简历总被 HR 刷掉</h2>
            <p className="muted">结论：标题搜索价值高，完播稳定，适合承接面试系列。</p>
            <Button onClick={onOpenEvidence}>查看依据</Button>
          </article>
        </div>
      </section>
    </>
  );
}

export function MemoryPage({ memories }: { memories: MemoryPattern[] }) {
  return (
    <>
      <PageHeader title="记忆库" subtitle="查看、确认、降低权重或删除系统学到的经验" actions={<Button type="primary">审核候选记忆</Button>} />
      <section className="memory-grid">
        {memories.map((memory) => (
          <article className="memory-card" key={memory.id}>
            <Tag>{memory.type}</Tag>
            <h2>{memory.summary}</h2>
            <p className="muted">
              权重 {memory.confidence} · 来源 {memory.sourceCount} 条内容 · {memory.lastVerifiedAt}
            </p>
            <div className="button-row">
              <Button type="primary">确认</Button>
              <Button>降权</Button>
              <Button danger>删除</Button>
            </div>
          </article>
        ))}
      </section>
    </>
  );
}

export function CollectorPage() {
  return (
    <>
      <PageHeader
        title="采集管理"
        subtitle="管理 Electron、浏览器插件、手动导入与采集任务状态"
        actions={
          <>
            <Button>手动导入</Button>
            <Button type="primary">立即同步</Button>
          </>
        }
      />
      <section>
        <div className="connector-grid">
          {["抖音", "快手", "小红书", "YouTube", "视频号"].map((name, index) => (
            <article className="connector" key={name}>
              <span className="status-dot" />
              <h2>{name}</h2>
              <p className="muted">{index === 0 ? "已连接，2 分钟前同步" : "待配置采集方式"}</p>
            </article>
          ))}
        </div>
        <section className="panel page-gap">
          <h2>任务队列</h2>
          <div className="task-list">
            <article className="task-item">
              <strong>标准化 douyin_video_raw</strong>
              <p className="muted">运行中 · 68%</p>
            </article>
            <article className="task-item">
              <strong>关联 ASR 口播文本</strong>
              <p className="muted">等待中</p>
            </article>
            <article className="task-item">
              <strong>写入 Milvus 向量库</strong>
              <p className="muted">等待中</p>
            </article>
          </div>
        </section>
      </section>
    </>
  );
}

export function SettingsPage() {
  return (
    <>
      <PageHeader title="设置" subtitle="配置工作区、平台账号、AI 风格、权限和采集策略" actions={<Button type="primary">保存设置</Button>} />
      <section className="panel">
        <div className="input-grid">
          <Input defaultValue="北极星内容组" aria-label="工作区名称" />
          <Select aria-label="模型路由" defaultValue="默认模型路由" options={[{ value: "默认模型路由" }]} />
          <Select aria-label="采集频率" defaultValue="采集频率：每 6 小时" options={[{ value: "采集频率：每 6 小时" }]} />
        </div>
        <h2 className="page-gap">AI 语气</h2>
        <TextArea defaultValue="克制、直接、给方法，不制造焦虑；避免“必爆”“全网最强”等夸张表达。" />
        <div className="chip-row page-gap-small">
          <Tag>禁用词：必爆</Tag>
          <Tag>品牌词：VO Mate</Tag>
          <Tag>CTA：关注后续路径</Tag>
        </div>
      </section>
    </>
  );
}

function BarList({ items }: { items: Array<[string, number]> }) {
  return (
    <div className="bar-list">
      {items.map(([label, value]) => (
        <div className="bar-row" key={label}>
          <span>{label}</span>
          <span className="bar-track">
            <span className="bar-fill" style={{ width: `${value}%` }} />
          </span>
          <strong>{value}</strong>
        </div>
      ))}
    </div>
  );
}
