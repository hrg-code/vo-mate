const navItems = [
  ["dashboard", "首页", "⌂"],
  ["contents", "视频库", "▤"],
  ["audience", "粉丝画像", "◉"],
  ["topics", "选题雷达", "✦"],
  ["scripts", "脚本工作台", "✎"],
  ["seo", "SEO 优化", "#"],
  ["calendar", "发布日历", "□"],
  ["retrospectives", "复盘中心", "✓"],
  ["memory", "记忆库", "◎"],
  ["collector", "采集管理", "↻"],
  ["settings", "设置", "⚙"]
];

const videos = [
  ["程序员 35 岁后还能不能继续写代码", "抖音", "2026-05-08", "62s", "34.6w", "1.9w", "892", "38%", "+1,286", "89", "已复盘"],
  ["为什么你的简历总被 HR 刷掉", "抖音", "2026-05-06", "48s", "18.2w", "8,431", "521", "42%", "+604", "82", "待复盘"],
  ["AI 时代普通程序员的三个机会", "视频号", "2026-05-04", "91s", "9.7w", "3,126", "318", "31%", "+298", "76", "脚本可复用"],
  ["外包五年后我学到的残酷真相", "小红书", "2026-05-02", "55s", "12.4w", "5,980", "437", "45%", "+781", "86", "高搜索"],
  ["面试官问项目难点怎么回答", "YouTube", "2026-04-29", "78s", "4.1w", "1,022", "89", "29%", "+96", "68", "需优化 SEO"]
];

const topics = [
  {
    title: "35 岁程序员不是危机，是岗位切换信号",
    angle: "把焦虑问题改成职业策略，适合做 60 秒强钩子口播。",
    score: 91,
    seo: 86,
    audience: 93,
    risk: "情绪过强会降低完播",
    evidence: "参考 12 条历史内容"
  },
  {
    title: "AI 不会淘汰程序员，但会淘汰不会拆任务的人",
    angle: "用真实项目拆解 AI 协作边界，承接近期搜索词。",
    score: 87,
    seo: 92,
    audience: 84,
    risk: "需要避免泛泛讲工具",
    evidence: "参考 8 条历史内容"
  },
  {
    title: "普通人转码前先算清这三笔账",
    angle: "面向泛职场人群，适合小红书搜索和收藏。",
    score: 79,
    seo: 88,
    audience: 72,
    risk: "账号人设匹配中等",
    evidence: "参考 6 条历史内容"
  }
];

const app = document.querySelector("#app");
const navList = document.querySelector("#navList");
const drawer = document.querySelector("#drawer");
const drawerBackdrop = document.querySelector("#drawerBackdrop");
const drawerBody = document.querySelector("#drawerBody");

let activeRoute = "dashboard";

function renderNav() {
  navList.innerHTML = navItems
    .map(
      ([id, label, icon]) => `
        <button class="nav-item ${id === activeRoute ? "active" : ""}" type="button" data-route="${id}">
          <span class="nav-icon" aria-hidden="true">${icon}</span>
          <span>${label}</span>
        </button>`
    )
    .join("");
}

function pageHeader(title, subtitle, actions = "") {
  return `
    <section class="page-header">
      <div>
        <p class="eyebrow">VO Mate / AI Creator Workbench</p>
        <h1>${title}</h1>
        <p class="page-subtitle">${subtitle}</p>
      </div>
      <div class="page-actions">${actions}</div>
    </section>
  `;
}

function button(label, type = "secondary", attrs = "") {
  return `<button class="button ${type}" type="button" ${attrs}>${label}</button>`;
}

function metric(label, value, delta, dir = "up") {
  const heights = [42, 58, 49, 65, 77, 62, 88, 79, 92, 84];
  return `
    <article class="metric-card">
      <div class="metric-label"><span>${label}</span><span class="delta ${dir}">${delta}</span></div>
      <div class="metric-value">${value}</div>
      <div class="mini-bars">${heights.map((h) => `<span style="height:${h}%"></span>`).join("")}</div>
    </article>`;
}

