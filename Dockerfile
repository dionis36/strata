FROM python:3.11-slim AS builder

WORKDIR /app


# Install system deps, PHP, and Composer
RUN apt-get update && apt-get install -y \
    build-essential \
    php-cli \
    php-xml \
    php-mbstring \
    unzip \
    && rm -rf /var/lib/apt/lists/*

# Install Composer
COPY --from=composer:latest /usr/bin/composer /usr/bin/composer

# Copy only requirements first for layer caching
COPY requirements.txt .


# Upgrade pip + install dependencies
RUN pip install --upgrade pip && \
    pip install --user -r requirements.txt

# Install PHP dependencies
COPY infrastructure/php/composer.json infrastructure/php/
RUN cd infrastructure/php && composer install --no-dev --no-interaction --no-progress

# =========================

FROM python:3.11-slim

# Install PHP in the final image
RUN apt-get update && apt-get install -y \
    php-cli \
    php-xml \
    php-mbstring \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app


# Copy installed packages from builder
COPY --from=builder /root/.local /root/.local
COPY --from=builder /usr/bin/composer /usr/bin/composer
COPY --from=builder /app/infrastructure/php/vendor /app/infrastructure/php/vendor

# Add local bin to PATH
ENV PATH=/root/.local/bin:$PATH

# Copy app source
COPY . .

# Create data dir
RUN mkdir -p /data

EXPOSE 8000
EXPOSE 8501

