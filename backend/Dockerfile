# syntax=docker/dockerfile:1.5

# Stage 1: Python dependencies

FROM python:3.12-slim AS builder

WORKDIR /install

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential gcc libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt ./
RUN python -m pip install --upgrade pip \
    && pip install --no-cache-dir --prefix=/install -r requirements.txt

# Stage 2: GeoIP database download (init container)

FROM ghcr.io/maxmind/geoipupdate:latest AS geoip

ARG MAXMIND_ACCOUNT_ID
ARG MAXMIND_LICENSE_KEY

ENV GEOIPUPDATE_ACCOUNT_ID=${MAXMIND_ACCOUNT_ID} \
    GEOIPUPDATE_LICENSE_KEY=${MAXMIND_LICENSE_KEY} \
    GEOIPUPDATE_EDITION_IDS="GeoLite2-City" \
    GEOIPUPDATE_FREQUENCY=0

# Validate credentials are set and download database with error checking
RUN if [ -z "$GEOIPUPDATE_ACCOUNT_ID" ] || [ -z "$GEOIPUPDATE_LICENSE_KEY" ]; then \
    echo "ERROR: MAXMIND_ACCOUNT_ID or MAXMIND_LICENSE_KEY not set"; \
    exit 1; \
    fi && \
    echo "Running geoipupdate with verbose output..." && \
    /usr/bin/geoipupdate -v 2>&1 || echo "geoipupdate exited with code $?" && \
    ls -la /usr/local/share/GeoIP/ 2>/dev/null || echo "GeoIP directory does not exist" && \
    test -f /usr/local/share/GeoIP/GeoLite2-City.mmdb || \
    (echo "ERROR: GeoIP database download failed. Check credentials and ensure GeoLite2-City edition is enabled on your MaxMind account."; exit 1)

# Stage 3: Final application image

FROM python:3.12-slim

WORKDIR /app

# Copy Python packages from builder
COPY --from=builder /install /usr/local

# Copy backend code
COPY backend/ ./

# Create directory for GeoIP database and copy from geoip stage
RUN mkdir -p /app/geoip
COPY --from=geoip /usr/local/share/GeoIP/GeoLite2-City.mmdb /app/geoip/

# Set up non‑root user and fix ownership
RUN adduser --disabled-password --gecos '' appuser \
    && chown -R appuser:appuser /app

# Switch to non‑root user
USER appuser

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

EXPOSE 8000

CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "2", "--log-level", "info"]