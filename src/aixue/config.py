"""应用配置管理，使用 Pydantic Settings 从环境变量/文件加载。"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """全局配置项，优先从 .env 文件加载，可被环境变量覆盖。"""

    # 数据库
    database_url: str = "postgresql+asyncpg://localhost/aixue"

    # LLM (OpenRouter)
    openrouter_api_key: str = ""
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    google_api_key: str = ""
    openai_api_key: str = ""
    llm_model: str = "google/gemini-3.1-pro-preview"
    llm_model_light: str = "google/gemini-2.5-flash"
    llm_model_ocr: str = ""  # OCR 模型，为空时回退到 llm_model_light

    # 认证
    secret_key: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 1440  # 24 小时

    # 验证
    max_retry_count: int = 3
    sympy_timeout: int = 10

    # 文件上传
    upload_dir: str = "/app/uploads"
    max_image_size: int = 5 * 1024 * 1024  # 5MB

    model_config = {"env_file": ".env", "extra": "ignore"}
