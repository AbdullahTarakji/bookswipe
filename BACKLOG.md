# BookSwipe Backlog (Prioritized)

## P0 — Core ✅ COMPLETE
- [x] Core backend (FastAPI + auth + books + categories)
- [x] Core frontend (Flutter + all screens)
- [x] Frontend ↔ Backend integration
- [x] CI/CD pipelines (GitHub Actions)

## P1 — Security & Architecture ✅ COMPLETE
- [x] Security hardening (rate limiting, headers, JWT, passwords)
- [x] OAuth Social Login (Google + Apple + email/password)
- [x] Clean Architecture refactor (repository pattern, DI, docstrings)
- [x] Error handling + Documentation

## P2 — Scale for 300K Users ✅ COMPLETE
- [x] PostgreSQL migration + connection pooling + indexes + GDPR soft delete — PR #30
- [x] Monitoring (Prometheus, structured logging, Sentry, K8s, HPA) — PR #31
- [x] Redis caching (distributed cache, rate limiting, token blacklist) — PR #32

## P3 — Product Features ✅ COMPLETE
- [x] Admin Panel (user mgmt, analytics, moderation, role-based access)
- [x] Stripe subscription/payments (checkout, webhooks, billing portal, swipe limits, tests)
- [x] UI polish & animations
- [x] Push notifications
- [x] Book recommendations (ML-based)
- [x] Social features (share books, friend lists)
- [x] CDN for book cover images
- [x] Load testing (k6/locust)
- [x] E2E Testing

## P4 — Deployment ✅ COMPLETE
- [x] Staging deployment (docker-compose.staging.yml, deploy script, CI/CD, nginx SPA)
- [x] Production deployment (deploy script, rollback, SSL/TLS, migrations, backup, CI/CD)
- [x] Deployment documentation (docs/DEPLOYMENT.md)

## P5 — Product Features v2 ✅ COMPLETE
- [x] US-30: Reading Lists & Collections (custom lists, CRUD, share, reorder)
- [x] US-31: User Reviews & Ratings (write/edit/delete reviews, star ratings, helpful votes)
- [x] US-32: Search Functionality (full-text search books, users, lists with filters & autocomplete)
- [x] US-33: Dark Mode (system-aware theme toggle, persistent preference)
- [x] US-34: Onboarding Flow (welcome screens, genre selection, tutorial, first swipe guidance)
- [x] US-35: Analytics Dashboard (user engagement, swipe stats, popular books, retention metrics)
- [x] US-36: Email Notifications (welcome email, weekly digest, recommendation alerts, transactional)
- [x] US-37: Book Sharing via Deep Links (share books/lists/profiles, OG meta tags, universal links)
