// ============================================================
// AIXue 前端 TypeScript 类型定义
// ============================================================

// --- 用户相关 ---

/** 年级选项 */
export type Grade =
  | "初一"
  | "初二"
  | "初三"
  | "高一"
  | "高二"
  | "高三";

/** 学科选项 */
export type Subject = "数学" | "物理" | "化学" | "生物";

/** 用户信息 */
export interface User {
  id: string;
  username: string;
  name: string;
  grade: Grade;
  subjects: string; // 逗号分隔
  created_at: string;
  updated_at: string;
}

/** 注册请求 */
export interface RegisterRequest {
  username: string;
  password: string;
  name: string;
  grade: Grade;
  subjects: string[];
}

/** 登录请求 */
export interface LoginRequest {
  username: string;
  password: string;
}

/** Token 响应 */
export interface TokenResponse {
  access_token: string;
  token_type: string;
}

/** 用户更新请求 */
export interface UserUpdateRequest {
  name?: string;
  grade?: Grade;
  subjects?: string[];
}

/** 用户解题统计 */
export interface UserStats {
  total_sessions: number;
  total_by_subject: Record<string, number>;
  recent_7_days: number;
  verified_count: number;
  accuracy_rate: number;
}

// --- 解题相关 ---

/** 解题模式 */
export type SolveMode = "socratic" | "direct";

/** 消息角色 */
export type MessageRole = "user" | "assistant" | "system";

/** 对话消息 */
export interface Message {
  id: string;
  session_id: string;
  role: MessageRole;
  content: string;
  image_path?: string;
  created_at: string;
}

/** 解题会话摘要 */
export interface SessionSummary {
  id: string;
  subject: string;
  topic?: string;
  mode: SolveMode;
  question_text?: string;
  image_path?: string;
  verification_status: string;
  created_at: string;
  message_count: number;
}

/** 解题会话详情 */
export interface SessionDetail extends SessionSummary {
  messages: Message[];
  verified_answer?: string;
  confidence?: number;
}

/** 解题响应（后端扁平结构） */
export interface SolveResponse {
  session_id: string;
  subject: string;
  question: string;
  content: string;
  mode: string;
  verified: boolean;
  attempts: number;
  sympy_result?: string | null;
  error?: string | null;
}

/** 追问响应 */
export interface FollowUpResponse {
  session_id: string;
  content: string;
  mode: string;
  error?: string | null;
}

// --- 学情诊断相关 ---

/** 诊断范围 */
export type DiagnosisScope = "full" | "subject" | "recent";

/** 诊断报告摘要 */
export interface DiagnosisReportSummary {
  id: string;
  scope: DiagnosisScope;
  subject?: string;
  overall_score?: number;
  created_at: string;
}

/** 知识漏洞 */
export interface KnowledgeGap {
  knowledge_point: string;
  mastery_level: number; // 0-100
  error_count: number;
  suggestion: string;
}

/** 思维路径 */
export interface ThinkingPattern {
  pattern_name: string;
  frequency: number;
  description: string;
}

/** 习惯分析 */
export interface HabitAnalysis {
  habit_name: string;
  score: number; // 0-100
  description: string;
}

/** 认知水平 */
export interface CognitiveLevel {
  dimension: string;
  level: number; // 1-6 (Bloom's)
  description: string;
}

/** 推荐练习题 */
export interface RecommendedExercise {
  id: string;
  content: string;
  difficulty: number;
  knowledge_points: string[];
  reason: string;
}

/** 诊断报告详情 */
export interface DiagnosisReportDetail {
  id: string;
  scope: DiagnosisScope;
  subject?: string;
  overall_score?: number;
  knowledge_gaps: KnowledgeGap[];
  thinking_patterns: ThinkingPattern[];
  habit_analysis: HabitAnalysis[];
  cognitive_level: CognitiveLevel[];
  recommendations: RecommendedExercise[];
  created_at: string;
}

/** 诊断响应 */
export interface DiagnosisResponse {
  report_id: string;
  overall_score: number;
  knowledge_gaps: KnowledgeGap[];
  thinking_patterns: ThinkingPattern[];
  habit_analysis: HabitAnalysis[];
  cognitive_level: CognitiveLevel[];
  recommendations: RecommendedExercise[];
}

/** 试卷导入响应 */
export interface ExamImportResponse {
  imported_count: number;
  correct_count: number;
  wrong_count: number;
  session_ids: string[];
}

// --- API 通用 ---

/** API 错误响应 */
export interface ApiError {
  detail: string;
}

/** 分页参数 */
export interface PaginationParams {
  limit?: number;
  offset?: number;
}
