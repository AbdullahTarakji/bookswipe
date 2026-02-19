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

## P5.5 — Tablet & Large Screen Support ✅ MOSTLY COMPLETE

### US-46: Responsive Framework Integration ✅
- [x] Add `responsive_framework` package to pubspec.yaml
- [x] Configure breakpoints in MaterialApp (mobile <600, tablet 600-1200, desktop >1200)
- [x] Set up responsive wrapper with max content width constraints

### US-47: Adaptive Navigation ✅
- [x] Replace BottomNavigationBar with adaptive navigation (bottom tabs on mobile, NavigationRail on tablet)
- [x] Ensure navigation state persists across layout changes
- [x] Test orientation changes (portrait ↔ landscape)

### US-48: Core Screens Tablet Adaptation ✅
- [x] Swipe card stack — constrain max width, center on tablet
- [x] Book detail screen — two-column layout on tablet (info left, reviews right)
- [x] Liked books grid — increase columns on wider screens (2→3→4)
- [x] Search screen — wider search bar, grid results on tablet
- [x] Profile/settings — constrained width, centered layout

### US-49: Secondary Screens Tablet Adaptation ✅
- [x] Onboarding flow — constrained width, centered content
- [x] Reading lists — grid layout on tablet
- [x] Analytics dashboard — side-by-side charts on tablet
- [x] Subscription/payment screens — constrained width
- [x] Legal pages (privacy, terms) — readable line width

### US-50: Landscape & Foldable Support ✅
- [x] Enable and handle landscape orientation on all screens
- [x] Android foldable support (resizeableActivity + multi-window)
- [x] Landscape card height constraints to prevent overflow

### US-51: Tablet Testing & QA
- [ ] Test on iPad simulator (multiple sizes: iPad Mini, iPad Air, iPad Pro)
- [ ] Test on Android tablet emulator (10", 12")
- [ ] Test on Chromebook if possible
- [ ] Test landscape on all device types
- [ ] Screenshot validation for store listings (tablet sizes)

## P6 — App Store Publication (NEXT)

### Track 1: Billing Migration ✅ COMPLETE
- [x] Integrate RevenueCat SDK (`purchases_flutter`) for cross-platform billing
- [x] Create unified payment service (RevenueCat on mobile, Stripe on web)
- [x] Server-side receipt validation (RevenueCat webhooks)
- [x] Restore Purchases button on subscription screen
- [x] Subscription management screen (view plan, cancel, upgrade)
- [x] Handle all subscription states (active, expired, grace period, billing retry)
- [x] Update subscription screen UI for RevenueCat paywall
- [x] Tests for billing service (20 tests)

### Track 2: Compliance & Legal ✅ COMPLETE
- [x] Sign in with Apple (config + backend ready)
- [x] Account deletion feature (soft delete + PII anonymization)
- [x] Privacy Policy — drafted and served via /legal/privacy-policy
- [x] Terms of Service — drafted and served via /legal/terms
- [x] iOS Privacy manifest (PrivacyInfo.xcprivacy)
- [x] iOS Required Reason APIs declarations
- [x] GDPR consent mechanism (consent screen + API)
- [x] Data export (GET /api/auth/export-data)
- [ ] Google Data Safety section preparation (needs Play Console)
- [ ] Content rating questionnaires (needs store accounts)
- [ ] Export compliance declaration (needs store accounts)

### Track 3: Store Assets & Config ✅ COMPLETE
- [x] App icon — SVG source + flutter_launcher_icons config
- [x] Screenshot guide — 8 screenshots, all device sizes, captions
- [x] Feature graphic concept (Google Play) — 1024x500
- [x] Store listings — ASO-optimized for both Apple & Google (docs/STORE_LISTING.md)
- [x] App preview video script — 20-sec scene-by-scene breakdown
- [x] Store setup checklists (docs/STORE_CONFIG.md)
- [ ] Demo account for Apple App Review (create at submission time)

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
