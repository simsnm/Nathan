# Multi-stage build for smaller image
FROM python:3.11-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY web_app/requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# Production stage
FROM python:3.11-slim

WORKDIR /app

# Copy Python dependencies from builder
COPY --from=builder /root/.local /root/.local

# Make sure scripts in .local are usable
ENV PATH=/root/.local/bin:$PATH

# Copy application code
COPY codechat.py workflow.py ./
COPY web_app/ ./web_app/
COPY web_frontend/ ./web_frontend/

# Create data directory for SQLite
RUN mkdir -p /app/data

# Environment variables (will be overridden by docker-compose/deployment)
ENV DATABASE_PATH=/app/data/sessions.db
ENV JWT_SECRET_KEY=change-in-production
ENV CORS_ORIGINS='["http://localhost:3000"]'

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD python -c "import requests; requests.get('http://localhost:8000/')" || exit 1

# Run the application
CMD ["python", "web_app/main.py"]