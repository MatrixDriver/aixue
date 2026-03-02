"""应用配置管理，使用 Pydantic Settings 从环境变量/文件加载。"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """全局配置项，优先从 .env 文件加载，可被环境变量覆盖。"""

    # 数据库
    database_url: str = "postgresql+asyncpg://localhost/aixue"

    # LLM
    anthropic_api_key: str = ""
    anthropic_base_url: str | None = None  # 自定义 API 端点(OpenRouter 等)
    openai_api_key: str = ""
    llm_model: str = "claude-sonnet-4-6-20250514"
    llm_model_light: str = "claude-haiku-4-5-20251001"

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

    model_config = {"env_file": ".env"}
