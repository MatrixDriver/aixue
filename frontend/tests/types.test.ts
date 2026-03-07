import { describe, it, expect } from "vitest";
import type { Message } from "@/lib/types";

describe("Message 类型扩展", () => {
  // TS-001 + TS-002: Message 接口新增 localImageUrl 和 ocrText 字段
  it("Message 应支持 localImageUrl 和 ocrText 可选字段", () => {
    const msgWithImage: Message = {
      id: "test-1",
      session_id: "session-1",
      role: "user",
      content: "[图片]",
      created_at: "2026-03-07T10:00:00Z",
      localImageUrl: "blob:http://localhost:3000/test",
      ocrText: "识别文本",
    };

    expect(msgWithImage.localImageUrl).toBe("blob:http://localhost:3000/test");
    expect(msgWithImage.ocrText).toBe("识别文本");
  });

  // TS-003: 向后兼容
  it("不含 localImageUrl/ocrText 的 Message 仍应正常使用", () => {
    const msg: Message = {
      id: "test-2",
      session_id: "session-1",
      role: "assistant",
      content: "解题结果",
      created_at: "2026-03-07T10:00:00Z",
    };

    expect(msg.localImageUrl).toBeUndefined();
    expect(msg.ocrText).toBeUndefined();
  });
});
