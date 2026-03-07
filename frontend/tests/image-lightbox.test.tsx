import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import ImageLightbox from "@/components/chat/image-lightbox";

describe("ImageLightbox", () => {
  const defaultProps = {
    src: "blob:http://localhost:3000/test-image-id",
    alt: "测试图片",
    onClose: vi.fn(),
  };

  beforeEach(() => {
    defaultProps.onClose.mockClear();
  });

  // IL-001: Lightbox 正常显示大图
  it("应渲染遮罩层和图片", () => {
    render(<ImageLightbox {...defaultProps} />);

    const dialog = screen.getByRole("dialog");
    expect(dialog).toBeInTheDocument();
    expect(dialog).toHaveAttribute("aria-modal", "true");

    const img = screen.getByAltText("测试图片");
    expect(img).toBeInTheDocument();
    expect(img).toHaveAttribute("src", defaultProps.src);
  });

  // IL-002: 点击遮罩层关闭 Lightbox
  it("点击遮罩层应调用 onClose", () => {
    render(<ImageLightbox {...defaultProps} />);

    const dialog = screen.getByRole("dialog");
    fireEvent.click(dialog);

    expect(defaultProps.onClose).toHaveBeenCalledTimes(1);
  });

  // IL-003: 点击关闭按钮关闭 Lightbox
  it("点击关闭按钮应调用 onClose", () => {
    render(<ImageLightbox {...defaultProps} />);

    // 关闭按钮包含 X 图标
    const buttons = screen.getAllByRole("button");
    fireEvent.click(buttons[0]);

    expect(defaultProps.onClose).toHaveBeenCalled();
  });

  // IL-004: ESC 键关闭 Lightbox
  it("按 ESC 键应调用 onClose", () => {
    render(<ImageLightbox {...defaultProps} />);

    fireEvent.keyDown(document, { key: "Escape" });

    expect(defaultProps.onClose).toHaveBeenCalledTimes(1);
  });

  // IL-005: 点击图片本身不关闭 Lightbox
  it("点击图片本身不应关闭 Lightbox", () => {
    render(<ImageLightbox {...defaultProps} />);

    const img = screen.getByAltText("测试图片");
    fireEvent.click(img);

    // onClose 不应被调用（图片 stopPropagation）
    expect(defaultProps.onClose).not.toHaveBeenCalled();
  });

  // IL-006: 无障碍属性
  it("应具有正确的无障碍属性", () => {
    render(<ImageLightbox {...defaultProps} />);

    const dialog = screen.getByRole("dialog");
    expect(dialog).toHaveAttribute("role", "dialog");
    expect(dialog).toHaveAttribute("aria-modal", "true");
  });

  // 默认 alt 文本
  it("未传 alt 时应使用默认值", () => {
    render(<ImageLightbox src={defaultProps.src} onClose={defaultProps.onClose} />);

    const img = screen.getByAltText("图片");
    expect(img).toBeInTheDocument();
  });
});
