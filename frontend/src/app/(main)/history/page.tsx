"use client";

import { useState, useEffect, useCallback } from "react";
import { listSessions, getSession } from "@/lib/api";
import { SUBJECTS, formatRelativeTime, getModeLabel, getVerificationLabel, getVerificationColor, truncateText, cn } from "@/lib/utils";
import ChatMessage from "@/components/chat/chat-message";
import { ChevronLeft, Filter, MessageSquare } from "lucide-react";
import type { SessionSummary, SessionDetail } from "@/lib/types";

export default function HistoryPage() {
  const [sessions, setSessions] = useState<SessionSummary[]>([]);
  const [selectedSession, setSelectedSession] = useState<SessionDetail | null>(null);
  const [subjectFilter, setSubjectFilter] = useState("");
  const [loading, setLoading] = useState(true);
  const [detailLoading, setDetailLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // 加载历史列表
  const loadSessions = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await listSessions({
        subject: subjectFilter || undefined,
        limit: 50,
      });
      setSessions(data);
    } catch {
      setError("加载历史记录失败");
    } finally {
      setLoading(false);
    }
  }, [subjectFilter]);

  useEffect(() => {
    loadSessions();
  }, [loadSessions]);

  // 查看会话详情
  const viewSession = async (sessionId: string) => {
    setDetailLoading(true);
    try {
      const detail = await getSession(sessionId);
      setSelectedSession(detail);
    } catch {
      setError("加载对话详情失败");
    } finally {
      setDetailLoading(false);
    }
  };

  // 返回列表
  const backToList = () => setSelectedSession(null);

  // 详情视图
  if (selectedSession) {
    return (
      <div className="flex h-full flex-col">
        <div className="flex items-center gap-3 border-b border-gray-200 bg-white px-4 py-3">
          <button
            onClick={backToList}
            className="rounded-lg p-1.5 text-gray-500 hover:bg-gray-100"
          >
            <ChevronLeft size={20} />
          </button>
          <div>
            <h2 className="text-sm font-semibold text-gray-800">
              {selectedSession.topic || selectedSession.subject || "解题对话"}
            </h2>
            <p className="text-xs text-gray-400">
              {getModeLabel(selectedSession.mode)} |{" "}
              <span className={getVerificationColor(selectedSession.verification_status)}>
                {getVerificationLabel(selectedSession.verification_status)}
              </span>
            </p>
          </div>
        </div>
        <div className="flex-1 overflow-y-auto bg-gray-50 py-4">
          {selectedSession.messages.map((msg) => (
            <ChatMessage
              key={msg.id}
              role={msg.role}
              content={msg.content}
              imagePath={msg.image_path}
              timestamp={msg.created_at}
            />
          ))}
        </div>
      </div>
    );
  }

  // 列表视图
  return (
    <div className="flex h-full flex-col">
      <div className="flex items-center justify-between border-b border-gray-200 bg-white px-4 py-3 lg:px-6">
        <h1 className="text-lg font-semibold text-gray-800">解题历史</h1>
        <div className="flex items-center gap-2">
          <Filter size={16} className="text-gray-400" />
          <select
            value={subjectFilter}
            onChange={(e) => setSubjectFilter(e.target.value)}
            className="rounded-lg border border-gray-300 px-3 py-1.5 text-sm text-gray-700 focus:border-indigo-400 focus:outline-none"
          >
            <option value="">全部学科</option>
            {SUBJECTS.map((s) => (
              <option key={s} value={s}>{s}</option>
            ))}
          </select>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-4 lg:p-6">
        {loading ? (
          <div className="flex items-center justify-center py-12">
            <p className="text-gray-400">加载中...</p>
          </div>
        ) : error ? (
          <div className="rounded-lg bg-red-50 p-4 text-center text-sm text-red-600">
            {error}
          </div>
        ) : sessions.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-12 text-center">
            <MessageSquare size={48} className="mb-3 text-gray-300" />
            <p className="text-gray-500">暂无解题记录</p>
            <p className="mt-1 text-sm text-gray-400">去解题页面开始你的第一道题吧</p>
          </div>
        ) : (
          <div className="space-y-3">
            {sessions.map((session) => (
              <button
                key={session.id}
                onClick={() => viewSession(session.id)}
                disabled={detailLoading}
                className={cn(
                  "w-full rounded-xl bg-white p-4 text-left shadow-sm border border-gray-100 transition-all hover:shadow-md hover:border-indigo-200",
                  detailLoading && "opacity-50 cursor-not-allowed"
                )}
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="rounded-full bg-indigo-50 px-2 py-0.5 text-xs font-medium text-indigo-600">
                        {session.subject || "未知"}
                      </span>
                      <span className="text-xs text-gray-400">
                        {getModeLabel(session.mode)}
                      </span>
                      <span className={cn("text-xs", getVerificationColor(session.verification_status))}>
                        {getVerificationLabel(session.verification_status)}
                      </span>
                    </div>
                    <p className="text-sm font-medium text-gray-800 truncate">
                      {session.topic || truncateText(session.question_text || "图片题目", 60)}
                    </p>
                  </div>
                  <div className="ml-4 shrink-0 text-right">
                    <p className="text-xs text-gray-400">
                      {formatRelativeTime(session.created_at)}
                    </p>
                    <p className="mt-1 text-xs text-gray-400">
                      {session.message_count} 条消息
                    </p>
                  </div>
                </div>
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
