FROM python:3.11-slim AS builder

WORKDIR /app

# Install system deps only if needed
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy only requirements first for layer caching
COPY requirements.txt .

# Upgrade pip + install dependencies
RUN pip install --upgrade pip && \
    pip install --user -r requirements.txt

# =========================

FROM python:3.11-slim

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /root/.local /root/.local

# Add local bin to PATH
ENV PATH=/root/.local/bin:$PATH

# Copy app source
COPY . .

# Create data dir
RUN mkdir -p /data

EXPOSE 8000
EXPOSE 8501

