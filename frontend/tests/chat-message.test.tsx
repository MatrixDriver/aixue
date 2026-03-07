import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import ChatMessage from "@/components/chat/chat-message";

// mock 子组件以隔离测试
vi.mock("@/components/chat/ocr-expand-panel", () => ({
  default: ({ ocrText, loading }: { ocrText?: string; loading?: boolean }) => (
    <div data-testid="ocr-expand-panel" data-ocr-text={ocrText} data-loading={loading}>
      OCR Panel Mock
    </div>
  ),
}));

vi.mock("@/components/chat/image-lightbox", () => ({
  default: ({ src, onClose }: { src: string; onClose: () => void }) => (
    <div data-testid="image-lightbox" data-src={src}>
      <button onClick={onClose}>关闭</button>
    </div>
  ),
}));

describe("ChatMessage", () => {
  // CM-002: 纯文本用户消息不受影响
  it("纯文本消息应正常渲染文字内容", () => {
    render(
      <ChatMessage
        role="user"
        content="这是一道数学题"
        timestamp="2026-03-07T10:00:00Z"
      />
    );

    expect(screen.getByText("我")).toBeInTheDocument(); // 用户头像
    // 内容通过 dangerouslySetInnerHTML 渲染，检查容器
    const container = document.querySelector(".prose");
    expect(container?.innerHTML).toContain("这是一道数学题");
  });

  // CM-003: AI 回复消息不显示图片组件
  it("AI 消息不应显示 OCR 展开面板", () => {
    render(
      <ChatMessage
        role="assistant"
        content="这道题的解法是..."
      />
    );

    expect(screen.getByText("AI")).toBeInTheDocument(); // AI 头像
    expect(screen.queryByTestId("ocr-expand-panel")).not.toBeInTheDocument();
  });

  // CM-001: 含图片的用户消息使用缩略图渲染
  it("有 localImageUrl 的用户消息应显示缩略图", () => {
    render(
      <ChatMessage
        role="user"
        content="[图片]"
        localImageUrl="blob:http://localhost:3000/test-image"
      />
    );

    const img = screen.getByAltText("上传的题目");
    expect(img).toBeInTheDocument();
    expect(img).toHaveAttribute("src", "blob:http://localhost:3000/test-image");
  });

  // 含图片消息应显示 OCR 展开面板（仅用户消息）
  it("用户图片消息应显示 OCR 展开面板", () => {
    render(
      <ChatMessage
        role="user"
        content="[图片]"
        localImageUrl="blob:http://localhost:3000/test"
        ocrText="识别出的文本"
      />
    );

    expect(screen.getByTestId("ocr-expand-panel")).toBeInTheDocument();
  });

  // 有 localImageUrl 且 content="[图片]" 时不显示文字气泡
  it('content 为"[图片]"且有图片时不应显示"[图片]"文字', () => {
    render(
      <ChatMessage
        role="user"
        content="[图片]"
        localImageUrl="blob:http://localhost:3000/test"
      />
    );

    // 不应在页面中找到 "[图片]" 文字
    const proseElements = document.querySelectorAll(".prose");
    const hasImageText = Array.from(proseElements).some(
      (el) => el.innerHTML.includes("[图片]")
    );
    expect(hasImageText).toBe(false);
  });

  // 缩略图点击应打开 Lightbox
  it("点击缩略图应打开 Lightbox", () => {
    render(
      <ChatMessage
        role="user"
        content="[图片]"
        localImageUrl="blob:http://localhost:3000/test"
      />
    );

    const img = screen.getByAltText("上传的题目");
    fireEvent.click(img);

    expect(screen.getByTestId("image-lightbox")).toBeInTheDocument();
  });

  // 降级到 imagePath
  it("无 localImageUrl 时应降级使用 imagePath", () => {
    render(
      <ChatMessage
        role="user"
        content="[图片]"
        imagePath="/uploads/test.jpg"
      />
    );

    const img = screen.getByAltText("上传的题目");
    expect(img).toHaveAttribute("src", "/uploads/test.jpg");
  });

  // 时间戳渲染
  it("应正确显示时间戳", () => {
    render(
      <ChatMessage
        role="user"
        content="测试"
        timestamp="2026-03-07T10:30:00Z"
      />
    );

    // 时间戳会以本地格式渲染（具体格式取决于 locale）
    const timeEl = document.querySelector(".text-xs.text-gray-400");
    expect(timeEl).toBeInTheDocument();
  });
});
