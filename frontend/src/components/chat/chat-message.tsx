"use client";

import { useState, useMemo } from "react";
import katex from "katex";
import { cn } from "@/lib/utils";
import type { MessageRole } from "@/lib/types";
import OcrExpandPanel from "./ocr-expand-panel";
import ImageLightbox from "./image-lightbox";

interface ChatMessageProps {
  role: MessageRole;
  content: string;
  imagePath?: string;
  localImageUrl?: string;
  ocrText?: string;
  ocrLoading?: boolean;
  timestamp?: string;
}

/**
 * 解析文本中的 LaTeX 公式并渲染
 * - 块级公式: $$...$$
 * - 行内公式: $...$
 */
function escapeHtml(text: string): string {
  return text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

export function renderWithLatex(text: string): string {
  // 先转义 HTML 防止 XSS，再处理 LaTeX（KaTeX 自行生成安全 HTML）
  let result = escapeHtml(text);

  // 处理块级公式 $$...$$
  result = result.replace(/\$\$([\s\S]*?)\$\$/g, (_, latex: string) => {
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
  localImageUrl,
  ocrText,
  ocrLoading,
  timestamp,
}: ChatMessageProps) {
  const isUser = role === "user";
  const [lightboxOpen, setLightboxOpen] = useState(false);

  const displayImageUrl = localImageUrl || imagePath;
  const showTextBubble = !(content === "[图片]" && displayImageUrl);

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
        {/* 图片缩略图 + OCR 展开面板 + Lightbox */}
        {displayImageUrl && (
          <div className="space-y-1">
            <img
              src={displayImageUrl}
              alt="上传的题目"
              className="w-48 sm:w-60 max-h-72 rounded-lg border border-gray-200 object-cover cursor-pointer hover:opacity-90 transition-opacity"
              onClick={() => setLightboxOpen(true)}
              onError={(e) => {
                (e.target as HTMLImageElement).src = "";
                (e.target as HTMLImageElement).alt = "图片已过期";
              }}
            />

            {isUser && (
              <OcrExpandPanel
                imageUrl={displayImageUrl}
                ocrText={ocrText}
                loading={ocrLoading}
              />
            )}

            {lightboxOpen && (
              <ImageLightbox
                src={displayImageUrl}
                alt="题目大图"
                onClose={() => setLightboxOpen(false)}
              />
            )}
          </div>
        )}

        {/* 文字内容 */}
        {showTextBubble && (
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
        )}

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
