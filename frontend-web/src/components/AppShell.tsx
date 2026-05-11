import {
  BarChart3,
  CalendarDays,
  DatabaseZap,
  FileText,
  Gauge,
  Library,
  Search,
  Settings,
  Sparkles,
  Target,
  Users,
  Video,
  Workflow
} from "lucide-react";
import { Avatar, Button, Input, Select, Tooltip } from "antd";
import type { ReactNode } from "react";
import type { RouteId, WorkspaceContext } from "../types";

const navItems: Array<{ id: RouteId; label: string; icon: ReactNode }> = [
  { id: "dashboard", label: "首页", icon: <Gauge size={18} /> },
  { id: "contents", label: "视频库", icon: <Video size={18} /> },
  { id: "audience", label: "粉丝画像", icon: <Users size={18} /> },
  { id: "topics", label: "选题雷达", icon: <Target size={18} /> },
  { id: "scripts", label: "脚本工作台", icon: <FileText size={18} /> },
  { id: "seo", label: "SEO 优化", icon: <BarChart3 size={18} /> },
  { id: "calendar", label: "发布日历", icon: <CalendarDays size={18} /> },
  { id: "retrospectives", label: "复盘中心", icon: <Sparkles size={18} /> },
  { id: "memory", label: "记忆库", icon: <Library size={18} /> },
  { id: "collector", label: "采集管理", icon: <DatabaseZap size={18} /> },
  { id: "settings", label: "设置", icon: <Settings size={18} /> }
];

export function AppShell({
  context,
  activeRoute,
  children,
  onNavigate
}: {
  context: WorkspaceContext;
  activeRoute: RouteId;
  children: ReactNode;
  onNavigate: (route: RouteId) => void;
}) {
  return (
    <div className="app-shell">
      <aside className="side-nav" aria-label="主导航">
        <div className="brand">
          <div className="brand-mark">VO</div>
          <div>
            <strong>VO Mate</strong>
            <span>AI Creator Workbench</span>
          </div>
        </div>
        <nav className="nav-list">
          {navItems.map((item) => (
            <Button
              className={`nav-item ${item.id === activeRoute ? "active" : ""}`}
              htmlType="button"
              key={item.id}
              onClick={() => onNavigate(item.id)}
            >
              <span className="nav-icon" aria-hidden="true">
                {item.icon}
              </span>
              <span>{item.label}</span>
            </Button>
          ))}
        </nav>
        <div className="collector-pill">
          <span className="status-dot" />
          <div>
            <strong>采集端在线</strong>
            <span>3 个任务运行中</span>
          </div>
        </div>
      </aside>

      <div className="workspace">
        <header className="top-bar">
          <div className="context-group">
            <Select
              aria-label="工作区"
              className="context-select"
              value={context.workspaceName}
              options={[{ value: context.workspaceName, label: context.workspaceName }]}
            />
            <Select
              aria-label="账号范围"
              className="context-select account-select"
              value={context.accountName}
              options={[{ value: context.accountName, label: context.accountName }]}
            />
          </div>
          <Input
            allowClear
            aria-label="全局搜索"
            className="global-search-input"
            placeholder="搜索视频、选题、关键词、复盘"
            prefix={<Search size={16} aria-hidden="true" />}
            type="search"
          />
          <div className="top-actions">
            <Tooltip title="任务中心">
              <Button aria-label="任务中心" className="top-icon-button" icon={<Workflow size={18} />} type="text" />
            </Tooltip>
            <Avatar className="user-avatar" aria-label="用户菜单">
              AL
            </Avatar>
          </div>
        </header>
        <main className="main-content" tabIndex={-1}>{children}</main>
      </div>
    </div>
  );
}
