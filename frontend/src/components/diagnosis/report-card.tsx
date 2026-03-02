"use client";

import type { DiagnosisReportDetail } from "@/lib/types";
import KnowledgeRadarChart from "./radar-chart";

interface ReportCardProps {
  report: DiagnosisReportDetail;
}

export default function ReportCard({ report }: ReportCardProps) {
  const scoreColor =
    (report.overall_score ?? 0) >= 80
      ? "text-green-600"
      : (report.overall_score ?? 0) >= 60
        ? "text-yellow-600"
        : "text-red-600";

  return (
    <div className="space-y-6">
      {/* 总体评分 */}
      <div className="flex items-center justify-between rounded-xl bg-white p-6 shadow-sm border border-gray-100">
        <div>
          <h3 className="text-sm font-medium text-gray-500">总体评分</h3>
          <p className={`mt-1 text-4xl font-bold ${scoreColor}`}>
            {report.overall_score ?? "--"}
            <span className="ml-1 text-lg text-gray-400">/ 100</span>
          </p>
        </div>
        <div className="text-right text-sm text-gray-500">
          <p>范围: {report.scope === "full" ? "全部" : report.scope === "subject" ? "单科" : "近期"}</p>
          {report.subject && <p>学科: {report.subject}</p>}
        </div>
      </div>

      {/* 知识点雷达图 */}
      <div className="rounded-xl bg-white p-6 shadow-sm border border-gray-100">
        <h3 className="mb-4 text-sm font-semibold text-gray-700">知识点掌握度</h3>
        <KnowledgeRadarChart data={report.knowledge_gaps} />
      </div>

      {/* 五维分析 */}
      <div className="grid gap-4 sm:grid-cols-2">
        {/* 思维路径 */}
        {report.thinking_patterns.length > 0 && (
          <div className="rounded-xl bg-white p-5 shadow-sm border border-gray-100">
            <h4 className="mb-3 text-sm font-semibold text-gray-700">思维路径分析</h4>
            <div className="space-y-2">
              {report.thinking_patterns.map((p, i) => (
                <div key={i} className="flex items-start gap-2">
                  <span className="mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-violet-100 text-xs text-violet-600">
                    {i + 1}
                  </span>
                  <div>
                    <p className="text-sm font-medium text-gray-700">{p.pattern_name}</p>
                    <p className="text-xs text-gray-500">{p.description}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* 习惯诊断 */}
        {report.habit_analysis.length > 0 && (
          <div className="rounded-xl bg-white p-5 shadow-sm border border-gray-100">
            <h4 className="mb-3 text-sm font-semibold text-gray-700">解题习惯诊断</h4>
            <div className="space-y-3">
              {report.habit_analysis.map((h, i) => (
                <div key={i}>
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-700">{h.habit_name}</span>
                    <span className="text-sm font-medium text-gray-600">{h.score}%</span>
                  </div>
                  <div className="mt-1 h-2 rounded-full bg-gray-100">
                    <div
                      className="h-2 rounded-full bg-indigo-500 transition-all"
                      style={{ width: `${h.score}%` }}
                    />
                  </div>
                  <p className="mt-0.5 text-xs text-gray-400">{h.description}</p>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* 认知水平 */}
        {report.cognitive_level.length > 0 && (
          <div className="rounded-xl bg-white p-5 shadow-sm border border-gray-100 sm:col-span-2">
            <h4 className="mb-3 text-sm font-semibold text-gray-700">认知水平评估</h4>
            <div className="flex flex-wrap gap-3">
              {report.cognitive_level.map((c, i) => (
                <div
                  key={i}
                  className="flex-1 min-w-[120px] rounded-lg bg-gray-50 p-3 text-center"
                >
                  <p className="text-xs text-gray-500">{c.dimension}</p>
                  <p className="mt-1 text-2xl font-bold text-indigo-600">L{c.level}</p>
                  <p className="mt-0.5 text-xs text-gray-400">{c.description}</p>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
