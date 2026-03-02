"use client";

import { useMemo } from "react";
import katex from "katex";
import type { RecommendedExercise } from "@/lib/types";

interface ExerciseRecommendProps {
  exercises: RecommendedExercise[];
}

/** 简单渲染含 LaTeX 的文本 */
function renderContent(text: string): string {
  let result = text.replace(/\$\$([\s\S]*?)\$\$/g, (_, latex: string) => {
    try {
      return katex.renderToString(latex.trim(), {
        displayMode: true,
        throwOnError: false,
      });
    } catch {
      return latex;
    }
  });
  result = result.replace(
    /(?<!\$)\$(?!\$)((?:[^$\\]|\\.)+?)\$(?!\$)/g,
    (_, latex: string) => {
      try {
        return katex.renderToString(latex.trim(), {
          displayMode: false,
          throwOnError: false,
        });
      } catch {
        return latex;
      }
    }
  );
  return result;
}

export default function ExerciseRecommend({ exercises }: ExerciseRecommendProps) {
  if (!exercises || exercises.length === 0) {
    return (
      <div className="py-8 text-center text-sm text-gray-400">
        暂无推荐练习题
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {exercises.map((ex, i) => (
        <ExerciseCard key={ex.id || i} exercise={ex} index={i} />
      ))}
    </div>
  );
}

function ExerciseCard({
  exercise,
  index,
}: {
  exercise: RecommendedExercise;
  index: number;
}) {
  const rendered = useMemo(
    () => renderContent(exercise.content),
    [exercise.content]
  );

  const difficultyStars = Array.from({ length: 5 }, (_, i) =>
    i < exercise.difficulty ? "text-yellow-400" : "text-gray-200"
  );

  return (
    <div className="rounded-xl bg-white p-5 shadow-sm border border-gray-100">
      <div className="mb-2 flex items-center justify-between">
        <span className="text-xs font-medium text-gray-400">
          练习 {index + 1}
        </span>
        <div className="flex items-center gap-0.5">
          {difficultyStars.map((color, i) => (
            <svg
              key={i}
              className={`h-3.5 w-3.5 ${color}`}
              fill="currentColor"
              viewBox="0 0 20 20"
            >
              <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
            </svg>
          ))}
        </div>
      </div>

      {/* 题目内容 */}
      <div
        className="prose prose-sm max-w-none text-sm text-gray-800"
        dangerouslySetInnerHTML={{ __html: rendered }}
      />

      {/* 知识点标签 */}
      <div className="mt-3 flex flex-wrap gap-1.5">
        {exercise.knowledge_points.map((kp, j) => (
          <span
            key={j}
            className="rounded-full bg-indigo-50 px-2.5 py-0.5 text-xs text-indigo-600"
          >
            {kp}
          </span>
        ))}
      </div>

      {/* 推荐原因 */}
      <p className="mt-2 text-xs text-gray-400">
        推荐原因: {exercise.reason}
      </p>
    </div>
  );
}
