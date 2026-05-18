# Metrika

A Django analytics backend built for tracking website events, aggregating visitor data, and exposing RESTful reporting endpoints.

## Highlights

- JWT-authenticated user management with email verification, password reset, and session security
- Event ingestion API with site-level tracking token, rate limiting, bot filtering, and geo-enrichment
- Daily aggregation of page views, referrers, countries, devices, browsers, operating systems, regions, and cities
- DRF + OpenAPI docs, Redis caching, background task support, and Prometheus metrics

## Architecture

- `backend/` — Django project root
- `accounts/` — authentication, registration, email verification, token lifecycle
- `sites/` — site management, tracking tokens, timezone and public ID support
- `tracking/` — event ingestion, request context extraction, spam/bot filtering
- `analytics/` — timezone-aware stats aggregation, sessions (bounce rate, views per visit, duration), pagination, and query sanitization
- `email_service/` — email sending, retry handling, and verification workflows
- `common/` — shared middleware, response format, validators, and utilities

graph TD
%% ---- Clients ----
USER[👤 Dashboard User]
VISITOR[🌐 Site Visitor]
BOT[🤖 Bot / Crawler]

    %% ---- Frontend ----
    NEXT[Next.js Frontend<br/>SPA + SSR]
    TRACKER[tracker.js<br/>JavaScript Snippet]

    %% ---- API Gateway & Middleware ----
    NGINX[Nginx / Reverse Proxy] (commercial use only)
    MIDDLEWARE[CORS · CSRF · Rate Limiting · JSON Envelope]

    %% ---- Django Modular Monolith ----
    subgraph DJANGO[Django Modular Monolith]
        ACCOUNTS[accounts<br/>Auth & Identity]
        SITES[sites<br/>Site Management]
        TRACKING_MOD[tracking<br/>Event Ingestion]
        ANALYTICS[analytics<br/>Aggregation & Stats]
        EMAIL_SVC[email_service<br/>Async Emails]
        COMMON[common<br/>Utilities & Cross-cutting]
    end

    %% ---- Data Stores ----
    DB[(Database<br/>SQLite)]
    REDIS[(Redis<br/>Cache · RQ Queue)]
    STATIC[Static Files<br/>tracker.js · Swagger UI]

    %% ---- Background Jobs ----
    WORKER[RQ Worker<br/>Email Sending]
    AGGREGATION_CRON[Cron / RQ Scheduler<br/>Daily Aggregation]

    %% ---- Dashboard Flow ----
    USER -->|Login / View Stats| NEXT
    NEXT -->|REST API| NGINX
    NGINX --> DJANGO

    %% ---- Tracking Flow ----
    VISITOR -->|Loads page| TRACKER
    TRACKER -->|POST /api/event<br/>X-Tracking-Token| NGINX
    BOT -->|Blocked by rate limit & bot filter| TRACKER
    NGINX --> DJANGO

    %% ---- Internal Module Communication ----
    ACCOUNTS -->|Service boundary| SITES
    SITES -->|get_site_by_token()| TRACKING_MOD
    TRACKING_MOD -->|Raw events| ANALYTICS
    ANALYTICS -->|Queries| SITES

    %% ---- Infrastructure Dependencies ----
    ACCOUNTS --> DB
    SITES --> DB
    TRACKING_MOD --> DB
    ANALYTICS --> DB
    EMAIL_SVC --> REDIS
    EMAIL_SVC --> WORKER
    AGGREGATION_CRON --> ANALYTICS

    %% ---- Static & Docs ----
    DJANGO --> STATIC
    NGINX --> STATIC
    NEXT -->|Serves snippet| STATIC

- Nginx is only added for future implementation. For now, the roadmap only involves building the next frontend

## Environment variables

Create a `.env` file from `.env.example` or set these values in your shell:

- `DJANGO_SECRET_KEY` — Django secret key
- `REDIS_URI` — Redis connection URL (used for cache and task queues)
- `FRONTEND_BASE_URL` — allowed frontend URL for CSRF/CORS
- `EMAIL_HOST` — SMTP server host
- `EMAIL_PORT` — SMTP server port
- `EMAIL_USE_TLS` — enable TLS for email delivery
- `EMAIL_HOST_USER` — SMTP username
- `EMAIL_HOST_PASSWORD` — SMTP password

```bash
cp .env.example .env
# edit .env with your values
```

## Quick start

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

## Docker setup

```bash
# build and run locally with Redis
docker compose up --build

# or build image only
docker build -t metrika-backend .
```

The app is then available at `http://localhost:8000` and the Swagger docs at `/api/docs/`.

## Useful endpoints

- `GET /api/docs/` — interactive Swagger UI
- `POST /api/auth/register/` — sign up and trigger email verification
- `POST /api/events/` — ingest tracking payloads with `X-Tracking-Token`
- `GET /api/stats/<site_id>/summary/` — site analytics summary

## Roadmap

- Next.js frontend dashboard for authenticated analytics consumers
- real-time event visualization and custom reporting widgets
- client-side tracking snippet generator and site onboarding flow
- production deployment automation with container orchestration

## Testing

```bash
cd backend
python manage.py test
```
