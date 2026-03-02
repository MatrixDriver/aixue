FROM python:3.12-slim

WORKDIR /app

# 安装 uv
RUN pip install --no-cache-dir uv

# 复制项目配置并安装依赖
COPY pyproject.toml .
RUN uv sync --no-dev --no-install-project

# 复制源代码
COPY src/ src/
COPY alembic.ini .

# 安装项目本身
RUN uv sync --no-dev

# 创建上传目录
RUN mkdir -p /app/uploads

EXPOSE 8000

CMD ["uv", "run", "uvicorn", "aixue.main:app", "--host", "0.0.0.0", "--port", "8000"]
