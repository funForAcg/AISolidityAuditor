# Stage 1: Build frontend
FROM node:20-alpine AS frontend-build
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# Stage 2: Backend + Slither runtime
FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Install static solc AFTER pip: solc-select (pulled in by slither/crytic-compile)
# installs its own /usr/local/bin/solc wrapper, which must be overridden by the
# real binary so solc works without solc-select state.
RUN curl -fsSL https://github.com/ethereum/solidity/releases/download/v0.8.20/solc-static-linux \
    -o /usr/local/bin/solc && chmod +x /usr/local/bin/solc

COPY backend/app ./backend/app
COPY --from=frontend-build /app/frontend/dist ./frontend/dist/

ENV DATA_DIR=/data/jobs
ENV PYTHONPATH=/app/backend
ENV CORS_ORIGINS=*
ENV PYTHONDONTWRITEBYTECODE=1

RUN mkdir -p /data/jobs

EXPOSE 8000

WORKDIR /app/backend
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
