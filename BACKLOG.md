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

## P6 — App Store Publication (NEXT)

### Track 1: Billing Migration (IN PROGRESS)
- [ ] Integrate RevenueCat SDK (`purchases_flutter`) for cross-platform billing
- [ ] Create unified payment service (RevenueCat on mobile, Stripe on web)
- [ ] Server-side receipt validation for both Apple & Google
- [ ] Restore Purchases button on subscription screen
- [ ] Subscription management screen (view plan, cancel, upgrade)
- [ ] Handle all subscription states (active, expired, grace period, billing retry)
- [ ] Update subscription screen UI for RevenueCat paywall
- [ ] Tests for billing service

### Track 2: Compliance & Legal (IN PROGRESS)
- [ ] Sign in with Apple (required since we offer Google OAuth)
- [ ] Account deletion feature (required by both stores)
- [ ] Privacy Policy — draft and host publicly
- [ ] Terms of Service — draft and host publicly
- [ ] iOS Privacy manifest (PrivacyInfo.xcprivacy)
- [ ] iOS Required Reason APIs declarations
- [ ] Google Data Safety section preparation
- [ ] GDPR consent mechanism
- [ ] CCPA "Do Not Sell" option
- [ ] Content rating questionnaires (Apple + IARC for Google)
- [ ] Export compliance declaration

### Track 3: Store Assets & Config (after Track 1 & 2)
- [ ] App icon — 1024x1024 source, generate all sizes
- [ ] Screenshots — all iPhone sizes + Android phone/tablet
- [ ] Feature graphic (Google Play) — 1024x500
- [ ] App name, subtitle, description, keywords
- [ ] App preview video (optional but recommended)
- [ ] Store category selection
- [ ] Demo account for Apple App Review

### Track 4: Store Accounts & Submission (LAST STEP — requires Abed)
- [ ] Apple Developer Program enrollment ($99/year)
- [ ] Google Play Developer account ($25 one-time) + identity verification
- [ ] App Store Connect setup (app record, bundle ID, IAP products)
- [ ] Google Play Console setup (app listing, subscription products)
- [ ] Code signing (Apple certificates + Google upload keystore)
- [ ] TestFlight beta (Apple)
- [ ] Closed testing 20+ testers 14+ days (Google)
- [ ] Production submission

See full checklists: docs/APPLE_STORE_CHECKLIST.md & docs/GOOGLE_PLAY_CHECKLIST.md

## P5 — Product Features v2 ✅ COMPLETE
- [x] US-30: Reading Lists & Collections (custom lists, CRUD, share, reorder)
- [x] US-31: User Reviews & Ratings (write/edit/delete reviews, star ratings, helpful votes)
- [x] US-32: Search Functionality (full-text search books, users, lists with filters & autocomplete)
- [x] US-33: Dark Mode (system-aware theme toggle, persistent preference)
- [x] US-34: Onboarding Flow (welcome screens, genre selection, tutorial, first swipe guidance)
- [x] US-35: Analytics Dashboard (user engagement, swipe stats, popular books, retention metrics)
- [x] US-36: Email Notifications (welcome email, weekly digest, recommendation alerts, transactional)
- [x] US-37: Book Sharing via Deep Links (share books/lists/profiles, OG meta tags, universal links)
