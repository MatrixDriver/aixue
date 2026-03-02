"use client";

import {
  Radar,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  ResponsiveContainer,
  Tooltip,
} from "recharts";
import type { KnowledgeGap } from "@/lib/types";

interface KnowledgeRadarChartProps {
  data: KnowledgeGap[];
}

export default function KnowledgeRadarChart({ data }: KnowledgeRadarChartProps) {
  if (!data || data.length === 0) {
    return (
      <div className="flex h-64 items-center justify-center text-sm text-gray-400">
        暂无数据
      </div>
    );
  }

  const chartData = data.slice(0, 8).map((gap) => ({
    subject: gap.knowledge_point.length > 6
      ? gap.knowledge_point.slice(0, 6) + "..."
      : gap.knowledge_point,
    fullName: gap.knowledge_point,
    mastery: gap.mastery_level,
  }));

  return (
    <ResponsiveContainer width="100%" height={280}>
      <RadarChart data={chartData} cx="50%" cy="50%" outerRadius="75%">
        <PolarGrid stroke="#e5e7eb" />
        <PolarAngleAxis
          dataKey="subject"
          tick={{ fontSize: 12, fill: "#6b7280" }}
        />
        <PolarRadiusAxis
          angle={30}
          domain={[0, 100]}
          tick={{ fontSize: 10, fill: "#9ca3af" }}
        />
        <Radar
          name="掌握度"
          dataKey="mastery"
          stroke="#6366f1"
          fill="#6366f1"
          fillOpacity={0.3}
          strokeWidth={2}
        />
        <Tooltip
          formatter={(value: number | undefined) => [`${value ?? 0}%`, "掌握度"]}
          labelFormatter={(label: unknown) => {
            const labelStr = String(label);
            const item = chartData.find((d) => d.subject === labelStr);
            return item?.fullName || labelStr;
          }}
        />
      </RadarChart>
    </ResponsiveContainer>
  );
}
