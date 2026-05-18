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

# Stage 2: Download GeoLite2 City via wget (License Key only)

FROM python:3.12-slim AS geoip

ARG MAXMIND_LICENSE_KEY

RUN apt-get update \
    && apt-get install -y --no-install-recommends wget tar \
    && mkdir -p /app/geoip \
    && wget -q "https://download.maxmind.com/app/geoip_download?edition_id=GeoLite2-City&license_key=${MAXMIND_LICENSE_KEY}&suffix=tar.gz" \
    -O /tmp/GeoLite2-City.tar.gz \
    && tar -xzf /tmp/GeoLite2-City.tar.gz -C /tmp \
    && mv /tmp/GeoLite2-City_*/GeoLite2-City.mmdb /app/geoip/ \
    && rm -rf /tmp/GeoLite2-City* \
    && apt-get purge -y wget tar && apt-get autoremove -y
# Stage 3: Final application image

FROM python:3.12-slim

WORKDIR /app

# Copy Python packages from builder
COPY --from=builder /install /usr/local

# Copy backend code
COPY backend/ ./

# copy from geoip stage
COPY --from=geoip /app/geoip/GeoLite2-City.mmdb /app/geoip/

# Set up non‑root user and fix ownership
RUN adduser --disabled-password --gecos '' appuser \
    && chown -R appuser:appuser /app

# Switch to non‑root user
USER appuser

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

EXPOSE 8000

CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "2", "--log-level", "info"]