function aiPanel(summary = "基于过去 30 条同类内容，建议今天优先做“职场转折 + 可执行清单”方向。") {
  return `
    <aside class="panel ai-panel">
      <div class="panel-header">
        <div>
          <p class="eyebrow">AI Insight</p>
          <h2>今日建议</h2>
        </div>
        <span class="badge score-high">可信度 86</span>
      </div>
      <p>${summary}</p>
      <div class="confidence">
        <div class="confidence-track"><span style="width:86%"></span></div>
        <strong>86%</strong>
      </div>
      <div class="evidence-list">
        <div class="evidence-item"><strong>为什么</strong><p class="muted">搜索流量连续 4 天增长，35 岁、AI、面试关键词共现率高。</p></div>
        <div class="evidence-item"><strong>建议动作</strong><p class="muted">生成 60 秒口播，保留强冲突开头，同时准备小红书搜索标题。</p></div>
        <div class="evidence-item"><strong>风险</strong><p class="muted">过度制造焦虑会提高评论但拉低收藏，需要用具体方法收束。</p></div>
      </div>
      <div class="button-row" style="margin-top:12px">
        ${button("查看依据", "secondary", "data-open-drawer")}
        ${button("采纳", "primary")}
      </div>
    </aside>`;
}

function renderDashboard() {
  app.innerHTML =
    pageHeader(
      "首页",
      "30 秒内看到账号表现、异常和今天最值得推进的内容动作",
      `${button("同步数据", "secondary")} ${button("生成今日选题", "primary", 'data-route="topics"')}`
    ) +
    `<div class="layout-grid">
      <section>
        <div class="metric-grid">
          ${metric("播放量", "34.6w", "+42%")}
          ${metric("互动率", "7.8%", "+1.2%")}
          ${metric("涨粉", "1,286", "+36%")}
          ${metric("完播率", "38%", "-4%", "down")}
          ${metric("搜索流量", "21%", "+9%")}
        </div>
        <div class="dashboard-grid">
          <div class="panel">
            <div class="panel-header">
              <div><h2>表现趋势</h2><p class="muted">近 12 日播放与搜索流量</p></div>
              <div class="segmented"><span class="chip">7 日</span><span class="chip">30 日</span><span class="chip">90 日</span></div>
            </div>
            <div class="trend-chart">${[42, 58, 46, 61, 72, 64, 78, 69, 84, 76, 91, 88]
              .map(
                (h, i) => `<div class="trend-column">
                  <span class="plays" style="height:${h}%"></span>
                  <span class="search" style="height:${Math.max(20, h - 28)}%"></span>
                  <small>${i + 1}</small>
                </div>`
              )
              .join("")}</div>
            <div class="legend"><span>播放</span><span>搜索流量</span></div>
          </div>
          <div class="panel">
            <h2>今日 AI 建议</h2>
            <div class="action-list">
              <div class="action-item"><strong>继续承接 35 岁程序员话题</strong><p class="muted">预测播放 28w-41w，建议先生成 60 秒脚本。</p></div>
              <div class="action-item"><strong>复盘完播率下降视频</strong><p class="muted">前 5 秒留存低于账号中位数 11%。</p></div>
              <div class="action-item"><strong>补充小红书搜索标题</strong><p class="muted">“转码成本”“AI 程序员”搜索机会上升。</p></div>
            </div>
          </div>
        </div>
        <div class="panel" style="margin-top:16px">
          <div class="panel-header"><h2>最近内容</h2>${button("查看全部", "secondary", 'data-route="contents"')}</div>
          ${videoTable(videos.slice(0, 4))}
        </div>
      </section>
      ${aiPanel()}
    </div>`;
}

