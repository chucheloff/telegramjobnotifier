FROM python:3.13-slim

WORKDIR /app

# Install uv
RUN pip install --no-cache-dir uv

# Copy project files
COPY pyproject.toml uv.lock ./
COPY bot/ ./bot/
COPY services/ ./services/
COPY server/ ./server/
COPY tests/ ./tests/
COPY main.py config.py README.md .

# Install dependencies
RUN uv sync --frozen

# Run the bot (env vars provided at runtime via docker-compose)
CMD ["uv", "run", "main.py"]
