"use client";

import { useState } from "react";
import Link from "next/link";
import { useAuth } from "@/hooks/use-auth";
import { GRADES, SUBJECTS } from "@/lib/utils";
import type { Grade } from "@/lib/types";

export default function RegisterPage() {
  const { register, loading, error } = useAuth();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [name, setName] = useState("");
  const [grade, setGrade] = useState<Grade | "">("");
  const [selectedSubjects, setSelectedSubjects] = useState<string[]>([]);
  const [localError, setLocalError] = useState("");

  const toggleSubject = (subject: string) => {
    setSelectedSubjects((prev) =>
      prev.includes(subject)
        ? prev.filter((s) => s !== subject)
        : [...prev, subject]
    );
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLocalError("");

    if (!username.trim()) {
      setLocalError("请输入用户名");
      return;
    }
    if (username.trim().length < 3) {
      setLocalError("用户名至少3个字符");
      return;
    }
    if (!name.trim()) {
      setLocalError("请输入姓名");
      return;
    }
    if (!password || password.length < 6) {
      setLocalError("密码至少6个字符");
      return;
    }
    if (password !== confirmPassword) {
      setLocalError("两次密码输入不一致");
      return;
    }
    if (!grade) {
      setLocalError("请选择年级");
      return;
    }
    if (selectedSubjects.length === 0) {
      setLocalError("请至少选择一个学科");
      return;
    }

    try {
      await register({
        username: username.trim(),
        password,
        name: name.trim(),
        grade: grade as Grade,
        subjects: selectedSubjects,
      });
    } catch {
      // error 已由 hook 处理
    }
  };

  const displayError = localError || error;

  return (
    <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100 px-4 py-8">
      <div className="w-full max-w-md">
        {/* Logo 和标题 */}
        <div className="mb-6 text-center">
          <h1 className="text-4xl font-bold text-indigo-600">AIXue</h1>
          <p className="mt-2 text-lg text-gray-600">爱学 - AI 学习助手</p>
        </div>

        {/* 注册表单 */}
        <div className="rounded-2xl bg-white p-8 shadow-lg">
          <h2 className="mb-6 text-2xl font-semibold text-gray-800">注册</h2>

          {displayError && (
            <div className="mb-4 rounded-lg bg-red-50 p-3 text-sm text-red-600">
              {displayError}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            {/* 用户名 */}
            <div>
              <label
                htmlFor="username"
                className="mb-1 block text-sm font-medium text-gray-700"
              >
                用户名
              </label>
              <input
                id="username"
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                className="w-full rounded-lg border border-gray-300 px-4 py-2.5 text-gray-900 focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-200"
                placeholder="至少3个字符"
                autoComplete="username"
              />
            </div>

            {/* 姓名 */}
            <div>
              <label
                htmlFor="name"
                className="mb-1 block text-sm font-medium text-gray-700"
              >
                姓名
              </label>
              <input
                id="name"
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                className="w-full rounded-lg border border-gray-300 px-4 py-2.5 text-gray-900 focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-200"
                placeholder="你的真实姓名"
              />
            </div>

            {/* 密码 */}
            <div>
              <label
                htmlFor="password"
                className="mb-1 block text-sm font-medium text-gray-700"
              >
                密码
              </label>
              <input
                id="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full rounded-lg border border-gray-300 px-4 py-2.5 text-gray-900 focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-200"
                placeholder="至少6个字符"
                autoComplete="new-password"
              />
            </div>

            {/* 确认密码 */}
            <div>
              <label
                htmlFor="confirmPassword"
                className="mb-1 block text-sm font-medium text-gray-700"
              >
                确认密码
              </label>
              <input
                id="confirmPassword"
                type="password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                className="w-full rounded-lg border border-gray-300 px-4 py-2.5 text-gray-900 focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-200"
                placeholder="再次输入密码"
                autoComplete="new-password"
              />
            </div>

            {/* 年级选择 */}
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

            {/* 学科多选 */}
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
                    className={`rounded-full px-4 py-1.5 text-sm font-medium transition-colors ${
                      selectedSubjects.includes(s)
                        ? "bg-indigo-600 text-white"
                        : "bg-gray-100 text-gray-600 hover:bg-gray-200"
                    }`}
                  >
                    {s}
                  </button>
                ))}
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full rounded-lg bg-indigo-600 py-2.5 text-white font-medium transition-colors hover:bg-indigo-700 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {loading ? "注册中..." : "注册"}
            </button>
          </form>

          <p className="mt-6 text-center text-sm text-gray-500">
            已有账号？{" "}
            <Link
              href="/login"
              className="font-medium text-indigo-600 hover:text-indigo-500"
            >
              立即登录
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
