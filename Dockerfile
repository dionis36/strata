# Use BuildKit to speed up the build
# syntax=docker/dockerfile:1

# 1. Base stage: Runtime dependencies for both stages
FROM python:3.11-slim AS base

WORKDIR /app

# Install PHP and system runtime libs once
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get update && apt-get install -y --no-install-recommends \
    php-cli \
    php-xml \
    php-mbstring \
    unzip \
    git \
    libcairo2 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf-2.0-0 \
    libffi-dev \
    shared-mime-info \
    && rm -rf /var/lib/apt/lists/*

# 2. Builder stage: High-performance dependency installation
FROM base AS builder

# Install 'uv' (Rust-based pip replacement) for 10x faster downloads
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Install Composer for PHP deps
COPY --from=composer:latest /usr/bin/composer /usr/bin/composer

# Create a virtual environment to keep the final image clean
RUN uv venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install Python dependencies using uv cache
COPY requirements.txt .
ENV UV_LINK_MODE=copy
RUN --mount=type=cache,target=/root/.cache/uv \
    uv pip install -r requirements.txt

# Install PHP dependencies
COPY infrastructure/php/composer.json infrastructure/php/
RUN --mount=type=cache,target=/root/.composer/cache \
    cd infrastructure/php && composer install --no-dev --no-interaction --no-progress

# 3. Final stage: Minimal runtime image
FROM base

# Copy the pre-built Python environment
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy the pre-built PHP dependencies
COPY --from=builder /usr/bin/composer /usr/bin/composer
COPY --from=builder /app/infrastructure/php/vendor /app/infrastructure/php/vendor

# Create data directory (cached layer)
RUN mkdir -p /data

# Copy application source code (changes most frequently)
COPY . .

EXPOSE 8000
EXPOSE 8501

# Default command
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
