# Load Testing — BookSwipe API

Load tests for the BookSwipe backend using [k6](https://grafana.com/docs/k6/latest/) by Grafana Labs.

## Prerequisites

### Install k6

**macOS:**
```bash
brew install k6
```

**Linux (Debian/Ubuntu):**
```bash
sudo gpg -k
sudo gpg --no-default-keyring --keyring /usr/share/keyrings/k6-archive-keyring.gpg \
  --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys C5AD17C747E3415A3642D57D77C6C491D6AC1D69
echo "deb [signed-by=/usr/share/keyrings/k6-archive-keyring.gpg] https://dl.k6.io/deb stable main" \
  | sudo tee /etc/apt/sources.list.d/k6.list
sudo apt-get update && sudo apt-get install k6
```

**Docker (no install needed):**
```bash
docker run --rm -i --network host grafana/k6 run - <backend/tests/load/smoke.js
```

**Verify installation:**
```bash
k6 version
```

## Quick Start

```bash
# Start the backend
make dev

# Run smoke test (sanity check)
make load-smoke

# Run average load test
make load-average

# Run stress test
make load-stress

# Run spike test
make load-spike
```

To target a deployed environment:
```bash
k6 run -e BASE_URL=https://api.bookswipe.app backend/tests/load/smoke.js
```

## Test Scenarios

| Scenario  | VUs       | Duration | Purpose                          |
|-----------|-----------|----------|----------------------------------|
| `smoke`   | 5         | 30s      | Sanity check — are endpoints up? |
| `average` | 20→100→0  | 5min     | Normal production traffic        |
| `stress`  | 500→2000  | 10min    | Find breaking points             |
| `spike`   | 50→5000   | ~2min    | Viral moment / launch surge      |

## Test Flows

Each scenario exercises a mix of these user journeys:

1. **Auth** — Register a new user → login → receive JWT token
2. **Discovery** — Browse books with category filters and pagination
3. **Swipe** — Like/skip books rapidly (write-heavy)
4. **Recommendations** — Fetch personalized book feed
5. **Social** — Activity feed, profile, followers, book lists

## Thresholds

### Standard (smoke / average)

| Metric                  | Threshold      |
|-------------------------|----------------|
| Error rate              | < 1%           |
| p95 latency (reads)     | < 200ms        |
| p95 latency (writes)    | < 500ms        |
| p95 latency (overall)   | < 500ms        |

### Stress

| Metric                  | Threshold      |
|-------------------------|----------------|
| Error rate              | < 5%           |
| p95 latency (reads)     | < 1000ms       |
| p95 latency (writes)    | < 2000ms       |

### Spike

| Metric                  | Threshold      |
|-------------------------|----------------|
| Error rate              | < 10%          |
| p95 latency (reads)     | < 3000ms       |
| p95 latency (writes)    | < 5000ms       |

## Custom Metrics

Beyond k6 built-ins, these custom metrics are tracked:

| Metric               | Type  | Description                        |
|----------------------|-------|------------------------------------|
| `error_rate`         | Rate  | Application-level error rate       |
| `auth_flow_duration` | Trend | Full register→login flow time      |
| `discover_duration`  | Trend | Book discovery endpoint latency    |
| `swipe_duration`     | Trend | Like/skip write latency            |
| `recommend_duration` | Trend | Recommendations endpoint latency   |
| `social_duration`    | Trend | Social feed + profile latency      |

## Expected Baseline Results

Results on a single `docker compose` instance (1 Uvicorn worker, PostgreSQL, Redis):

| Scenario | Avg Latency | p95 Latency | RPS    | Error Rate |
|----------|-------------|-------------|--------|------------|
| Smoke    | ~50ms       | ~150ms      | ~10    | 0%         |
| Average  | ~80ms       | ~200ms      | ~200   | <0.5%      |
| Stress   | ~200ms      | ~800ms      | ~500   | <3%        |
| Spike    | ~500ms      | ~3000ms     | ~300   | <8%        |

> These baselines are for a single dev instance. Production with Gunicorn (4 workers),
> connection pooling, and Redis caching should perform significantly better.

## Bottleneck Analysis & Tuning

### Common Bottlenecks

**1. Database Connection Pool Exhaustion**

Symptom: Timeouts spike above 500 VUs.

```python
# backend/app/database.py — tune pool for production
engine = create_engine(
    DATABASE_URL,
    pool_size=20,          # default 5 — increase for high concurrency
    max_overflow=30,       # extra connections above pool_size
    pool_timeout=30,       # seconds to wait for a connection
    pool_recycle=1800,     # recycle connections every 30 min
    pool_pre_ping=True,    # verify connections before use
)
```

**2. Redis Connection Limits**

Symptom: Cache misses increase under load, latency degrades.

```yaml
# docker-compose.prod.yml — Redis config
command: redis-server --maxmemory 512mb --maxmemory-policy allkeys-lru --maxclients 10000
```

**3. Missing Database Indexes**

Symptom: Discovery and social feed queries slow down with data growth.

```sql
-- Key indexes for load test flows
CREATE INDEX CONCURRENTLY idx_liked_books_user_id ON liked_books(user_id);
CREATE INDEX CONCURRENTLY idx_skipped_books_user_id ON skipped_books(user_id);
CREATE INDEX CONCURRENTLY idx_swipe_events_user_id ON swipe_events(user_id);
CREATE INDEX CONCURRENTLY idx_activity_user_id_created ON activity(user_id, created_at DESC);
CREATE INDEX CONCURRENTLY idx_follows_follower_id ON follows(follower_id);
CREATE INDEX CONCURRENTLY idx_follows_followed_id ON follows(followed_id);
```

**4. Rate Limiter Under Stress**

The auth endpoints have a 5/min rate limit (slowapi). Under load testing, this will cause 429 responses. Options:

- Disable rate limiting in test environment: `RATE_LIMIT_ENABLED=false`
- Increase limits for load test: `AUTH_RATE_LIMIT=1000/minute`
- Use the `--rps` flag in k6 to cap request rate per-VU

### Production Tuning Recommendations

**Gunicorn Workers:**
```bash
# Rule of thumb: 2 * CPU_CORES + 1
gunicorn app.main:app -w 9 -k uvicorn.workers.UvicornWorker
```

**PostgreSQL (postgresql.conf):**
```ini
max_connections = 200
shared_buffers = 2GB           # 25% of RAM
effective_cache_size = 6GB     # 75% of RAM
work_mem = 16MB
maintenance_work_mem = 512MB
random_page_cost = 1.1         # SSD storage
```

**Redis:**
```ini
maxmemory 1gb
maxmemory-policy allkeys-lru
maxclients 10000
tcp-backlog 511
```

**Connection Pooling (PgBouncer):**

For 300K concurrent users, add PgBouncer between the app and PostgreSQL:
```ini
[pgbouncer]
pool_mode = transaction
max_client_conn = 10000
default_pool_size = 100
reserve_pool_size = 25
```

### Scaling for 300K Concurrent Users

To hit the 300K target:

1. **Horizontal scaling** — Run 8–16 backend instances behind a load balancer
2. **PgBouncer** — Transaction pooling to prevent connection exhaustion
3. **Redis cluster** — Shard cache across 3+ nodes
4. **Read replicas** — Route discovery/recommendation reads to PostgreSQL replicas
5. **CDN** — Cache book cover images and static assets at the edge
6. **Rate limiting** — Use distributed rate limiting (Redis-backed) instead of in-process

## Output Formats

```bash
# JSON output (for CI/dashboards)
k6 run --out json=results.json backend/tests/load/smoke.js

# CSV output
k6 run --out csv=results.csv backend/tests/load/smoke.js

# InfluxDB (for Grafana dashboards)
k6 run --out influxdb=http://localhost:8086/k6 backend/tests/load/smoke.js
```

## File Structure

```
backend/tests/load/
├── config.js    # Shared config: BASE_URL, thresholds, constants
├── helpers.js   # Reusable test flows: auth, discovery, swipe, social
├── smoke.js     # 5 VUs, 30s — sanity check
├── average.js   # 100 VUs, 5min — normal load
├── stress.js    # 500→2000 VUs, 10min — stress test
└── spike.js     # 5000 VUs, 2min — spike test
```
