FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

WORKDIR /app

# All environment variables in one layer
ENV UV_COMPILE_BYTECODE=1 \
    UV_NO_PROGRESS=1 \
    PYTHONUNBUFFERED=1 \
    DOCKER_CONTAINER=1 \
    AWS_REGION=us-west-2 \
    AWS_DEFAULT_REGION=us-west-2

ENV PATH="/app/.venv/bin:$PATH"

# Install dependencies
COPY pyproject.toml uv.lock .
RUN uv sync --frozen --no-install-project --no-dev

# Signal that this is running in Docker for host binding logic
ENV DOCKER_CONTAINER=1

# Create non-root user
RUN useradd -m -u 1000 bedrock_agentcore
USER bedrock_agentcore

# AgentCore HTTP endpoint
EXPOSE 9000
EXPOSE 8000
EXPOSE 8080

# Copy application code
COPY . .

# Health check using the /ping endpoint provided by AgentCore SDK
HEALTHCHECK --interval=30s --timeout=3s --start-period=40s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/ping', timeout=3)" || exit 1

CMD ["opentelemetry-instrument", "python", "-m", "src.agent"]
