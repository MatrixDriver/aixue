"use client";

// ============================================================
// 学情诊断数据 Hook
// ============================================================

import { useState, useCallback } from "react";
import {
  runDiagnosis,
  importExam,
  listDiagnosisReports,
  getDiagnosisReport,
} from "@/lib/api";
import type {
  DiagnosisReportSummary,
  DiagnosisReportDetail,
  DiagnosisResponse,
  ExamImportResponse,
} from "@/lib/types";

interface DiagnosisState {
  reports: DiagnosisReportSummary[];
  currentReport: DiagnosisReportDetail | null;
  lastAnalysis: DiagnosisResponse | null;
  loading: boolean;
  analyzing: boolean;
  importing: boolean;
  error: string | null;
}

export function useDiagnosis() {
  const [state, setState] = useState<DiagnosisState>({
    reports: [],
    currentReport: null,
    lastAnalysis: null,
    loading: false,
    analyzing: false,
    importing: false,
    error: null,
  });

  // 加载报告列表
  const loadReports = useCallback(async () => {
    setState((prev) => ({ ...prev, loading: true, error: null }));
    try {
      const reports = await listDiagnosisReports();
      setState((prev) => ({ ...prev, reports, loading: false }));
    } catch {
      setState((prev) => ({
        ...prev,
        loading: false,
        error: "加载报告列表失败",
      }));
    }
  }, []);

  // 查看报告详情
  const viewReport = useCallback(async (reportId: string) => {
    setState((prev) => ({ ...prev, loading: true, error: null }));
    try {
      const report = await getDiagnosisReport(reportId);
      setState((prev) => ({ ...prev, currentReport: report, loading: false }));
    } catch {
      setState((prev) => ({
        ...prev,
        loading: false,
        error: "加载报告详情失败",
      }));
    }
  }, []);

  // 运行诊断分析
  const analyze = useCallback(
    async (scope: string, subject?: string) => {
      setState((prev) => ({ ...prev, analyzing: true, error: null }));
      try {
        const result = await runDiagnosis({ scope, subject });
        setState((prev) => ({
          ...prev,
          lastAnalysis: result,
          analyzing: false,
        }));
        // 刷新报告列表
        const reports = await listDiagnosisReports();
        setState((prev) => ({ ...prev, reports }));
        return result;
      } catch (err: unknown) {
        const message =
          (err as { response?: { data?: { detail?: string } } })?.response
            ?.data?.detail || "诊断分析失败";
        setState((prev) => ({
          ...prev,
          analyzing: false,
          error: message,
        }));
        return null;
      }
    },
    []
  );

  // 导入试卷
  const importExamImages = useCallback(
    async (images: File[]): Promise<ExamImportResponse | null> => {
      setState((prev) => ({ ...prev, importing: true, error: null }));
      try {
        const result = await importExam(images);
        setState((prev) => ({ ...prev, importing: false }));
        return result;
      } catch (err: unknown) {
        const message =
          (err as { response?: { data?: { detail?: string } } })?.response
            ?.data?.detail || "试卷导入失败";
        setState((prev) => ({
          ...prev,
          importing: false,
          error: message,
        }));
        return null;
      }
    },
    []
  );

  // 返回列表
  const clearCurrentReport = useCallback(() => {
    setState((prev) => ({ ...prev, currentReport: null }));
  }, []);

  return {
    reports: state.reports,
    currentReport: state.currentReport,
    lastAnalysis: state.lastAnalysis,
    loading: state.loading,
    analyzing: state.analyzing,
    importing: state.importing,
    error: state.error,
    loadReports,
    viewReport,
    analyze,
    importExamImages,
    clearCurrentReport,
  };
}
