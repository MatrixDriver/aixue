// ============================================================
// 工具函数
// ============================================================

import type { Grade, Subject } from "./types";

/** 所有年级选项 */
export const GRADES: Grade[] = [
  "初一",
  "初二",
  "初三",
  "高一",
  "高二",
  "高三",
];

/** 所有学科选项 */
export const SUBJECTS: Subject[] = ["数学", "物理", "化学", "生物"];

/** 学科图标颜色映射 */
export const SUBJECT_COLORS: Record<string, string> = {
  数学: "#3b82f6", // blue
  物理: "#8b5cf6", // violet
  化学: "#10b981", // emerald
  生物: "#f59e0b", // amber
};

/** 格式化日期 */
export function formatDate(dateStr: string): string {
  const d = new Date(dateStr);
  const year = d.getFullYear();
  const month = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

/** 格式化日期时间 */
export function formatDateTime(dateStr: string): string {
  const d = new Date(dateStr);
  const year = d.getFullYear();
  const month = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  const hour = String(d.getHours()).padStart(2, "0");
  const min = String(d.getMinutes()).padStart(2, "0");
  return `${year}-${month}-${day} ${hour}:${min}`;
}

/** 格式化相对时间 */
export function formatRelativeTime(dateStr: string): string {
  const now = Date.now();
  const past = new Date(dateStr).getTime();
  const diffMs = now - past;
  const diffMin = Math.floor(diffMs / 60000);
  const diffHour = Math.floor(diffMs / 3600000);
  const diffDay = Math.floor(diffMs / 86400000);

  if (diffMin < 1) return "刚刚";
  if (diffMin < 60) return `${diffMin} 分钟前`;
  if (diffHour < 24) return `${diffHour} 小时前`;
  if (diffDay < 30) return `${diffDay} 天前`;
  return formatDate(dateStr);
}

/** 截断文本 */
export function truncateText(text: string, maxLen: number = 50): string {
  if (text.length <= maxLen) return text;
  return text.slice(0, maxLen) + "...";
}

/** 验证状态中文映射 */
export function getVerificationLabel(status: string): string {
  const map: Record<string, string> = {
    verified: "已验证",
    unverified: "未验证",
    pending: "验证中",
    failed: "验证失败",
  };
  return map[status] || status;
}

/** 验证状态颜色 */
export function getVerificationColor(status: string): string {
  const map: Record<string, string> = {
    verified: "text-green-600",
    unverified: "text-yellow-600",
    pending: "text-gray-400",
    failed: "text-red-600",
  };
  return map[status] || "text-gray-400";
}

/** 解题模式中文映射 */
export function getModeLabel(mode: string): string {
  return mode === "socratic" ? "苏格拉底引导" : "完整解答";
}

/** cn 函数：合并 CSS 类名 */
export function cn(...classes: (string | false | null | undefined)[]): string {
  return classes.filter(Boolean).join(" ");
}
