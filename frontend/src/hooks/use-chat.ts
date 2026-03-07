"use client";

// ============================================================
// 解题对话状态管理 Hook
// ============================================================

import { useState, useCallback } from "react";
import { detectQuestions, solveQuestion, followUp } from "@/lib/api";
import type { Message, SolveMode, SolveResponse, FollowUpResponse, QuestionOption, DetectResponse } from "@/lib/types";

interface ChatState {
  messages: Message[];
  sessionId: string | null;
  mode: SolveMode;
  subject: string;
  loading: boolean;
  error: string | null;
  pendingImage: File | null;
  detecting: boolean;
  selectionDisabled: boolean;
}

export function useChat() {
  const [state, setState] = useState<ChatState>({
    messages: [],
    sessionId: null,
    mode: "socratic",
    subject: "",
    loading: false,
    error: null,
    pendingImage: null,
    detecting: false,
    selectionDisabled: false,
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
        localImageUrl: image ? URL.createObjectURL(image) : undefined,
        created_at: new Date().toISOString(),
      };
      setState((prev) => ({
        ...prev,
        messages: [...prev.messages, userMsg],
      }));

      try {
        let aiMsg: Message;
        let newSessionId: string;
        let ocrQuestion: string | undefined;

        if (state.sessionId) {
          // 追问模式
          const response: FollowUpResponse = await followUp(state.sessionId, text);
          newSessionId = response.session_id;
          aiMsg = {
            id: `ai-${Date.now()}`,
            session_id: response.session_id,
            role: "assistant",
            content: response.content,
            created_at: new Date().toISOString(),
          };
        } else {
          // 新题目
          if (image && !text) {
            // 仅图片，无 user_hint -> 触发多题检测
            setState((prev) => ({ ...prev, detecting: true }));
            try {
              const detectResult: DetectResponse = await detectQuestions(image);
              const completeQuestions = detectResult.questions.filter((q) => q.complete);

              if (completeQuestions.length === 1 && detectResult.question_count <= 1) {
                // 单题快速通道：直接解题
                const response: SolveResponse = await solveQuestion({
                  image,
                  mode: state.mode,
                });
                newSessionId = response.session_id;
                ocrQuestion = response.question;
                aiMsg = {
                  id: `ai-${Date.now()}`,
                  session_id: response.session_id,
                  role: "assistant",
                  content: response.content,
                  created_at: new Date().toISOString(),
                };
              } else {
                // 多题或全不完整 -> 返回选题消息
                setState((prev) => ({
                  ...prev,
                  detecting: false,
                  loading: false,
                  pendingImage: image,
                  messages: [...prev.messages, {
                    id: `detect-${Date.now()}`,
                    session_id: "",
                    role: "assistant" as const,
                    content: detectResult.message,
                    created_at: new Date().toISOString(),
                    type: "question_selection" as const,
                    questionOptions: detectResult.questions,
                  }],
                }));
                return; // 等待用户选择
              }
            } finally {
              setState((prev) => ({ ...prev, detecting: false }));
            }
          } else {
            // 有文字（可能含图片）-> 现有流程（user_hint 跳过检测）
            const response: SolveResponse = await solveQuestion({
              text: text || undefined,
              image: image || undefined,
              subject: state.subject || undefined,
              mode: state.mode,
            });
            newSessionId = response.session_id;
            ocrQuestion = response.question;
            aiMsg = {
              id: `ai-${Date.now()}`,
              session_id: response.session_id,
              role: "assistant",
              content: response.content,
              created_at: new Date().toISOString(),
            };
          }
        }

        // 添加 AI 回复，同时回填 OCR 文本到用户消息
        setState((prev) => ({
          ...prev,
          messages: prev.messages.map((msg) =>
            msg.id === userMsg.id && ocrQuestion !== undefined
              ? { ...msg, ocrText: ocrQuestion }
              : msg
          ).concat([aiMsg]),
          sessionId: newSessionId,
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

  // 选择单题
  const selectQuestion = useCallback(
    async (selected: QuestionOption) => {
      if (!state.pendingImage) return;
      setState((prev) => ({ ...prev, loading: true, selectionDisabled: true }));

      try {
        const response: SolveResponse = await solveQuestion({
          image: state.pendingImage,
          text: selected.label ? `第${selected.label}题` : `题目${selected.index}`,
          mode: state.mode,
        });

        const aiMsg: Message = {
          id: `ai-${Date.now()}`,
          session_id: response.session_id,
          role: "assistant",
          content: response.content,
          created_at: new Date().toISOString(),
        };

        setState((prev) => ({
          ...prev,
          messages: [...prev.messages, aiMsg],
          sessionId: response.session_id,
          loading: false,
          pendingImage: null,
        }));
      } catch (err: unknown) {
        const message =
          (err as { response?: { data?: { detail?: string } } })?.response
            ?.data?.detail || "解题失败，请稍后重试";
        setState((prev) => ({
          ...prev,
          loading: false,
          selectionDisabled: false,
          error: message,
        }));
      }
    },
    [state.pendingImage, state.mode]
  );

  // 全部解答
  const selectAll = useCallback(
    async () => {
      if (!state.pendingImage) return;
      // 找到选题消息中的完整题目
      const selectionMsg = state.messages.find((m) => m.type === "question_selection");
      const completeQuestions = selectionMsg?.questionOptions?.filter((q) => q.complete) || [];
      if (completeQuestions.length === 0) return;

      setState((prev) => ({ ...prev, loading: true, selectionDisabled: true }));

      const results: Message[] = [];
      const failures: string[] = [];

      for (const q of completeQuestions) {
        try {
          const response: SolveResponse = await solveQuestion({
            image: state.pendingImage!,
            text: q.label ? `第${q.label}题` : `题目${q.index}`,
            mode: state.mode,
          });
          results.push({
            id: `ai-${Date.now()}-${q.index}`,
            session_id: response.session_id,
            role: "assistant",
            content: `**第${q.label || q.index}题**\n\n${response.content}`,
            created_at: new Date().toISOString(),
          });
        } catch {
          failures.push(q.label || String(q.index));
        }
      }

      if (failures.length > 0) {
        results.push({
          id: `ai-fail-${Date.now()}`,
          session_id: "",
          role: "assistant",
          content: `以下题目解答失败：${failures.join("、")}，请稍后重试。`,
          created_at: new Date().toISOString(),
        });
      }

      setState((prev) => ({
        ...prev,
        messages: [...prev.messages, ...results],
        sessionId: results.length > 0 ? results[results.length - 1].session_id : prev.sessionId,
        loading: false,
        pendingImage: null,
      }));
    },
    [state.pendingImage, state.mode, state.messages]
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
    // 释放所有本地图片 Object URL
    state.messages.forEach((msg) => {
      if (msg.localImageUrl) {
        URL.revokeObjectURL(msg.localImageUrl);
      }
    });
    setState({
      messages: [],
      sessionId: null,
      mode: state.mode,
      subject: "",
      loading: false,
      error: null,
      pendingImage: null,
      detecting: false,
      selectionDisabled: false,
    });
  }, [state.mode, state.messages]);

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
        pendingImage: null,
        detecting: false,
        selectionDisabled: false,
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
    detecting: state.detecting,
    selectionDisabled: state.selectionDisabled,
    sendMessage,
    setMode,
    setSubject,
    newChat,
    loadSession,
    selectQuestion,
    selectAll,
  };
}