function videoTable(rows = videos) {
  return `<div class="table-wrap">
    <table>
      <thead>
        <tr><th>内容</th><th>平台</th><th>发布</th><th>时长</th><th>播放</th><th>点赞</th><th>评论</th><th>完播</th><th>涨粉</th><th>评分</th><th>状态</th><th>操作</th></tr>
      </thead>
      <tbody>
        ${rows
          .map(
            (v) => `<tr>
              <td><div class="video-cell"><span class="cover"></span><strong>${v[0]}</strong></div></td>
              <td><span class="chip">${v[1]}</span></td><td>${v[2]}</td><td>${v[3]}</td><td>${v[4]}</td><td>${v[5]}</td><td>${v[6]}</td><td>${v[7]}</td><td>${v[8]}</td>
              <td><span class="badge ${Number(v[9]) > 80 ? "score-high" : "score-mid"}">${v[9]}</span></td>
              <td>${v[10]}</td><td>${button("复盘", "ghost", "data-open-drawer")}</td>
            </tr>`
          )
          .join("")}
      </tbody>
    </table>
  </div>`;
}

function renderContents() {
  app.innerHTML =
    pageHeader(
      "视频库",
      "统一查看多平台历史内容，筛选高潜力视频并进入复盘",
      `${button("导入数据", "secondary")} ${button("生成复盘", "primary", "data-open-drawer")}`
    ) +
    `<section class="panel">
      <div class="filter-bar">
        <select class="field" style="width:150px"><option>全部平台</option><option>抖音</option><option>小红书</option></select>
        <select class="field" style="width:150px"><option>近 30 天</option><option>近 90 天</option></select>
        <input class="field" style="width:260px" placeholder="搜索标题、标签、关键词" />
        <span class="chip">有 ASR</span><span class="chip">未复盘</span><span class="chip">完播率 > 30%</span>
      </div>
      ${videoTable()}
    </section>`;
}

function renderAudience() {
  app.innerHTML =
    pageHeader("粉丝画像", "理解粉丝是谁、何时活跃、喜欢什么", button("生成画像洞察", "primary", "data-open-drawer")) +
    `<div class="layout-grid">
      <section>
        <div class="metric-grid">
          ${metric("粉丝总数", "18.7w", "+3.4%")}
          ${metric("净增粉", "4,926", "+18%")}
          ${metric("活跃粉丝", "42%", "+6%")}
          ${metric("高互动粉", "8,340", "+11%")}
          ${metric("取关率", "0.8%", "-0.2%")}
        </div>
        <div class="dashboard-grid">
          <div class="panel"><h2>兴趣分布</h2>${barList([["职场成长", 82], ["AI 工具", 74], ["面试求职", 67], ["副业转型", 48]])}</div>
          <div class="panel"><h2>活跃时间</h2><div class="heatmap">${Array.from({ length: 28 }, (_, i) => `<span class="heat-cell" style="--level:${0.12 + (i % 7) * 0.1}"></span>`).join("")}</div></div>
        </div>
      </section>
      ${aiPanel("粉丝新增主要来自 25-34 岁职场人，收藏行为集中在“面试回答”和“AI 工具清单”。")}
    </div>`;
}

function barList(items) {
  return `<div class="bar-list">${items
    .map(([label, value]) => `<div class="bar-row"><span>${label}</span><span class="bar-track"><span class="bar-fill" style="width:${value}%"></span></span><strong>${value}</strong></div>`)
    .join("")}</div>`;
}

function renderTopics() {
  app.innerHTML =
    pageHeader("选题雷达", "从历史数据、ASR、搜索词和记忆库中生成可拍选题", button("生成选题", "primary", 'id="generateTopic"')) +
    `<div class="layout-grid">
      <section>
        <div class="panel">
          <div class="input-grid">
            <input class="field" id="topicInput" value="程序员 35 岁危机" aria-label="方向描述" />
            <select class="field"><option>目标：涨粉</option><option>目标：搜索</option></select>
            <select class="field"><option>60 秒</option><option>30 秒</option><option>90 秒</option></select>
          </div>
          <div class="chip-row" style="margin-top:10px"><span class="chip">抖音</span><span class="chip">小红书</span><span class="chip">参考热点</span><span class="chip">账号风格：克制直接</span></div>
        </div>
        <div class="topic-list" id="topicList" style="margin-top:16px">${topicCards()}</div>
      </section>
      ${aiPanel("系统已检索 26 条相似历史内容，其中“职业转折 + 明确步骤”的结构表现最稳定。")}
    </div>`;
}

