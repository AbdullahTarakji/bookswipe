# BookSwipe Demo Script

Step-by-step walkthrough of key BookSwipe features for a live demo or self-guided exploration.

## Setup

```bash
# Start the stack
docker compose up --build -d

# Wait for services to be healthy (~30s)
docker compose ps

# Seed demo data
docker compose exec backend python -m scripts.seed_demo
```

**URLs:**
- Frontend: http://localhost:8080
- API Docs: http://localhost:8000/docs
- Health: http://localhost:8000/health

**Demo Accounts:**

| Email | Password | Role |
|-------|----------|------|
| `admin@bookswipe.app` | `Admin123!` | Admin |
| `reader1@bookswipe.app` | `Reader123!` | User (fiction/fantasy fan) |
| `reader2@bookswipe.app` | `Reader123!` | User (sci-fi/thriller fan) |

---

## Flow 1: User Registration and Login

### Via API (Swagger UI)

1. Open http://localhost:8000/docs
2. **Register** -- POST `/api/auth/register`
   ```json
   {
     "email": "demo@example.com",
     "password": "DemoPass123!"
   }
   ```
3. Copy the `access_token` from the response
4. Click "Authorize" in Swagger UI, paste the token
5. **Get profile** -- GET `/api/auth/me`

### Via curl

```bash
# Register
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"demo@example.com","password":"DemoPass123!"}'

# Login with demo account
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"reader1@bookswipe.app","password":"Reader123!"}'
```

---

## Flow 2: Book Discovery

### Browse Categories

```bash
# List all 14 categories
curl http://localhost:8000/api/categories | python3 -m json.tool
```

### Discover Books

```bash
# Browse fiction books
curl "http://localhost:8000/api/books/discover?category=fiction&page=1" | python3 -m json.tool

# Browse sci-fi
curl "http://localhost:8000/api/books/discover?category=science+fiction&page=1" | python3 -m json.tool
```

### Get Book Details

```bash
# Get detailed info for a specific book
curl "http://localhost:8000/api/books/wrOQLV6xB-wC" | python3 -m json.tool
```

---

## Flow 3: Swipe — Like and Skip

```bash
# Login first
TOKEN=$(curl -s -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"reader1@bookswipe.app","password":"Reader123!"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

# Like a book (swipe right)
curl -X POST http://localhost:8000/api/books/like \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "google_book_id": "wrOQLV6xB-wC",
    "title": "The Hobbit",
    "authors": "J.R.R. Tolkien",
    "thumbnail": "https://books.google.com/books/content?id=wrOQLV6xB-wC&printsec=frontcover&img=1&zoom=1"
  }'

# Skip a book (swipe left)
curl -X POST http://localhost:8000/api/books/skip \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"google_book_id": "some-book-id"}'

# View liked books
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/books/liked | python3 -m json.tool
```

---

## Flow 4: Personalized Recommendations

reader1 has been seeded with 5 liked books (fiction/fantasy). The recommendation engine uses this history.

```bash
# Get recommendations for reader1
TOKEN=$(curl -s -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"reader1@bookswipe.app","password":"Reader123!"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/recommendations/ | python3 -m json.tool
```

Compare with reader2 (sci-fi/thriller preferences) — recommendations differ based on swipe history.

---

## Flow 5: Health Check and Monitoring

```bash
# Health check — shows DB and Redis status
curl http://localhost:8000/health | python3 -m json.tool
```

Expected response:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "uptime": 42.5,
  "dependencies": {
    "database": "ok",
    "redis": "connected"
  }
}
```

---

## Flow 6: Admin Operations

```bash
# Login as admin
TOKEN=$(curl -s -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@bookswipe.app","password":"Admin123!"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

# List all users (admin only)
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/admin/users | python3 -m json.tool
```

---

## Key Talking Points

1. **One-command setup** -- `docker compose up` starts the entire stack
2. **Clean architecture** -- Router -> Service -> Repository separation
3. **11-table PostgreSQL schema** -- Users, books, swipes, recommendations, notifications
4. **Content-based recommendations** -- Learns from swipe history (genre, author, category scores)
5. **JWT auth with token rotation** -- Access (15 min) + refresh (7 days), Redis blacklist
6. **OAuth ready** -- Google and Apple sign-in with automatic account linking
7. **Rate limiting** -- SlowAPI + Redis (5/min auth, 30/min API)
8. **Multi-stage Docker builds** -- Small production images
9. **CI/CD** -- GitHub Actions with lint, test, coverage, Docker build
10. **Production-grade** -- Gunicorn, health checks, Prometheus, Sentry, daily backups

---

## Cleanup

```bash
docker compose down -v    # Remove containers and volumes
make clean                # Full cleanup including build artifacts
```
