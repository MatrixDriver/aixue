// ============================================================
// Axios API 客户端 + JWT Bearer Token 拦截器
// ============================================================

import axios from "axios";
import { getToken, removeToken } from "./auth";
import type {
  TokenResponse,
  RegisterRequest,
  LoginRequest,
  User,
  UserUpdateRequest,
  UserStats,
  SolveResponse,
  FollowUpResponse,
  SessionSummary,
  SessionDetail,
  DiagnosisResponse,
  DiagnosisReportSummary,
  DiagnosisReportDetail,
  ExamImportResponse,
} from "./types";

const API_BASE =
  typeof window !== "undefined" && process.env.NEXT_PUBLIC_API_URL
    ? `${process.env.NEXT_PUBLIC_API_URL}/api`
    : "/api";

const api = axios.create({
  baseURL: API_BASE,
  timeout: 180000, // 图片 OCR + 解题可能较慢，180s 超时
});

// 请求拦截器：自动附加 JWT Token
api.interceptors.request.use((config) => {
  const token = getToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// 响应拦截器：处理 401 未授权（Token 过期/无效）
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      removeToken();
      // 跳转到登录页（避免 SSR 错误）
      if (typeof window !== "undefined") {
        window.location.href = "/login";
      }
    }
    return Promise.reject(error);
  }
);

// ============================================================
// 认证 API
// ============================================================

export async function register(data: RegisterRequest): Promise<TokenResponse> {
  const res = await api.post<TokenResponse>("/auth/register", {
    ...data,
    subjects: data.subjects.join(","),
  });
  return res.data;
}

export async function login(data: LoginRequest): Promise<TokenResponse> {
  const res = await api.post<TokenResponse>("/auth/login", data);
  return res.data;
}

// ============================================================
// 用户 API
// ============================================================

export async function getMe(): Promise<User> {
  const res = await api.get<User>("/users/me");
  return res.data;
}

export async function updateMe(data: UserUpdateRequest): Promise<User> {
  const payload: Record<string, unknown> = { ...data };
  if (data.subjects) {
    payload.subjects = data.subjects.join(",");
  }
  const res = await api.put<User>("/users/me", payload);
  return res.data;
}

export async function getMyStats(): Promise<UserStats> {
  const res = await api.get<UserStats>("/users/me/stats");
  return res.data;
}

// ============================================================
// 解题 API
// ============================================================

export async function solveQuestion(params: {
  image?: File;
  text?: string;
  subject?: string;
  mode: string;
  session_id?: string;
}): Promise<SolveResponse> {
  const formData = new FormData();
  if (params.image) formData.append("image", params.image);
  if (params.text) formData.append("text", params.text);
  if (params.subject) formData.append("subject", params.subject);
  formData.append("mode", params.mode);
  if (params.session_id) formData.append("session_id", params.session_id);

  const res = await api.post<SolveResponse>("/solve", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return res.data;
}

export async function followUp(
  sessionId: string,
  message: string
): Promise<FollowUpResponse> {
  const formData = new FormData();
  formData.append("message", message);
  const res = await api.post<FollowUpResponse>(
    `/solve/${sessionId}/follow-up`,
    formData,
    { headers: { "Content-Type": "multipart/form-data" } }
  );
  return res.data;
}

export async function listSessions(params?: {
  subject?: string;
  limit?: number;
  offset?: number;
}): Promise<SessionSummary[]> {
  const res = await api.get<SessionSummary[]>("/sessions", { params });
  return res.data;
}

export async function getSession(sessionId: string): Promise<SessionDetail> {
  const res = await api.get<SessionDetail>(`/sessions/${sessionId}`);
  return res.data;
}

// ============================================================
// 学情诊断 API
// ============================================================

export async function runDiagnosis(params: {
  scope: string;
  subject?: string;
}): Promise<DiagnosisResponse> {
  const formData = new FormData();
  formData.append("scope", params.scope);
  if (params.subject) formData.append("subject", params.subject);
  const res = await api.post<DiagnosisResponse>("/diagnosis/analyze", formData);
  return res.data;
}

export async function importExam(
  images: File[]
): Promise<ExamImportResponse> {
  const formData = new FormData();
  images.forEach((img) => formData.append("images", img));
  const res = await api.post<ExamImportResponse>(
    "/diagnosis/import-exam",
    formData,
    { headers: { "Content-Type": "multipart/form-data" } }
  );
  return res.data;
}

export async function listDiagnosisReports(): Promise<
  DiagnosisReportSummary[]
> {
  const res = await api.get<DiagnosisReportSummary[]>("/diagnosis/reports");
  return res.data;
}

export async function getDiagnosisReport(
  reportId: string
): Promise<DiagnosisReportDetail> {
  const res = await api.get<DiagnosisReportDetail>(
    `/diagnosis/reports/${reportId}`
  );
  return res.data;
}

export default api;
