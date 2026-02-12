# BookSwipe Backlog (Prioritized)

## P0 — In Progress
- [x] Core backend (FastAPI + auth + books + categories) ✅
- [x] Core frontend (Flutter + all screens) ✅
- [x] Frontend ↔ Backend integration ✅
- [x] CI/CD pipelines ✅
- [ ] Security hardening (rate limiting, headers, JWT, passwords) — BUILDING NOW

## P1 — Critical (Next Sprint)
- [ ] Clean Architecture refactor
  - Backend: routers → services → repositories → models (repository pattern, DI)
  - Frontend: clean separation, no API calls in widgets
- [ ] Encryption at rest (emails, tokens — Fernet + hashed lookups)
- [ ] OAuth Social Login (Google + Apple + email/password)
- [ ] Comprehensive error handling
  - Backend: global exception handler, custom error classes, structured error responses
  - Frontend: graceful error states, retry logic, offline handling, user-friendly messages
  - API error codes: standardized error schema across all endpoints
- [ ] Documentation
  - OpenAPI/Swagger (auto from FastAPI)
  - Architecture Decision Records (docs/decisions/)
  - README with setup, architecture, tech stack
  - Docstrings on all public functions
  - CONTRIBUTING.md + API usage examples

## P2 — Scale for 300K Users
- [ ] Load balancer ready
  - Stateless backend (already done ✅)
  - Redis for session/cache (replace in-memory TTL cache)
  - Redis for rate limiting (distributed)
  - Database connection pooling (async SQLAlchemy)
  - Horizontal scaling config (Kubernetes manifests or docker-compose scale)
- [ ] PostgreSQL migration (SQLite → PostgreSQL)
- [ ] Database optimization
  - Indexes on all query columns
  - Query optimization + N+1 prevention
  - Read replicas config
  - Connection pooling (pgbouncer)
- [ ] CDN for book cover images (cache proxy)
- [ ] API response caching (Redis)
- [ ] Background job queue (Celery/ARQ) for heavy operations
- [ ] Monitoring & observability
  - Prometheus metrics
  - Grafana dashboards
  - Sentry error tracking
  - Structured JSON logging
  - Health check endpoints with dependency status

## P3 — Product Features
- [ ] Admin Panel
  - User management (view, ban/suspend, delete)
  - Analytics dashboard (active users, swipes/day, popular categories)
  - Content moderation
  - System monitoring
  - Role-based access (admin vs user)
- [ ] Stripe subscription/payments
- [ ] UI polish & animations
- [ ] Staging + production deployment
- [ ] Biometric auth (fingerprint/face ID)

## Standards (enforced on ALL work)
- Clean Architecture: strict layer separation
- Every public function has docstrings
- Every feature has tests
- No secrets in code
- Structured error responses everywhere
- Design for 300K concurrent users from the start
