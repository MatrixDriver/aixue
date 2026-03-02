"use client";

import { useMemo } from "react";
import katex from "katex";
import { cn } from "@/lib/utils";
import type { MessageRole } from "@/lib/types";

interface ChatMessageProps {
  role: MessageRole;
  content: string;
  imagePath?: string;
  timestamp?: string;
}

/**
 * 解析文本中的 LaTeX 公式并渲染
 * - 块级公式: $$...$$
 * - 行内公式: $...$
 */
function renderWithLatex(text: string): string {
  // 先处理块级公式 $$...$$
  let result = text.replace(/\$\$([\s\S]*?)\$\$/g, (_, latex: string) => {
    try {
      return katex.renderToString(latex.trim(), {
        displayMode: true,
        throwOnError: false,
        trust: true,
      });
    } catch {
      return `<span class="text-red-500">[公式渲染错误]</span>`;
    }
  });

  // 再处理行内公式 $...$（排除已渲染的块级公式和货币符号 $数字）
  result = result.replace(
    /(?<!\$)\$(?!\$)((?:[^$\\]|\\.)+?)\$(?!\$)/g,
    (_, latex: string) => {
      try {
        return katex.renderToString(latex.trim(), {
          displayMode: false,
          throwOnError: false,
          trust: true,
        });
      } catch {
        return `<span class="text-red-500">[公式渲染错误]</span>`;
      }
    }
  );

  // 处理 \boxed{} 答案框（如果不在 $ 中）
  result = result.replace(/\\boxed\{([^}]*)\}/g, (_, content: string) => {
    try {
      return katex.renderToString(`\\boxed{${content}}`, {
        displayMode: false,
        throwOnError: false,
      });
    } catch {
      return `<strong>[${content}]</strong>`;
    }
  });

  // 将换行转为 <br>
  result = result.replace(/\n/g, "<br>");

  return result;
}

export default function ChatMessage({
  role,
  content,
  imagePath,
  timestamp,
}: ChatMessageProps) {
  const isUser = role === "user";

  const renderedContent = useMemo(() => renderWithLatex(content), [content]);

  return (
    <div
      className={cn(
        "flex gap-3 px-4 py-3",
        isUser ? "flex-row-reverse" : "flex-row"
      )}
    >
      {/* 头像 */}
      <div
        className={cn(
          "flex h-8 w-8 shrink-0 items-center justify-center rounded-full text-sm font-bold text-white",
          isUser ? "bg-indigo-500" : "bg-emerald-500"
        )}
      >
        {isUser ? "我" : "AI"}
      </div>

      {/* 消息内容 */}
      <div
        className={cn(
          "max-w-[80%] space-y-2",
          isUser ? "items-end text-right" : "items-start text-left"
        )}
      >
        {/* 图片 */}
        {imagePath && (
          <img
            src={imagePath}
            alt="上传的题目"
            className="max-h-60 rounded-lg border border-gray-200"
          />
        )}

        {/* 文字内容 */}
        <div
          className={cn(
            "inline-block rounded-2xl px-4 py-2.5 text-sm leading-relaxed",
            isUser
              ? "bg-indigo-600 text-white"
              : "bg-white text-gray-800 shadow-sm border border-gray-100"
          )}
        >
          <div
            className={cn(
              "prose prose-sm max-w-none",
              isUser && "prose-invert"
            )}
            dangerouslySetInnerHTML={{ __html: renderedContent }}
          />
        </div>

        {/* 时间戳 */}
        {timestamp && (
          <p className="text-xs text-gray-400">
            {new Date(timestamp).toLocaleTimeString("zh-CN", {
              hour: "2-digit",
              minute: "2-digit",
            })}
          </p>
        )}
      </div>
    </div>
  );
}
