"use client";

import { useState } from "react";
import { ChevronDown, ChevronUp, Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";
import { renderWithLatex } from "./chat-message";

interface OcrExpandPanelProps {
  imageUrl?: string;
  ocrText?: string;
  loading?: boolean;
}

export default function OcrExpandPanel({ imageUrl, ocrText, loading }: OcrExpandPanelProps) {
  const [expanded, setExpanded] = useState(false);

  // 不需要展开按钮的情况：无 OCR 文本且不在加载中
  if (!loading && ocrText === undefined) return null;

  return (
    <div className="mt-1.5">
      {/* 展开/收起按钮 */}
      <button
        type="button"
        onClick={() => setExpanded(!expanded)}
        className="flex items-center gap-1 text-xs text-gray-500 hover:text-indigo-500 transition-colors"
      >
        {expanded ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
        {expanded ? "收起" : "查看识别结果"}
      </button>

      {/* 展开区域 - grid 动画 */}
      <div
        className={cn(
          "grid transition-all duration-300 ease-in-out",
          expanded ? "grid-rows-[1fr]" : "grid-rows-[0fr]"
        )}
      >
        <div className="overflow-hidden">
          <div className="mt-2 space-y-2 rounded-lg border border-gray-200 bg-gray-50 p-3">
            {/* 大图 */}
            {imageUrl && (
              <img
                src={imageUrl}
                alt="题目图片"
                className="max-w-full max-h-80 rounded border border-gray-200"
              />
            )}

            {/* OCR 文本 */}
            {loading ? (
              <div className="flex items-center gap-2 text-sm text-gray-400">
                <Loader2 size={14} className="animate-spin" />
                正在识别...
              </div>
            ) : ocrText ? (
              <div className="border-l-2 border-indigo-300 pl-3">
                <p className="mb-1 text-xs font-medium text-gray-500">识别结果</p>
                <div
                  className="prose prose-sm max-w-none text-sm text-gray-700"
                  dangerouslySetInnerHTML={{ __html: renderWithLatex(ocrText) }}
                />
              </div>
            ) : (
              <p className="text-sm text-gray-400">未能识别图片中的文字</p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
