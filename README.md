# Metrika

A Django analytics backend built for tracking website events, aggregating visitor data, and exposing RESTful reporting endpoints.
Live docs [here](https://metrika-api.up.railway.app/api/docs/)

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
- `email_service/` — email sending via smtp with brevo free tier (gmail smtp auto marks as spam), retry handling, and verification workflows
- `common/` — shared middleware, response format, validators, and utilities

## Architecture Diagram

![Metrika Architecture](backend/docs/architecture.png)

- Read [Decisons](DECISIONS.md) for full breakdown of architectural choices and decisions

## Environment variables

Create a `.env` file from `.env.example` or set these values in your shell:

- `DJANGO_SECRET_KEY` — Django secret key
- `REDIS_URL` — Redis connection URL (used for cache and task queues)
- `FRONTEND_BASE_URL` — allowed frontend URL for CSRF/CORS
- `BREVO_API_KEY` — API provider for transactional email sending
- `MAXMIND_LICENSE_KEY` — For GeoCityLite-2 download during docker build
- `MAXMIND_ACCOUNT_ID` — Also for GeoCityLite-2 download
- `CSRF_TRUSTED_ORIGINS` — For CSRF protection
- `DEFAULT_FROM_EMAIL` — Email address that displays to receivers
- `AGGREGATION_SECRET` — Secret key for daily aggregation

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
- `GET /metrics/dashboard` — Human readable prometheus metrics

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
