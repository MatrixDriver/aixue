"use client";

import { useState, useMemo } from "react";
import katex from "katex";
import { cn } from "@/lib/utils";
import type { MessageRole, QuestionOption } from "@/lib/types";
import OcrExpandPanel from "./ocr-expand-panel";
import ImageLightbox from "./image-lightbox";
import QuestionSelector from "./question-selector";

interface ChatMessageProps {
  role: MessageRole;
  content: string;
  imagePath?: string;
  localImageUrl?: string;
  ocrText?: string;
  ocrLoading?: boolean;
  timestamp?: string;
  type?: "text" | "question_selection";
  questionOptions?: QuestionOption[];
  onSelectQuestion?: (selected: QuestionOption) => void;
  onSelectAll?: () => void;
  selectionDisabled?: boolean;
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
  // 清理 MathML 标签（旧数据兼容：LLM 有时返回 MathML 而非 LaTeX）
  let cleaned = text.replace(/<math[^>]*>[\s\S]*?<\/math>/gi, (match) => {
    // 尝试提取 MathML 中的数字文本作为 fallback
    const nums = match.replace(/<[^>]+>/g, "").trim();
    return nums ? `$${nums}$` : "";
  });
  // 清理其他残留 HTML 标签（非 KaTeX 生成的）
  cleaned = cleaned.replace(/<\/?(?:msub|msup|mfrac|mn|mi|mo|mrow|mover|munder|mtable|mtr|mtd|mtext|mspace|mpadded)[^>]*>/gi, "");

  // 转义 HTML 防止 XSS，再处理 LaTeX（KaTeX 自行生成安全 HTML）
  let result = escapeHtml(cleaned);

  // 处理 Markdown 表格
  result = result.replace(
    /(?:^|\n)(\|.+\|)\n(\|[\s\-:|]+\|)\n((?:\|.+\|\n?)+)/g,
    (_, header: string, _sep: string, body: string) => {
      const headerCells = header.split("|").filter((c: string) => c.trim());
      const rows = body.trim().split("\n").map((row: string) =>
        row.split("|").filter((c: string) => c.trim())
      );
      let table = '<table class="border-collapse text-sm my-2"><thead><tr>';
      headerCells.forEach((c: string) => {
        table += `<th class="border border-gray-300 px-2 py-1 bg-gray-100">${escapeHtml(c.trim())}</th>`;
      });
      table += "</tr></thead><tbody>";
      rows.forEach((cells: string[]) => {
        table += "<tr>";
        cells.forEach((c: string) => {
          table += `<td class="border border-gray-300 px-2 py-1">${escapeHtml(c.trim())}</td>`;
        });
        table += "</tr>";
      });
      table += "</tbody></table>";
      return table;
    }
  );

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
  type,
  questionOptions,
  onSelectQuestion,
  onSelectAll,
  selectionDisabled,
}: ChatMessageProps) {
  const isUser = role === "user";
  const [lightboxOpen, setLightboxOpen] = useState(false);

  const displayImageUrl = localImageUrl || imagePath;
  const showTextBubble = !(content === "[图片]" && displayImageUrl) && type !== "question_selection";

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

        {/* 选题按钮组 */}
        {type === "question_selection" && questionOptions && onSelectQuestion && onSelectAll && (
          <div className="inline-block rounded-2xl px-4 py-3 bg-white shadow-sm border border-gray-100">
            <QuestionSelector
              questions={questionOptions}
              message={content}
              onSelect={onSelectQuestion}
              onSelectAll={onSelectAll}
              disabled={selectionDisabled}
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
