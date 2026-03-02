"use client";

import { Menu } from "lucide-react";

interface HeaderProps {
  onMenuClick: () => void;
}

export default function Header({ onMenuClick }: HeaderProps) {
  return (
    <header className="flex h-14 items-center border-b border-gray-200 bg-white px-4 lg:hidden">
      <button
        onClick={onMenuClick}
        className="rounded-lg p-2 text-gray-600 hover:bg-gray-100"
        aria-label="打开菜单"
      >
        <Menu size={24} />
      </button>
      <span className="ml-3 text-lg font-bold text-indigo-600">AIXue</span>
    </header>
  );
}
