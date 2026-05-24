# Architecture & Design Decisions – Metrika

This document records the significant architectural decisions made during the development of Metrika, a privacy‑friendly web analytics platform. Each section follows the format:

- **Context** – the problem needed to solve.
- **Decision** – what I chose and why.
- **Consequences** – the resulting benefits and trade‑offs.
- **Alternatives Considered** – what else I evaluated.

## 1. Modular Monolith as the Top‑Level Architecture

### Context

I needed to build a backend that was maintainable, testable, and understandable for a single developer while still demonstrating the ability to scale and separate concerns.

### Decision

I chose a **service‑oriented modular monolith**. The codebase is organised into Django “apps” that represent bounded contexts (`accounts`, `sites`, `tracking`, `analytics`, `email_service`). Each context exposes a **public service class** and **never** imports models from another context directly for direct use. Cross‑module communication happens only through these service interfaces.

### Consequences

- Clear boundaries without the operational overhead of microservices.
- Easy to extract a module into a separate service later if needed.
- Developers (and reviewers) can understand the system by reading a single codebase.

### Alternatives Considered

- **Layered (horizontal) architecture** – would have blurred domain boundaries and made the system harder to reason about as it grew.

## 2. JWT Authentication with HttpOnly Refresh Cookies and CSRF

### Context

A secure, stateless authentication scheme for a single‑page application (Next.js) and a public API.

### Decision

**access tokens** (short‑lived, 10 minutes) stored in memory by the frontend, and **refresh tokens** (long‑lived) stored in **HttpOnly, Secure, SameSite cookies**. Login sets the refresh cookie; token refresh reads the cookie and returns a new access token. All state‑changing endpoints are protected by Django’s CSRF middleware; the frontend sends the CSRF token in the `X‑CSRFToken` header.

### Consequences

- Refresh tokens are invisible to JavaScript, mitigating XSS attacks.
- Access token remains ephemeral (10 minutes). If stolen, damage is limited.
- CSRF protection is mandatory (and enabled) to prevent cross‑site attacks.
- Token blacklisting (logout, password reset, password change, email change) revokes compromised refresh tokens.

### Alternatives Considered

- **Session authentication** – easier to implement but jwt was preferred as a personal choice.
- **JWT only (access token in localStorage)** – simpler, but vulnerable to XSS. I explicitly avoided this for the refresh token.

## 3. Asynchronous Email with Redis + RQ

### Context

Sending emails (verification, password reset, suspicious login alerts) must not block the HTTP request cycle.

### Decision

I used **Redis** as a message broker and **django‑rq** to enqueue email sending tasks. A separate RQ worker process dequeues jobs and sends them via Brevo's API (Django's console backend is used in debug mode). Failed jobs are automatically retried with an exponential backoff interval (only on transient errors, not on permanent failures like invalid addresses).

### Consequences

- API responses are fast – email delivery is decoupled.
- Built‑in retry logic prevents lost emails during temporary API outages.
- Workers and the web app share the same codebase, making deployment simple.
- Requires Redis and a running worker process, which adds operational complexity (mitigated by Docker / Railway service definitions).

### Alternatives Considered

- **Celery** – too heavy for this scale; requires a separate message broker and more configuration.
- **Database‑backed queue** – would have worked but adds write load to the primary database and requires a cron job to process.

## 4. Analytics Data Pre‑Aggregation

### Context

Raw pageview events can be numerous. Querying them directly for every dashboard chart would be slow.

### Decision

Events are **pre‑aggregated** into daily summary tables (`DailySiteStats`, `DailyPageStats`, etc.) using a nightly management command (`aggregate_daily`). The dashboard reads from these lightweight tables. Only “today” and “last 24 hours” use live raw event queries. For monthly and yearly views, I further aggregated the daily tables on‑the‑fly with `TruncMonth`/`TruncYear`.

### Consequences

- Dashboard queries are fast (simple `SUM` over a few hundred rows per site per day).
- Storage is minimal – one row per dimension per day.
- The aggregation job must run reliably; a free scheduling service is considered. Railway's cron job cannot be used for web services because it runs once.
- Real‑time data for the current day is served from raw events, keeping the dashboard up‑to‑date.

### Alternatives Considered

- **Query raw events for everything** – simple but would become slow and expensive as data grows.
- **ClickHouse / columnar stores** – excellent for very large datasets, but overkill for a portfolio. This is a future scaling option.

## 5. Timezone‑Aware Aggregation

### Context

