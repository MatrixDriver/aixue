"use client";

// ============================================================
// 解题对话状态管理 Hook
// ============================================================

import { useState, useCallback } from "react";
import { solveQuestion, followUp } from "@/lib/api";
import type { Message, SolveMode } from "@/lib/types";

interface ChatState {
  messages: Message[];
  sessionId: string | null;
  mode: SolveMode;
  subject: string;
  loading: boolean;
  error: string | null;
}

export function useChat() {
  const [state, setState] = useState<ChatState>({
    messages: [],
    sessionId: null,
    mode: "socratic",
    subject: "",
    loading: false,
    error: null,
  });

  // 发送消息
  const sendMessage = useCallback(
    async (text: string, image: File | null) => {
      setState((prev) => ({ ...prev, loading: true, error: null }));

      // 添加用户消息到列表（临时 ID）
      const userMsg: Message = {
        id: `temp-${Date.now()}`,
        session_id: state.sessionId || "",
        role: "user",
        content: text || "[图片]",
        created_at: new Date().toISOString(),
      };
      setState((prev) => ({
        ...prev,
        messages: [...prev.messages, userMsg],
      }));

      try {
        let response;

        if (state.sessionId) {
          // 追问模式
          response = await followUp(state.sessionId, text);
        } else {
          // 新题目
          response = await solveQuestion({
            text: text || undefined,
            image: image || undefined,
            subject: state.subject || undefined,
            mode: state.mode,
          });
        }

        // 添加 AI 回复
        setState((prev) => ({
          ...prev,
          messages: [...prev.messages, response.message],
          sessionId: response.session_id,
          loading: false,
        }));
      } catch (err: unknown) {
        const message =
          (err as { response?: { data?: { detail?: string } } })?.response
            ?.data?.detail || "发送失败，请稍后重试";
        setState((prev) => ({
          ...prev,
          loading: false,
          error: message,
        }));
      }
    },
    [state.sessionId, state.mode, state.subject]
  );

  // 切换模式
  const setMode = useCallback((mode: SolveMode) => {
    setState((prev) => ({ ...prev, mode }));
  }, []);

  // 切换学科
  const setSubject = useCallback((subject: string) => {
    setState((prev) => ({ ...prev, subject }));
  }, []);

  // 开始新对话
  const newChat = useCallback(() => {
    setState({
      messages: [],
      sessionId: null,
      mode: state.mode,
      subject: "",
      loading: false,
      error: null,
    });
  }, [state.mode]);

  // 加载已有对话
  const loadSession = useCallback(
    (sessionId: string, messages: Message[], mode: SolveMode) => {
      setState({
        messages,
        sessionId,
        mode,
        subject: "",
        loading: false,
        error: null,
      });
    },
    []
  );

  return {
    messages: state.messages,
    sessionId: state.sessionId,
    mode: state.mode,
    subject: state.subject,
    loading: state.loading,
    error: state.error,
    sendMessage,
    setMode,
    setSubject,
    newChat,
    loadSession,
  };
}
