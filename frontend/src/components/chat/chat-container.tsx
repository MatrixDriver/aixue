"use client";

import { useRef, useEffect } from "react";
import ChatMessage from "./chat-message";
import ChatInput from "./chat-input";
import ModeSwitch from "./mode-switch";
import { Loader2 } from "lucide-react";
import type { Message, SolveMode, QuestionOption } from "@/lib/types";
import { SUBJECTS } from "@/lib/utils";

interface ChatContainerProps {
  messages: Message[];
  mode: SolveMode;
  onModeChange: (mode: SolveMode) => void;
  onSend: (text: string, image: File | null) => void;
  loading: boolean;
  sessionId: string | null;
  subject: string;
  onSubjectChange: (subject: string) => void;
  onSelectQuestion?: (selected: QuestionOption) => void;
  onSelectAll?: () => void;
  selectionDisabled?: boolean;
}

export default function ChatContainer({
  messages,
  mode,
  onModeChange,
  onSend,
  loading,
  sessionId,
  subject,
  onSubjectChange,
  onSelectQuestion,
  onSelectAll,
  selectionDisabled,
}: ChatContainerProps) {
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // 新消息到达时自动滚动到底部
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  const isFollowUp = !!sessionId && messages.length > 0;

  return (
    <div className="flex h-full flex-col">
      {/* 顶部工具栏 */}
      <div className="flex flex-wrap items-center gap-3 border-b border-gray-200 bg-white px-4 py-3">
        <ModeSwitch
          mode={mode}
          onChange={onModeChange}
          disabled={isFollowUp}
        />

        {/* 学科选择 */}
        {!isFollowUp && (
          <select
            value={subject}
            onChange={(e) => onSubjectChange(e.target.value)}
            className="rounded-lg border border-gray-300 px-3 py-1.5 text-sm text-gray-700 focus:border-indigo-400 focus:outline-none"
          >
            <option value="">自动判断学科</option>
            {SUBJECTS.map((s) => (
              <option key={s} value={s}>
                {s}
              </option>
            ))}
          </select>
        )}

        {sessionId && (
          <span className="text-xs text-gray-400">
            会话 ID: {sessionId.slice(0, 8)}...
          </span>
        )}
      </div>

      {/* 消息列表 */}
      <div className="flex-1 overflow-y-auto bg-gray-50">
        {messages.length === 0 ? (
          <div className="flex h-full flex-col items-center justify-center px-4 text-center">
            <div className="mb-4 rounded-full bg-indigo-100 p-4">
              <svg
                className="h-12 w-12 text-indigo-600"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={1.5}
                  d="M12 6.042A8.967 8.967 0 006 3.75c-1.052 0-2.062.18-3 .512v14.25A8.987 8.987 0 016 18c2.305 0 4.408.867 6 2.292m0-14.25a8.966 8.966 0 016-2.292c1.052 0 2.062.18 3 .512v14.25A8.987 8.987 0 0018 18a8.967 8.967 0 00-6 2.292m0-14.25v14.25"
                />
              </svg>
            </div>
            <h3 className="mb-2 text-lg font-semibold text-gray-700">
              开始解题
            </h3>
            <p className="max-w-sm text-sm text-gray-500">
              上传题目图片或输入题目文字，AI 将为你提供详细的解题思路和步骤。
            </p>
            <div className="mt-4 flex flex-wrap justify-center gap-2 text-xs text-gray-400">
              <span className="rounded-full bg-gray-100 px-3 py-1">
                支持数学、物理、化学、生物
              </span>
              <span className="rounded-full bg-gray-100 px-3 py-1">
                LaTeX 公式渲染
              </span>
              <span className="rounded-full bg-gray-100 px-3 py-1">
                多轮追问
              </span>
            </div>
          </div>
        ) : (
          <div className="py-4">
            {messages.map((msg) => (
              <ChatMessage
                key={msg.id}
                role={msg.role}
                content={msg.content}
                imagePath={msg.image_path}
                localImageUrl={msg.localImageUrl}
                ocrText={msg.ocrText}
                ocrLoading={msg.role === "user" && !!msg.localImageUrl && msg.ocrText === undefined && loading}
                timestamp={msg.created_at}
                type={msg.type}
                questionOptions={msg.questionOptions}
                onSelectQuestion={onSelectQuestion}
                onSelectAll={onSelectAll}
                selectionDisabled={selectionDisabled}
              />
            ))}

            {/* 加载动画 */}
            {loading && (
              <div className="flex items-center gap-2 px-4 py-3">
                <div className="flex h-8 w-8 items-center justify-center rounded-full bg-emerald-500 text-sm font-bold text-white">
                  AI
                </div>
                <div className="flex items-center gap-2 rounded-2xl border border-gray-100 bg-white px-4 py-2.5 text-sm text-gray-500 shadow-sm">
                  <Loader2 size={16} className="animate-spin" />
                  正在思考...
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      {/* 输入区域 */}
      <ChatInput
        onSend={onSend}
        disabled={loading}
        placeholder={
          isFollowUp ? "继续追问..." : "输入题目文字或上传题目图片..."
        }
        followUp={isFollowUp}
      />
    </div>
  );
}
