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

## P3 — Product Features (NEXT)
- [ ] Admin Panel (user mgmt, analytics, moderation, role-based access)
- [ ] Stripe subscription/payments
- [ ] UI polish & animations
- [ ] Staging + production deployment
- [ ] Push notifications
- [ ] Book recommendations (ML-based)
- [ ] Social features (share books, friend lists)
- [ ] CDN for book cover images
- [ ] Load testing (k6/locust)