function topicCards() {
  return topics
    .map(
      (topic) => `<article class="topic-card">
        <div>
          <div class="chip-row"><span class="badge score-high">预测高</span><span class="chip">${topic.evidence}</span></div>
          <h2 style="margin-top:10px">${topic.title}</h2>
          <p class="muted">${topic.angle}</p>
          <div class="topic-meta">
            <span class="chip">SEO ${topic.seo}</span><span class="chip">受众 ${topic.audience}</span><span class="badge risk">${topic.risk}</span><span class="chip">抖音 / 小红书</span>
          </div>
          <div class="button-row" style="margin-top:12px">${button("生成脚本", "primary", 'data-route="scripts"')} ${button("查看依据", "secondary", "data-open-drawer")}</div>
        </div>
        <div class="score-box">${topic.score}</div>
      </article>`
    )
    .join("");
}

function renderScripts() {
  app.innerHTML =
    pageHeader("脚本工作台", "把选题转为可拍、可改、可发布的口播内容", `${button("保存草稿", "secondary")} ${button("生成 SEO", "primary", 'data-route="seo"')}`) +
    `<section class="split-page">
      <aside class="panel">
        <h2>当前选题</h2>
        <p><strong>35 岁程序员不是危机，是岗位切换信号</strong></p>
        <p class="muted">参考 12 条历史内容，推荐 60 秒结构。</p>
        <h3>版本</h3>
        <div class="version-list">
          <div class="version-item"><strong>v1 AI 初稿</strong><p class="muted">10:42 生成</p></div>
          <div class="version-item"><strong>v2 抖音版</strong><p class="muted">强化开头钩子</p></div>
        </div>
      </aside>
      <section class="panel script-editor">
        <div class="panel-header"><h2>口播脚本</h2><span class="badge score-high">预计 58 秒</span></div>
        <textarea class="textarea script-textarea">开头 3 秒：
如果你担心 35 岁以后写不动代码，先别急着否定自己。

主体：
真正的问题不是年龄，而是你还停留在“只接需求”的岗位形态里。35 岁以后，企业更需要的是能拆问题、控风险、带人交付的人。

转折：
所以这不是退出信号，而是岗位切换信号。

结尾 CTA：
如果你想知道怎么从执行型程序员转到方案型角色，我下一条讲具体路径。</textarea>
        <div class="word-count"><span>字数 226</span><span>结构：钩子 / 解释 / 转折 / CTA</span></div>
      </section>
      <aside class="panel">
        <h2>AI Copilot</h2>
        <div class="task-list">
          <button class="button secondary" type="button">改强开头</button>
          <button class="button secondary" type="button">缩短到 30 秒</button>
          <button class="button secondary" type="button">加真实案例</button>
          <button class="button secondary" type="button">转小红书口吻</button>
        </div>
        <div class="evidence-list" style="margin-top:16px">
          <div class="evidence-item"><strong>当前判断</strong><p class="muted">开头清晰，但中段案例不足，建议加入一条真实项目场景。</p></div>
          <div class="evidence-item"><strong>可信度 82%</strong><p class="muted">依据 7 条高完播脚本，强案例段通常出现在 18-32 秒。</p></div>
          <div class="button-row">${button("查看依据", "secondary", "data-open-drawer")} ${button("采纳建议", "primary")}</div>
        </div>
      </aside>
    </section>`;
}

