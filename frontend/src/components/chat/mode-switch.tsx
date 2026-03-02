"use client";

import { cn } from "@/lib/utils";
import type { SolveMode } from "@/lib/types";

interface ModeSwitchProps {
  mode: SolveMode;
  onChange: (mode: SolveMode) => void;
  disabled?: boolean;
}

export default function ModeSwitch({
  mode,
  onChange,
  disabled,
}: ModeSwitchProps) {
  return (
    <div className="flex items-center rounded-full bg-gray-100 p-1">
      <button
        type="button"
        onClick={() => onChange("socratic")}
        disabled={disabled}
        className={cn(
          "rounded-full px-4 py-1.5 text-sm font-medium transition-colors",
          mode === "socratic"
            ? "bg-indigo-600 text-white shadow-sm"
            : "text-gray-600 hover:text-gray-800",
          disabled && "cursor-not-allowed opacity-50"
        )}
      >
        苏格拉底引导
      </button>
      <button
        type="button"
        onClick={() => onChange("direct")}
        disabled={disabled}
        className={cn(
          "rounded-full px-4 py-1.5 text-sm font-medium transition-colors",
          mode === "direct"
            ? "bg-indigo-600 text-white shadow-sm"
            : "text-gray-600 hover:text-gray-800",
          disabled && "cursor-not-allowed opacity-50"
        )}
      >
        完整解答
      </button>
    </div>
  );
}
