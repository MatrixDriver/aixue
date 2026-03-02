"use client";

import { useState, useEffect } from "react";
import { useAuth } from "@/hooks/use-auth";
import { updateMe, getMyStats } from "@/lib/api";
import { GRADES, SUBJECTS, cn } from "@/lib/utils";
import { User, Save, Loader2, CheckCircle } from "lucide-react";
import type { Grade, UserStats } from "@/lib/types";

export default function ProfilePage() {
  const { user, refreshUser } = useAuth();
  const [name, setName] = useState("");
  const [grade, setGrade] = useState<Grade | "">("");
  const [selectedSubjects, setSelectedSubjects] = useState<string[]>([]);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [stats, setStats] = useState<UserStats | null>(null);
  const [statsLoading, setStatsLoading] = useState(true);

  // 初始化表单
  useEffect(() => {
    if (user) {
      setName(user.name);
      setGrade(user.grade);
      setSelectedSubjects(user.subjects ? user.subjects.split(",") : []);
    }
  }, [user]);

  // 加载统计数据
  useEffect(() => {
    setStatsLoading(true);
    getMyStats()
      .then(setStats)
      .catch(() => {
        // 统计数据加载失败不阻塞页面
      })
      .finally(() => setStatsLoading(false));
  }, []);

  const toggleSubject = (subject: string) => {
    setSelectedSubjects((prev) =>
      prev.includes(subject)
        ? prev.filter((s) => s !== subject)
        : [...prev, subject]
    );
  };

  const handleSave = async () => {
    if (!name.trim()) {
      setError("姓名不能为空");
      return;
    }
    if (!grade) {
      setError("请选择年级");
      return;
    }
    if (selectedSubjects.length === 0) {
      setError("请至少选择一个学科");
      return;
    }

    setSaving(true);
    setError(null);
    setSaved(false);

    try {
      await updateMe({
        name: name.trim(),
        grade: grade as Grade,
        subjects: selectedSubjects,
      });
      await refreshUser();
      setSaved(true);
      setTimeout(() => setSaved(false), 3000);
    } catch {
      setError("保存失败，请稍后重试");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="flex h-full flex-col">
      <div className="border-b border-gray-200 bg-white px-4 py-3 lg:px-6">
        <h1 className="text-lg font-semibold text-gray-800">个人信息</h1>
      </div>

      <div className="flex-1 overflow-y-auto p-4 lg:p-6">
        <div className="mx-auto max-w-2xl space-y-6">
          {/* 用户头像和基本信息 */}
          <div className="flex items-center gap-4 rounded-xl bg-white p-6 shadow-sm border border-gray-100">
            <div className="flex h-16 w-16 items-center justify-center rounded-full bg-indigo-100">
              <User size={32} className="text-indigo-600" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-gray-800">
                {user?.name || "未设置"}
              </h2>
              <p className="text-sm text-gray-500">
                @{user?.username || "unknown"} | {user?.grade || "未设置"}
              </p>
            </div>
          </div>

          {/* 解题统计 */}
          <div className="rounded-xl bg-white p-6 shadow-sm border border-gray-100">
            <h3 className="mb-4 text-sm font-semibold text-gray-700">
              解题统计
            </h3>
            {statsLoading ? (
              <p className="text-sm text-gray-400">加载中...</p>
            ) : stats ? (
              <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
                <div className="text-center">
                  <p className="text-2xl font-bold text-indigo-600">
                    {stats.total_sessions}
                  </p>
                  <p className="text-xs text-gray-500">总解题数</p>
                </div>
                <div className="text-center">
                  <p className="text-2xl font-bold text-emerald-600">
                    {stats.recent_7_days}
                  </p>
                  <p className="text-xs text-gray-500">近7天</p>
                </div>
                <div className="text-center">
                  <p className="text-2xl font-bold text-blue-600">
                    {stats.verified_count}
                  </p>
                  <p className="text-xs text-gray-500">已验证</p>
                </div>
                <div className="text-center">
                  <p className="text-2xl font-bold text-amber-600">
                    {Math.round(stats.accuracy_rate * 100)}%
                  </p>
                  <p className="text-xs text-gray-500">正确率</p>
                </div>
              </div>
            ) : (
              <p className="text-sm text-gray-400">暂无统计数据</p>
            )}

            {/* 分学科统计 */}
            {stats && stats.total_by_subject && (
              <div className="mt-4 border-t border-gray-100 pt-4">
                <p className="mb-2 text-xs font-medium text-gray-500">
                  分学科统计
                </p>
                <div className="flex flex-wrap gap-2">
                  {Object.entries(stats.total_by_subject).map(
                    ([subj, count]) => (
                      <span
                        key={subj}
                        className="rounded-full bg-gray-100 px-3 py-1 text-xs text-gray-600"
                      >
                        {subj}: {count} 题
                      </span>
                    )
                  )}
                </div>
              </div>
            )}
          </div>

          {/* 编辑个人信息 */}
          <div className="rounded-xl bg-white p-6 shadow-sm border border-gray-100">
            <h3 className="mb-4 text-sm font-semibold text-gray-700">
              编辑信息
            </h3>

            {error && (
              <div className="mb-4 rounded-lg bg-red-50 p-3 text-sm text-red-600">
                {error}
              </div>
            )}
            {saved && (
              <div className="mb-4 flex items-center gap-2 rounded-lg bg-green-50 p-3 text-sm text-green-600">
                <CheckCircle size={16} />
                保存成功
              </div>
            )}

            <div className="space-y-4">
              <div>
                <label className="mb-1 block text-sm font-medium text-gray-700">
                  姓名
                </label>
                <input
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className="w-full rounded-lg border border-gray-300 px-4 py-2.5 text-gray-900 focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-200"
                />
              </div>

              <div>
                <label className="mb-1 block text-sm font-medium text-gray-700">
                  年级
                </label>
                <select
                  value={grade}
                  onChange={(e) => setGrade(e.target.value as Grade | "")}
                  className="w-full rounded-lg border border-gray-300 px-4 py-2.5 text-gray-900 focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-200"
                >
                  <option value="">请选择年级</option>
                  {GRADES.map((g) => (
                    <option key={g} value={g}>
                      {g}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="mb-2 block text-sm font-medium text-gray-700">
                  重点学科（可多选）
                </label>
                <div className="flex flex-wrap gap-2">
                  {SUBJECTS.map((s) => (
                    <button
                      key={s}
                      type="button"
                      onClick={() => toggleSubject(s)}
                      className={cn(
                        "rounded-full px-4 py-1.5 text-sm font-medium transition-colors",
                        selectedSubjects.includes(s)
                          ? "bg-indigo-600 text-white"
                          : "bg-gray-100 text-gray-600 hover:bg-gray-200"
                      )}
                    >
                      {s}
                    </button>
                  ))}
                </div>
              </div>

              <button
                onClick={handleSave}
                disabled={saving}
                className="flex items-center gap-2 rounded-lg bg-indigo-600 px-6 py-2.5 text-sm font-medium text-white transition-colors hover:bg-indigo-700 disabled:cursor-not-allowed disabled:opacity-50"
              >
                {saving ? (
                  <Loader2 size={16} className="animate-spin" />
                ) : (
                  <Save size={16} />
                )}
                {saving ? "保存中..." : "保存修改"}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
