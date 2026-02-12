.PHONY: dev prod test lint migrate seed clean help
.DEFAULT_GOAL := help

# ── Development ──────────────────────────────────────────────
dev: ## Start development environment
	docker compose up --build -d
	@echo "Dev environment running: http://localhost:8000/docs"

dev-logs: ## Tail development logs
	docker compose logs -f

dev-down: ## Stop development environment
	docker compose down

# ── Production ───────────────────────────────────────────────
prod: ## Start production environment
	docker compose -f docker-compose.prod.yml up --build -d
	@echo "Production environment running on port $${HTTP_PORT:-80}"

prod-logs: ## Tail production logs
	docker compose -f docker-compose.prod.yml logs -f

prod-down: ## Stop production environment
	docker compose -f docker-compose.prod.yml down

prod-restart: ## Restart production backend (zero-downtime with healthcheck)
	docker compose -f docker-compose.prod.yml up -d --no-deps --build backend

# ── Testing ──────────────────────────────────────────────────
test: ## Run backend tests with coverage
	cd backend && python -m pytest --cov=app tests/ -v

test-ci: ## Run tests in CI mode (strict)
	cd backend && python -m pytest --cov=app --cov-fail-under=70 tests/ -v

# ── Linting ──────────────────────────────────────────────────
lint: ## Run linter
	cd backend && ruff check .

lint-fix: ## Run linter with auto-fix
	cd backend && ruff check --fix . && ruff format .

# ── Database ─────────────────────────────────────────────────
migrate: ## Run database migrations
	cd backend && alembic upgrade head

migrate-new: ## Create a new migration (usage: make migrate-new MSG="add users table")
	cd backend && alembic revision --autogenerate -m "$(MSG)"

seed: ## Seed the database with default data
	cd backend && python -c "from app.database import SessionLocal, engine, Base; from app.models import Category, SEED_CATEGORIES; Base.metadata.create_all(bind=engine); db = SessionLocal(); [db.merge(Category(**c)) for c in SEED_CATEGORIES]; db.commit(); db.close(); print('Seeded.')"

# ── Backups ──────────────────────────────────────────────────
backup: ## Run a manual database backup (production)
	docker compose -f docker-compose.prod.yml exec backup /usr/local/bin/backup.sh

backup-list: ## List available backups
	docker compose -f docker-compose.prod.yml exec backup ls -lh /backups/

# ── Utilities ────────────────────────────────────────────────
clean: ## Remove all containers, volumes, and build artifacts
	docker compose down -v --remove-orphans 2>/dev/null || true
	docker compose -f docker-compose.prod.yml down -v --remove-orphans 2>/dev/null || true
	find backend -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find backend -name "*.pyc" -delete 2>/dev/null || true
	rm -rf backend/.pytest_cache backend/.coverage backend/htmlcov

shell: ## Open a shell in the running backend container
	docker compose exec backend /bin/bash

shell-db: ## Open psql in the running database container
	docker compose exec db psql -U bookswipe

# ── Help ─────────────────────────────────────────────────────
help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'
