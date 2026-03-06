/**
 * 图片压缩工具：缩放至最长边 1536px + WebP/JPEG 格式转换。
 */

const MAX_DIMENSION = 1536;
const WEBP_QUALITY = 0.85;
const JPEG_QUALITY = 0.80;

/**
 * 检测浏览器是否支持 WebP 导出。
 */
function supportsWebP(): boolean {
  const canvas = document.createElement("canvas");
  canvas.width = 1;
  canvas.height = 1;
  return canvas.toDataURL("image/webp").startsWith("data:image/webp");
}

/**
 * 压缩图片文件：缩放至最长边 1536px，转换为 WebP（不支持则 JPEG）。
 *
 * - 小于 1536px 的图片不放大，仅做格式转换
 * - 压缩为异步操作
 *
 * @param file 原始图片 File 对象
 * @returns 压缩后的 File 对象
 */
export async function compressImage(file: File): Promise<File> {
  const bitmap = await createImageBitmap(file);
  const { width, height } = bitmap;

  // 计算缩放比例（不放大）
  const scale = Math.min(1, MAX_DIMENSION / Math.max(width, height));
  const newWidth = Math.round(width * scale);
  const newHeight = Math.round(height * scale);

  // 绘制到 Canvas
  const canvas = document.createElement("canvas");
  canvas.width = newWidth;
  canvas.height = newHeight;
  const ctx = canvas.getContext("2d")!;
  ctx.drawImage(bitmap, 0, 0, newWidth, newHeight);
  bitmap.close();

  // 选择输出格式
  const useWebP = supportsWebP();
  const mimeType = useWebP ? "image/webp" : "image/jpeg";
  const quality = useWebP ? WEBP_QUALITY : JPEG_QUALITY;
  const ext = useWebP ? ".webp" : ".jpg";

  // 导出 Blob
  const blob = await new Promise<Blob>((resolve, reject) => {
    canvas.toBlob(
      (b) => (b ? resolve(b) : reject(new Error("Canvas toBlob 失败"))),
      mimeType,
      quality
    );
  });

  // 构造新文件名
  const baseName = file.name.replace(/\.[^.]+$/, "");
  return new File([blob], `${baseName}${ext}`, { type: mimeType });
}
