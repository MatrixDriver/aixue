"use client";

import { useState, useRef, useCallback } from "react";
import { ImagePlus, Camera, X } from "lucide-react";
import { cn } from "@/lib/utils";

interface ImageUploadProps {
  onImageSelect: (file: File) => void;
  selectedImage: File | null;
  onClear: () => void;
  disabled?: boolean;
}

export default function ImageUpload({
  onImageSelect,
  selectedImage,
  onClear,
  disabled,
}: ImageUploadProps) {
  const [preview, setPreview] = useState<string | null>(null);
  const [dragOver, setDragOver] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const cameraInputRef = useRef<HTMLInputElement>(null);

  const handleFile = useCallback(
    (file: File) => {
      if (!file.type.startsWith("image/")) return;
      if (file.size > 5 * 1024 * 1024) {
        alert("图片大小不能超过 5MB");
        return;
      }
      onImageSelect(file);
      const reader = new FileReader();
      reader.onloadend = () => setPreview(reader.result as string);
      reader.readAsDataURL(file);
    },
    [onImageSelect]
  );

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setDragOver(false);
      if (disabled) return;
      const file = e.dataTransfer.files[0];
      if (file) handleFile(file);
    },
    [disabled, handleFile]
  );

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    if (!disabled) setDragOver(true);
  };

  const handleClear = () => {
    setPreview(null);
    onClear();
    if (fileInputRef.current) fileInputRef.current.value = "";
    if (cameraInputRef.current) cameraInputRef.current.value = "";
  };

  // 已选择图片：显示预览
  if (selectedImage && preview) {
    return (
      <div className="relative inline-block">
        <img
          src={preview}
          alt="题目预览"
          className="h-20 w-20 rounded-lg border border-gray-200 object-cover"
        />
        <button
          type="button"
          onClick={handleClear}
          className="absolute -right-2 -top-2 rounded-full bg-red-500 p-0.5 text-white shadow-sm hover:bg-red-600"
        >
          <X size={14} />
        </button>
      </div>
    );
  }

  // 未选择：显示上传区域
  return (
    <div className="flex items-center gap-2">
      {/* 拖拽区域 */}
      <div
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onDragLeave={() => setDragOver(false)}
        onClick={() => fileInputRef.current?.click()}
        className={cn(
          "flex cursor-pointer items-center gap-1.5 rounded-lg border-2 border-dashed px-3 py-2 text-sm transition-colors",
          dragOver
            ? "border-indigo-400 bg-indigo-50 text-indigo-600"
            : "border-gray-300 text-gray-500 hover:border-indigo-300 hover:text-indigo-500",
          disabled && "cursor-not-allowed opacity-50"
        )}
      >
        <ImagePlus size={18} />
        <span className="hidden sm:inline">上传图片</span>
      </div>

      {/* 拍照按钮（移动端） */}
      <button
        type="button"
        onClick={() => cameraInputRef.current?.click()}
        disabled={disabled}
        className="flex items-center gap-1.5 rounded-lg border-2 border-dashed border-gray-300 px-3 py-2 text-sm text-gray-500 transition-colors hover:border-indigo-300 hover:text-indigo-500 disabled:cursor-not-allowed disabled:opacity-50 sm:hidden"
      >
        <Camera size={18} />
      </button>

      {/* 隐藏的文件选择器 */}
      <input
        ref={fileInputRef}
        type="file"
        accept="image/*"
        className="hidden"
        onChange={(e) => {
          const file = e.target.files?.[0];
          if (file) handleFile(file);
        }}
        disabled={disabled}
      />

      {/* 隐藏的拍照选择器 */}
      <input
        ref={cameraInputRef}
        type="file"
        accept="image/*"
        capture="environment"
        className="hidden"
        onChange={(e) => {
          const file = e.target.files?.[0];
          if (file) handleFile(file);
        }}
        disabled={disabled}
      />
    </div>
  );
}
