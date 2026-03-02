"use client";

import type { KnowledgeGap } from "@/lib/types";
import { cn } from "@/lib/utils";

interface WeakPointListProps {
  gaps: KnowledgeGap[];
}

export default function WeakPointList({ gaps }: WeakPointListProps) {
  if (!gaps || gaps.length === 0) {
    return (
      <div className="py-8 text-center text-sm text-gray-400">
        暂无薄弱知识点数据
      </div>
    );
  }

  // 按掌握度从低到高排序
  const sorted = [...gaps].sort((a, b) => a.mastery_level - b.mastery_level);

  return (
    <div className="space-y-3">
      {sorted.map((gap, i) => {
        const level = gap.mastery_level;
        const barColor =
          level < 40
            ? "bg-red-500"
            : level < 60
              ? "bg-yellow-500"
              : level < 80
                ? "bg-blue-500"
                : "bg-green-500";
        const textColor =
          level < 40
            ? "text-red-600"
            : level < 60
              ? "text-yellow-600"
              : level < 80
                ? "text-blue-600"
                : "text-green-600";

        return (
          <div
            key={i}
            className="rounded-lg bg-white p-4 shadow-sm border border-gray-100"
          >
            <div className="flex items-start justify-between">
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-gray-800">
                  {gap.knowledge_point}
                </p>
                <p className="mt-1 text-xs text-gray-500">{gap.suggestion}</p>
              </div>
              <div className="ml-4 shrink-0 text-right">
                <span className={cn("text-lg font-bold", textColor)}>
                  {level}%
                </span>
                <p className="text-xs text-gray-400">
                  错 {gap.error_count} 次
                </p>
              </div>
            </div>
            <div className="mt-2 h-1.5 rounded-full bg-gray-100">
              <div
                className={cn("h-1.5 rounded-full transition-all", barColor)}
                style={{ width: `${level}%` }}
              />
            </div>
          </div>
        );
      })}
    </div>
  );
}