function renderSeo() {
  app.innerHTML =
    pageHeader("SEO 优化", "生成平台适配标题、简介、标签与关键词布局", button("加入发布计划", "primary", 'data-route="calendar"')) +
    `<div class="layout-grid">
      <section class="panel">
        <div class="platform-tabs"><button class="tab-button active">抖音</button><button class="tab-button">小红书</button><button class="tab-button">YouTube Shorts</button><button class="tab-button">视频号</button></div>
        <h2>标题实验</h2>
        <div class="action-list">
          <div class="action-item"><div class="panel-header"><strong>35 岁程序员最该换的不是行业，而是岗位形态</strong><span class="badge score-high">92</span></div><p class="muted">覆盖关键词：35 岁、程序员、岗位、转型</p></div>
          <div class="action-item"><div class="panel-header"><strong>程序员 35 岁危机，其实是一个误解</strong><span class="badge score-mid">78</span></div><p class="muted">冲突明确，但搜索词覆盖偏弱。</p></div>
        </div>
        <h2 style="margin-top:16px">简介</h2>
        <textarea class="textarea">这条视频聊程序员 35 岁后的职业切换：从只写代码，到能拆问题、控风险、交付方案。</textarea>
        <div class="chip-row" style="margin-top:12px"><span class="chip">#程序员</span><span class="chip">#35岁危机</span><span class="chip">#AI时代</span><span class="chip">#职场成长</span></div>
      </section>
      ${aiPanel("标题 1 更适合抖音推荐流，标题 2 更适合评论互动。建议 A/B 测试前 2 小时数据。")}
    </div>`;
}

function renderCalendar() {
  app.innerHTML =
    pageHeader("发布日历", "管理内容从灵感、脚本、拍摄、剪辑到发布的计划", button("新建计划", "primary")) +
    `<section class="kanban">
      ${["灵感", "已生成脚本", "待剪辑", "待发布"]
        .map(
          (col, i) => `<div class="kanban-column"><h3>${col}</h3>
            <article class="calendar-item"><span class="chip">${["抖音", "小红书", "视频号", "YouTube"][i]}</span><h3>${["AI 时代程序员机会", "35 岁岗位切换", "面试项目难点", "转码前算三笔账"][i]}</h3><p class="muted">${["今天 18:30", "明天 11:00", "5 月 12 日", "5 月 14 日"][i]}</p></article>
          </div>`
        )
        .join("")}
    </section>`;
}

function renderRetrospectives() {
  app.innerHTML =
    pageHeader("复盘中心", "管理单条视频复盘、周期报告和可沉淀经验", button("生成周报", "primary", "data-open-drawer")) +
    `<div class="layout-grid">
      <section class="panel">
        <div class="platform-tabs"><button class="tab-button active">单条视频</button><button class="tab-button">周报</button><button class="tab-button">月报</button><button class="tab-button">模式</button></div>
        <div class="retrospective-list">
          <div class="retrospective-item"><h2>程序员 35 岁后还能不能继续写代码</h2><p class="muted">结论：开头问题命中强，但中段缺少反例，评论转化高于收藏。</p><div class="button-row">${button("写入记忆库", "primary")} ${button("驳回结论", "secondary")}</div></div>
          <div class="retrospective-item"><h2>为什么你的简历总被 HR 刷掉</h2><p class="muted">结论：标题搜索价值高，完播稳定，适合承接面试系列。</p><div class="button-row">${button("生成承接选题", "primary", 'data-route="topics"')} ${button("查看依据", "secondary", "data-open-drawer")}</div></div>
        </div>
      </section>
      ${aiPanel("本周成功内容共同点：开头提出具体问题，20 秒内给出第一个可执行方法。")}
    </div>`;
}

function renderMemory() {
  app.innerHTML =
    pageHeader("记忆库", "查看、确认、降低权重或删除系统学到的经验", button("审核候选记忆", "primary")) +
    `<section class="memory-grid">
      ${[
        ["成功模式", "职场焦虑类内容必须在 15 秒内给出第一个解决动作。", "权重 0.82"],
        ["标题模式", "“不是 X，而是 Y”结构在程序员转型内容中收藏率更高。", "权重 0.76"],
        ["失败模式", "纯工具清单如果没有真实场景，评论多但完播偏低。", "权重 0.69"]
      ]
        .map(
          ([type, text, weight]) => `<article class="memory-card"><span class="chip">${type}</span><h2>${text}</h2><p class="muted">${weight} · 来源 6-14 条内容</p><div class="button-row">${button("确认", "primary")} ${button("降权", "secondary")} ${button("删除", "danger")}</div></article>`
        )
        .join("")}
    </section>`;
}

