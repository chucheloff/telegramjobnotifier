FROM python:3.13-slim

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

WORKDIR /app

# Install uv
RUN pip install --no-cache-dir uv

# Install dependencies first for better layer caching
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

# Copy project files
COPY bot/ ./bot/
COPY services/ ./services/
COPY main.py config.py README.md .

RUN useradd --create-home --shell /usr/sbin/nologin appuser \
    && mkdir -p /app/data \
    && chown -R appuser:appuser /app

# Run the bot (env vars provided at runtime via docker-compose)
USER appuser
CMD ["/app/.venv/bin/python", "main.py"]
