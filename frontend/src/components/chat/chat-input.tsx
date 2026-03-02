"use client";

import { useState, useRef, useCallback } from "react";
import { Send } from "lucide-react";
import ImageUpload from "./image-upload";
import { cn } from "@/lib/utils";

interface ChatInputProps {
  onSend: (text: string, image: File | null) => void;
  disabled?: boolean;
  placeholder?: string;
  /** 是否为追问模式（隐藏图片上传） */
  followUp?: boolean;
}

export default function ChatInput({
  onSend,
  disabled,
  placeholder = "输入你的问题...",
  followUp = false,
}: ChatInputProps) {
  const [text, setText] = useState("");
  const [image, setImage] = useState<File | null>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const handleSubmit = useCallback(() => {
    const trimmed = text.trim();
    if (!trimmed && !image) return;
    onSend(trimmed, image);
    setText("");
    setImage(null);
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
    }
  }, [text, image, onSend]);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  // 自动调整 textarea 高度
  const handleInput = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setText(e.target.value);
    const el = e.target;
    el.style.height = "auto";
    el.style.height = Math.min(el.scrollHeight, 150) + "px";
  };

  const hasContent = text.trim() || image;

  return (
    <div className="border-t border-gray-200 bg-white px-4 py-3">
      {/* 图片预览行 */}
      {!followUp && (
        <div className="mb-2">
          <ImageUpload
            onImageSelect={setImage}
            selectedImage={image}
            onClear={() => setImage(null)}
            disabled={disabled}
          />
        </div>
      )}

      {/* 输入行 */}
      <div className="flex items-end gap-2">
        <textarea
          ref={textareaRef}
          value={text}
          onChange={handleInput}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          disabled={disabled}
          rows={1}
          className="flex-1 resize-none rounded-xl border border-gray-300 px-4 py-2.5 text-sm text-gray-800 placeholder-gray-400 focus:border-indigo-400 focus:outline-none focus:ring-2 focus:ring-indigo-100 disabled:cursor-not-allowed disabled:opacity-50"
          style={{ minHeight: "40px", maxHeight: "150px" }}
        />
        <button
          type="button"
          onClick={handleSubmit}
          disabled={disabled || !hasContent}
          className={cn(
            "flex h-10 w-10 shrink-0 items-center justify-center rounded-xl transition-colors",
            hasContent && !disabled
              ? "bg-indigo-600 text-white hover:bg-indigo-700"
              : "bg-gray-100 text-gray-400 cursor-not-allowed"
          )}
        >
          <Send size={18} />
        </button>
      </div>

      <p className="mt-1.5 text-xs text-gray-400">
        Enter 发送，Shift+Enter 换行
        {!followUp && " | 支持上传题目图片"}
      </p>
    </div>
  );
}