function renderCollector() {
  app.innerHTML =
    pageHeader("采集管理", "管理 Electron、浏览器插件、手动导入与采集任务状态", `${button("手动导入", "secondary")} ${button("立即同步", "primary")}`) +
    `<section>
      <div class="connector-grid">
        ${["抖音", "快手", "小红书", "YouTube", "视频号"]
          .map((name, i) => `<div class="connector"><span class="status-dot" style="display:inline-block"></span><h2>${name}</h2><p class="muted">${i === 0 ? "已连接，2 分钟前同步" : "待配置采集方式"}</p></div>`)
          .join("")}
      </div>
      <div class="panel" style="margin-top:16px">
        <h2>任务队列</h2>
        <div class="task-list">
          <div class="task-item"><strong>标准化 douyin_video_raw</strong><p class="muted">运行中 · 68%</p></div>
          <div class="task-item"><strong>关联 ASR 口播文本</strong><p class="muted">等待中</p></div>
          <div class="task-item"><strong>写入 Milvus 向量库</strong><p class="muted">等待中</p></div>
        </div>
      </div>
    </section>`;
}

function renderSettings() {
  app.innerHTML =
    pageHeader("设置", "配置工作区、平台账号、AI 风格、权限和采集策略", button("保存设置", "primary")) +
    `<section class="panel">
      <div class="input-grid">
        <input class="field" value="北极星内容组" aria-label="工作区名称" />
        <select class="field"><option>默认模型路由</option></select>
        <select class="field"><option>采集频率：每 6 小时</option></select>
      </div>
      <h2 style="margin-top:16px">AI 语气</h2>
      <textarea class="textarea">克制、直接、给方法，不制造焦虑；避免“必爆”“全网最强”等夸张表达。</textarea>
      <div class="chip-row" style="margin-top:12px"><span class="chip">禁用词：必爆</span><span class="chip">品牌词：VO Mate</span><span class="chip">CTA：关注后续路径</span></div>
    </section>`;
}

const renderers = {
  dashboard: renderDashboard,
  contents: renderContents,
  audience: renderAudience,
  topics: renderTopics,
  scripts: renderScripts,
  seo: renderSeo,
  calendar: renderCalendar,
  retrospectives: renderRetrospectives,
  memory: renderMemory,
  collector: renderCollector,
  settings: renderSettings
};

function openDrawer() {
  drawerBody.innerHTML = [
    ["历史视频", "程序员 35 岁后还能不能继续写代码", "播放 34.6w，完播 38%，涨粉 1,286，相关性 94%"],
    ["搜索关键词", "35 岁危机 / AI 程序员 / 转型", "近 7 日搜索占比从 12% 升至 21%"],
    ["受众画像", "25-34 岁职场人", "收藏集中在职业路径、面试、AI 工具清单"],
    ["记忆模式", "先承认焦虑，再给可执行步骤", "来源于 9 条高收藏内容，权重 0.82"]
  ]
    .map(([type, title, desc]) => `<article class="evidence-item"><span class="chip">${type}</span><h3 style="margin-top:8px">${title}</h3><p class="muted">${desc}</p></article>`)
    .join("");
  drawer.hidden = false;
  drawerBackdrop.hidden = false;
  requestAnimationFrame(() => drawer.classList.add("open"));
  drawer.setAttribute("aria-hidden", "false");
}

function closeDrawer() {
  drawer.classList.remove("open");
  drawer.setAttribute("aria-hidden", "true");
  setTimeout(() => {
    drawer.hidden = true;
    drawerBackdrop.hidden = true;
  }, 200);
}

function navigate(route) {
  activeRoute = route;
  renderNav();
  renderers[route]();
  app.focus();
}

document.addEventListener("click", (event) => {
  const routeButton = event.target.closest("[data-route]");
  if (routeButton) {
    navigate(routeButton.dataset.route);
    return;
  }
  if (event.target.closest("[data-open-drawer]")) {
    openDrawer();
  }
});

document.querySelector("#closeDrawer").addEventListener("click", closeDrawer);
drawerBackdrop.addEventListener("click", closeDrawer);

renderNav();
renderDashboard();
