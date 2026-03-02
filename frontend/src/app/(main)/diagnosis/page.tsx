"use client";

import { useEffect, useState, useRef } from "react";
import { useDiagnosis } from "@/hooks/use-diagnosis";
import ReportCard from "@/components/diagnosis/report-card";
import WeakPointList from "@/components/diagnosis/weak-point-list";
import ExerciseRecommend from "@/components/diagnosis/exercise-recommend";
import { SUBJECTS, formatDate, cn } from "@/lib/utils";
import {
  BarChart3,
  Upload,
  ChevronLeft,
  FileText,
  Loader2,
  AlertCircle,
} from "lucide-react";

type TabKey = "overview" | "weak-points" | "exercises";

export default function DiagnosisPage() {
  const {
    reports,
    currentReport,
    loading,
    analyzing,
    importing,
    error,
    loadReports,
    viewReport,
    analyze,
    importExamImages,
    clearCurrentReport,
  } = useDiagnosis();

  const [scope, setScope] = useState("full");
  const [subject, setSubject] = useState("");
  const [activeTab, setActiveTab] = useState<TabKey>("overview");
  const [importResult, setImportResult] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    loadReports();
  }, [loadReports]);

  // 触发诊断
  const handleAnalyze = async () => {
    const result = await analyze(scope, subject || undefined);
    if (result) {
      // 查看刚生成的报告
      viewReport(result.report_id);
    }
  };

  // 试卷上传
  const handleImportExam = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (!files || files.length === 0) return;
    const images = Array.from(files);
    const result = await importExamImages(images);
    if (result) {
      setImportResult(
        `成功导入 ${result.imported_count} 道题，正确 ${result.correct_count} 题，错误 ${result.wrong_count} 题`
      );
    }
    if (fileInputRef.current) fileInputRef.current.value = "";
  };

  // 查看报告详情
  if (currentReport) {
    const tabs: { key: TabKey; label: string }[] = [
      { key: "overview", label: "总览" },
      { key: "weak-points", label: "薄弱知识点" },
      { key: "exercises", label: "推荐练习" },
    ];

    return (
      <div className="flex h-full flex-col">
        {/* 标题栏 */}
        <div className="flex items-center gap-3 border-b border-gray-200 bg-white px-4 py-3">
          <button
            onClick={clearCurrentReport}
            className="rounded-lg p-1.5 text-gray-500 hover:bg-gray-100"
          >
            <ChevronLeft size={20} />
          </button>
          <h2 className="text-lg font-semibold text-gray-800">诊断报告</h2>
        </div>

        {/* Tab 切换 */}
        <div className="flex gap-1 border-b border-gray-200 bg-white px-4">
          {tabs.map((tab) => (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key)}
              className={cn(
                "border-b-2 px-4 py-2.5 text-sm font-medium transition-colors",
                activeTab === tab.key
                  ? "border-indigo-600 text-indigo-600"
                  : "border-transparent text-gray-500 hover:text-gray-700"
              )}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* Tab 内容 */}
        <div className="flex-1 overflow-y-auto p-4 lg:p-6">
          {activeTab === "overview" && <ReportCard report={currentReport} />}
          {activeTab === "weak-points" && (
            <WeakPointList gaps={currentReport.knowledge_gaps} />
          )}
          {activeTab === "exercises" && (
            <ExerciseRecommend exercises={currentReport.recommendations} />
          )}
        </div>
      </div>
    );
  }

  // 列表视图
  return (
    <div className="flex h-full flex-col">
      <div className="border-b border-gray-200 bg-white px-4 py-3 lg:px-6">
        <h1 className="text-lg font-semibold text-gray-800">学情诊断</h1>
      </div>

      <div className="flex-1 overflow-y-auto p-4 lg:p-6">
        {/* 错误提示 */}
        {error && (
          <div className="mb-4 flex items-center gap-2 rounded-lg bg-red-50 px-4 py-3 text-sm text-red-600">
            <AlertCircle size={16} />
            {error}
          </div>
        )}

        {/* 导入成功提示 */}
        {importResult && (
          <div className="mb-4 rounded-lg bg-green-50 px-4 py-3 text-sm text-green-600">
            {importResult}
            <button
              onClick={() => setImportResult(null)}
              className="ml-2 underline"
            >
              关闭
            </button>
          </div>
        )}

        {/* 操作面板 */}
        <div className="mb-6 grid gap-4 sm:grid-cols-2">
          {/* 发起诊断 */}
          <div className="rounded-xl bg-white p-5 shadow-sm border border-gray-100">
            <h3 className="mb-3 flex items-center gap-2 text-sm font-semibold text-gray-700">
              <BarChart3 size={16} className="text-indigo-500" />
              发起诊断分析
            </h3>
            <div className="space-y-3">
              <div>
                <label className="mb-1 block text-xs text-gray-500">
                  诊断范围
                </label>
                <select
                  value={scope}
                  onChange={(e) => setScope(e.target.value)}
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-indigo-400 focus:outline-none"
                >
                  <option value="full">全科诊断</option>
                  <option value="subject">单科诊断</option>
                  <option value="recent">近期诊断</option>
                </select>
              </div>
              {scope === "subject" && (
                <div>
                  <label className="mb-1 block text-xs text-gray-500">
                    选择学科
                  </label>
                  <select
                    value={subject}
                    onChange={(e) => setSubject(e.target.value)}
                    className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-indigo-400 focus:outline-none"
                  >
                    <option value="">请选择</option>
                    {SUBJECTS.map((s) => (
                      <option key={s} value={s}>
                        {s}
                      </option>
                    ))}
                  </select>
                </div>
              )}
              <button
                onClick={handleAnalyze}
                disabled={analyzing || (scope === "subject" && !subject)}
                className="w-full rounded-lg bg-indigo-600 py-2 text-sm font-medium text-white transition-colors hover:bg-indigo-700 disabled:cursor-not-allowed disabled:opacity-50"
              >
                {analyzing ? (
                  <span className="flex items-center justify-center gap-2">
                    <Loader2 size={16} className="animate-spin" />
                    分析中...
                  </span>
                ) : (
                  "开始诊断"
                )}
              </button>
            </div>
          </div>

          {/* 试卷上传 */}
          <div className="rounded-xl bg-white p-5 shadow-sm border border-gray-100">
            <h3 className="mb-3 flex items-center gap-2 text-sm font-semibold text-gray-700">
              <Upload size={16} className="text-emerald-500" />
              上传试卷
            </h3>
            <p className="mb-3 text-xs text-gray-500">
              拍照上传试卷，AI 自动识别题目并判定对错，导入到你的解题记录中。
            </p>
            <button
              onClick={() => fileInputRef.current?.click()}
              disabled={importing}
              className="w-full rounded-lg border-2 border-dashed border-gray-300 py-6 text-sm text-gray-500 transition-colors hover:border-indigo-300 hover:text-indigo-500 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {importing ? (
                <span className="flex items-center justify-center gap-2">
                  <Loader2 size={16} className="animate-spin" />
                  导入中...
                </span>
              ) : (
                "点击上传试卷图片（可多张）"
              )}
            </button>
            <input
              ref={fileInputRef}
              type="file"
              accept="image/*"
              multiple
              className="hidden"
              onChange={handleImportExam}
            />
          </div>
        </div>

        {/* 历史报告列表 */}
        <div>
          <h3 className="mb-3 text-sm font-semibold text-gray-700">
            历史诊断报告
          </h3>
          {loading ? (
            <div className="py-8 text-center text-sm text-gray-400">
              加载中...
            </div>
          ) : reports.length === 0 ? (
            <div className="flex flex-col items-center py-8 text-center">
              <FileText size={40} className="mb-2 text-gray-300" />
              <p className="text-sm text-gray-500">暂无诊断报告</p>
              <p className="mt-1 text-xs text-gray-400">
                完成一些解题后，即可发起学情诊断
              </p>
            </div>
          ) : (
            <div className="space-y-2">
              {reports.map((report) => (
                <button
                  key={report.id}
                  onClick={() => viewReport(report.id)}
                  className="w-full rounded-lg bg-white p-4 text-left shadow-sm border border-gray-100 transition-all hover:shadow-md hover:border-indigo-200"
                >
                  <div className="flex items-center justify-between">
                    <div>
                      <span className="rounded-full bg-indigo-50 px-2 py-0.5 text-xs font-medium text-indigo-600">
                        {report.scope === "full"
                          ? "全科"
                          : report.scope === "subject"
                            ? report.subject || "单科"
                            : "近期"}
                      </span>
                      <span className="ml-2 text-sm text-gray-600">
                        总评{" "}
                        <strong className="text-gray-800">
                          {report.overall_score ?? "--"}
                        </strong>{" "}
                        分
                      </span>
                    </div>
                    <span className="text-xs text-gray-400">
                      {formatDate(report.created_at)}
                    </span>
                  </div>
                </button>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
