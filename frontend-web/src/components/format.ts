import type { Platform } from "../types";

export const platformLabel: Record<Platform, string> = {
  douyin: "抖音",
  kuaishou: "快手",
  xiaohongshu: "小红书",
  youtube: "YouTube",
  wechat: "视频号"
};

export function compactNumber(value: number) {
  if (value >= 10000) return `${(value / 10000).toFixed(value >= 100000 ? 1 : 2)}w`;
  return value.toLocaleString("zh-CN");
}

export function percent(value: number) {
  return `${Math.round(value * 100)}%`;
}
