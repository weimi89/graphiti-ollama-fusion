FROM python:3.11-slim AS base

# 安裝 uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

# 先複製依賴檔案，利用 Docker 層快取
COPY pyproject.toml uv.lock ./
RUN uv sync --no-dev --frozen

# 複製應用程式碼
COPY graphiti_mcp_server.py ./
COPY src/ ./src/
COPY web/ ./web/
COPY .env.example ./.env.example

# 建立日誌目錄
RUN mkdir -p logs

EXPOSE 8000

# 預設啟動 HTTP 模式
CMD ["uv", "run", "python", "graphiti_mcp_server.py", "--transport", "http", "--host", "0.0.0.0", "--port", "8000"]
