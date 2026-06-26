FROM python:3.12-slim

WORKDIR /app

# Install system dependencies for psycopg2 and uv
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libpq-dev && \
    rm -rf /var/lib/apt/lists/*

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install uv and project dependencies
RUN pip install --no-cache-dir uv && \
    uv sync --frozen --no-dev

# Copy application code
COPY app/ app/

# Expose port
EXPOSE 8000

# Run with uvicorn (4 workers for concurrency)
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]