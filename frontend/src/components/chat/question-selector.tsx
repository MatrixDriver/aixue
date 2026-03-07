"use client";

import { useState } from "react";
import { cn } from "@/lib/utils";
import type { QuestionOption } from "@/lib/types";

interface QuestionSelectorProps {
  questions: QuestionOption[];
  message: string;
  onSelect: (selected: QuestionOption) => void;
  onSelectAll: () => void;
  disabled?: boolean;
}

export default function QuestionSelector({
  questions,
  message,
  onSelect,
  onSelectAll,
  disabled = false,
}: QuestionSelectorProps) {
  const [selectedIndex, setSelectedIndex] = useState<number | null>(null);
  const completeQuestions = questions.filter((q) => q.complete);

  const handleSelect = (q: QuestionOption) => {
    if (!q.complete || disabled) return;
    setSelectedIndex(q.index);
    onSelect(q);
  };

  const handleSelectAll = () => {
    if (disabled) return;
    setSelectedIndex(-1); // -1 表示全部
    onSelectAll();
  };

  return (
    <div className="space-y-2">
      <p className="text-sm text-gray-600">{message}</p>
      <div className="flex flex-col gap-2">
        {questions.map((q) => (
          <button
            key={q.index}
            onClick={() => handleSelect(q)}
            disabled={!q.complete || disabled || selectedIndex !== null}
            className={cn(
              "flex items-center gap-2 rounded-lg border px-3 py-2 text-left text-sm transition-colors",
              q.complete && selectedIndex === null && !disabled
                ? "border-indigo-200 bg-indigo-50 text-indigo-700 hover:bg-indigo-100 cursor-pointer"
                : "",
              !q.complete
                ? "border-gray-200 bg-gray-50 text-gray-400 cursor-not-allowed"
                : "",
              selectedIndex === q.index
                ? "border-indigo-500 bg-indigo-100 ring-2 ring-indigo-200"
                : "",
              selectedIndex !== null && selectedIndex !== q.index
                ? "opacity-50"
                : ""
            )}
          >
            <span className="font-medium shrink-0">
              {q.label ? `第${q.label}题` : `题目 ${q.index}`}
            </span>
            <span className="truncate">{q.summary}</span>
            {!q.complete && (
              <span className="ml-auto shrink-0 rounded bg-gray-200 px-1.5 py-0.5 text-xs text-gray-500">
                不完整
              </span>
            )}
          </button>
        ))}

        {completeQuestions.length >= 2 && (
          <button
            onClick={handleSelectAll}
            disabled={disabled || selectedIndex !== null}
            className={cn(
              "rounded-lg border-2 border-dashed px-3 py-2 text-sm font-medium transition-colors",
              selectedIndex === null && !disabled
                ? "border-emerald-300 text-emerald-600 hover:bg-emerald-50 cursor-pointer"
                : "",
              selectedIndex === -1
                ? "border-emerald-500 bg-emerald-50 ring-2 ring-emerald-200"
                : "",
              selectedIndex !== null && selectedIndex !== -1
                ? "opacity-50"
                : ""
            )}
          >
            全部解答（{completeQuestions.length} 道题）
          </button>
        )}
      </div>
    </div>
  );
}
