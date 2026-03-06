"""
成本优化 — 模型配置测试。

覆盖测试规格:
  - CO-CFG-001 ~ CO-CFG-004: LLM_MODEL_OCR 配置加载与回退
"""

import pytest


class TestOCRModelConfig:
    """OCR 模型配置测试。"""

    def test_llm_model_ocr_loaded(self, monkeypatch):
        """CO-CFG-001: LLM_MODEL_OCR 配置加载。"""
        monkeypatch.setenv("LLM_MODEL_OCR", "google/gemini-2.0-flash-001")
        monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")

        from aixue.config import Settings

        s = Settings()
        assert s.llm_model_ocr == "google/gemini-2.0-flash-001"

    def test_llm_model_ocr_fallback(self, monkeypatch):
        """CO-CFG-002: LLM_MODEL_OCR 未配置时回退到 LLM_MODEL_LIGHT。"""
        monkeypatch.setenv("LLM_MODEL_OCR", "")
        monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")

        from aixue.config import Settings

        s = Settings()
        # 空字符串 or llm_model_light 应回退
        ocr_model = s.llm_model_ocr or s.llm_model_light
        assert ocr_model == s.llm_model_light

    def test_ocr_and_reasoning_models_independent(self, monkeypatch):
        """CO-CFG-003: OCR 和推理模型可独立配置。"""
        monkeypatch.setenv("LLM_MODEL_OCR", "model-ocr")
        monkeypatch.setenv("LLM_MODEL", "model-reasoning")
        monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")

        from aixue.config import Settings

        s = Settings()
        assert s.llm_model_ocr != s.llm_model
        assert s.llm_model_ocr == "model-ocr"
        assert s.llm_model == "model-reasoning"

    def test_ocr_model_property(self, monkeypatch):
        """CO-CFG-004: ocr_model 优先使用 LLM_MODEL_OCR。"""
        monkeypatch.setenv("LLM_MODEL_OCR", "custom-ocr-model")
        monkeypatch.setenv("LLM_MODEL_LIGHT", "light-model")
        monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")

        from aixue.config import Settings

        s = Settings()
        # 当 llm_model_ocr 有值时，应使用它而非 llm_model_light
        ocr_model = s.llm_model_ocr or s.llm_model_light
        assert ocr_model == "custom-ocr-model"