Site owners expect their daily statistics to be calculated using their local midnight, not the server’s UTC midnight. A site in Tokyo should have “May 17” cover the Tokyo day, not the UTC day.

### Decision

A `timezone` (IANA name) is stored on each `Site` model and used during aggregation and live “today” queries. The utility `get_local_day_utc_range` maps a local date to a UTC window, which filters raw events. Aggregated rows are stamped with the **local date**, so the dashboard can filter by `date` directly.

### Consequences

- Each site’s data is correctly aligned to its owner’s calendar.
- Historical queries (`?start=2026-05-01&end=2026-05-15`) return data labelled in the site’s local dates.
- Raw events stay in UTC, which is the standard for storage.
- Timezone lookups are cached with `functools.lru_cache` to avoid repeated file I/O.

### Alternatives Considered

- **Always use UTC** – simpler, but produces misleading “today” counts for non‑UTC sites.
- **Store events in the site’s local time** – would complicate comparisons across sites and make migration between timezones error‑prone.

## 6. Sessionization (Bounce Rate, Duration, Views per Visit)

### Context

To offer services akin with platforms like Plausible, I needed session‑based metrics: bounce rate, average visit duration, and views per visit.

### Decision

I implemented a **30‑minute inactivity sessionization** algorithm in Python, using raw events. The algorithm groups events by visitor, sorts them chronologically, and splits sessions when a gap exceeds 30 minutes. The resulting component counts (`total_visits`, `single_page_sessions`, `total_duration_seconds`, `total_pageviews_in_sessions`) are stored in `DailySiteStats` and used to compute the derived percentages at query time.

### Consequences

- Accurate bounce rate and average duration without storing session objects.
- The algorithm runs once per day per site during aggregation; live “today” metrics are computed on‑the‑fly.
- Storing raw component counts (not percentages) allows correct aggregation across arbitrary date ranges.

### Alternatives Considered

- **Database‑level window functions** – more performant for large datasets but less portable (SQLite doesn’t support them, which was the development database before deploy decision on railway).
- **Pre‑computed session tables** – would add complexity and storage for minimal gain at this scale.

## 7. Referrer Parsing & UTM Handling

### Context

I needed to classify incoming traffic into sources (Google, Facebook, etc.) and mediums (organic, social, referral).

### Decision

I built a simple, deterministic `parse_referrer` function that checks the referrer domain against known search engines and social networks. For marketing campaigns, I also checked the landing page URL for UTM parameters (`utm_source`, `utm_medium`) and used them to override the referrer.

### Consequences

- No external API calls or database lookups – extremely fast.
- Easy to extend with new domains or sources.
- UTM support aligns with marketing needs and demonstrates awareness of real‑world analytics requirements.

### Alternatives Considered

- **Third‑party attribution libraries** – heavier than needed; a simple string‑matching approach is sufficient and transparent.

## 8. Bot Filtering & Query Parameter Stripping

### Context

Bots inflate analytics numbers, and query strings split the same page into multiple entries.

### Decision

- **Bot filtering**: During ingestion, I check `user_agents.is_bot` and skip event creation for known bots.
- **Query stripping**: During aggregation, I extracted only the path (`parsed.path`) from the URL, discarding query strings. This way `example.com` and `example.com?q=3` are the under the same entry.

### Consequences

- Cleaner, more accurate reports.
- Minimal overhead – `is_bot` is a simple boolean check; URL parsing is fast.
- No false positives for legitimate users (the `is_bot` list is maintained by the `user-agents` library).

## 9. Rate Limiting Strategy

### Context

Public endpoints (login, registration, tracking) must be protected from abuse. Authenticated dashboard queries should not degrade performance for other users.

### Decision

I used DRF’s built‑in throttling with **per‑endpoint scopes**. This is not a proper defence against brute force or DoS attacks. It's a simple protection layer:

- `login`: 5 requests/minute (mitigates brute force).
- `register`: 3 requests/hour (prevents mass account creation).
- `tracking`: 1000 requests/hour per IP (stops single‑IP abuse without affecting legitimate high‑traffic sites).
- Global authenticated: 1000 requests/hour per user.

### Consequences

- Bruteforce attacks on login are mitigated.
- Abusive scripts hitting the tracking endpoint are contained per IP.
- Legitimate viral traffic is unaffected (because it comes from many distinct IPs).
- The implementation uses Django’s caching framework, so no extra infrastructure is needed.

### Alternatives Considered

- **Per‑token rate limiting** – rejected because a viral site could legitimately exceed any fixed limit, leading to dropped events and poor user experience.

