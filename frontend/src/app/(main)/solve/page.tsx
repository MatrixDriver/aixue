"use client";

import { useChat } from "@/hooks/use-chat";
import ChatContainer from "@/components/chat/chat-container";
import { Plus } from "lucide-react";

export default function SolvePage() {
  const {
    messages,
    sessionId,
    mode,
    subject,
    loading,
    error,
    sendMessage,
    setMode,
    setSubject,
    newChat,
    selectQuestion,
    selectAll,
    selectionDisabled,
  } = useChat();

  return (
    <div className="flex h-full flex-col">
      {/* 页面标题栏 */}
      <div className="flex items-center justify-between border-b border-gray-200 bg-white px-4 py-2 lg:px-6">
        <h1 className="text-lg font-semibold text-gray-800">智能解题</h1>
        {sessionId && (
          <button
            onClick={newChat}
            className="flex items-center gap-1.5 rounded-lg bg-indigo-50 px-3 py-1.5 text-sm font-medium text-indigo-600 transition-colors hover:bg-indigo-100"
          >
            <Plus size={16} />
            新对话
          </button>
        )}
      </div>

      {/* 错误提示 */}
      {error && (
        <div className="mx-4 mt-2 rounded-lg bg-red-50 px-4 py-2 text-sm text-red-600">
          {error}
        </div>
      )}

      {/* 对话容器 */}
      <div className="flex-1 overflow-hidden">
        <ChatContainer
          messages={messages}
          mode={mode}
          onModeChange={setMode}
          onSend={sendMessage}
          loading={loading}
          sessionId={sessionId}
          subject={subject}
          onSubjectChange={setSubject}
          onSelectQuestion={selectQuestion}
          onSelectAll={selectAll}
          selectionDisabled={selectionDisabled}
        />
      </div>
    </div>
  );
}