## 10. API Documentation with drf‑spectacular

### Context

I needed interactive, accurate, and always‑up‑to‑date API documentation.

### Decision

I chose **drf‑spectacular** to auto‑generate OpenAPI 3.0 schemas from the DRF views and serializers. I created a custom envelope schema and used `@extend_schema` decorators to document every endpoint with examples. The documentation is served at `/api/docs/` (Swagger UI).

### Consequences

- Documentation is always in sync with the code.
- Frontend developers can explore and test the API without separate tools.
- Requires manual annotation for complex responses (our custom envelope), but that effort is minimal and yields high‑quality docs.

### Alternatives Considered

- **Hand‑written OpenAPI YAML** – would drift out of date; higher maintenance.

## 11. Pagination (Shrunk Preview vs Expanded Drill‑Down)

### Context

Dashboard cards show a compact “Top N” list, while clicking “View all” expands to a full paginated list with “Load more” functionality.

### Decision

I used **DRF’s `LimitOffsetPagination`** with a custom envelope that includes `next`/`previous` links and a `meta` object (`total`, `offset`, `limit`). When the query parameter `offset` is present, the response includes pagination metadata; when absent, only a simple top‑N list is returned (no count query). This gives the frontend two clean modes with a single endpoint.

### Consequences

- The frontend can implement “Load more” by following `meta.next`.
- The shrunk mode avoids unnecessary `COUNT` queries, keeping dashboard cards fast.
- Consistent with REST best practices (HATEOAS‑style navigation).

### Alternatives Considered

- **Separate endpoints** (`/top-pages/preview` vs `/top-pages/full`) – would duplicate logic.
- **Cursor‑based pagination** – better for real‑time feeds, but offset‑based is simpler and sufficient for analytics data. It is considered for scale.

## 12. Deployment & Infrastructure

### Context

The project needed to be deployable to a modern cloud platform for a live demo.

### Decision

**Railway** is used for deployment using a `railway.toml`. Two services are hosted:

1. **web** – Main API. Started with Gunicorn
2. **worker** – RQ worker for async email.

Redis is provided as a Railway plugin. PostgreSQL or SQLite can be used, however SQLite is ephemeral so the live service uses Railway's PostgreSQL service; the settings are environment‑based.

### Consequences

- One Dockerfile – simple and maintainable.
- Railway’s built‑in Redis and database plugins reduce operational burden.

### Alternatives Considered

- **VPS** – free tiers are more restrictive and have higher maintenance.

## 13. Testing Strategy

### Context

I needed to ensure correctness across all modules and make the project trustworthy.

### Decision

**Django’s test framework** with `APIClient` is used for API tests, `freezegun` for time‑dependent tests, and `unittest.mock` for external service isolation. Tests cover:

- Unit tests for services, validators, and utilities.
- Integration tests for all API endpoints (auth, sites, tracking, analytics).
- Edge cases: rate limiting, timezone handling, pagination, bot filtering.

### Consequences

- A comprehensive test suite (over 170 tests) gives confidence to refactor and deploy.
- Fast test execution (SQLite in‑memory for most tests) encourages frequent running.

### Alternatives Considered

- **pytest** with Django plugin – equally good; Django’s built‑in runner offers simplicity.

## 14. Load Testing & Performance Characterisation

### Context

I needed to understand how the API behaves under concurrent load and where the single‑instance deployment reaches its limits.

### Decision

I used **k6** to write and run targeted load tests against the deployed Railway backend. Tests covered:

- **Authentication** (login) – CPU‑bound due to password hashing and JWT signing.
- **Analytics reads** (raw‑event endpoints) – I/O‑bound, querying the `Event` table.

All tests were executed from a cloud VM (Google Cloud Shell) to eliminate local network bias.

### Key Results

- **Login:** sustained **~7 requests/second** with 0% failures. Latency remained under 1.5 s up to 10 concurrent users; at 100 concurrent users, latency increased to ~10 s while throughput remained constant.
- **Analytics reads:** served **79 req/s with avg latency 327 ms** under 50 concurrent users, and **138 req/s with avg latency 1.04 s** under 200 concurrent users – both with **0% errors**.

### Consequences

- The single‑instance Railway server handles moderate traffic well and degrades gracefully under overload (no crashes, no dropped connections).
- The authentication path is CPU‑limited; horizontal scaling would be required for high‑traffic login scenarios.
- The analytics read path is I/O‑bound and scales well until database connections saturate.
