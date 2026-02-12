# Contributing to BookSwipe

Thank you for your interest in contributing to BookSwipe. This guide covers everything you need to get started, from setting up your development environment to opening a pull request.

---

## Table of Contents

1. [Development Setup](#development-setup)
2. [Coding Standards](#coding-standards)
3. [PR Process](#pr-process)
4. [Testing Guidelines](#testing-guidelines)
5. [Project Structure](#project-structure)

---

## Development Setup

### Backend (Python)

**Requirements:** Python 3.12 or higher.

```bash
cd backend
python -m venv venv
source venv/bin/activate   # On Windows: venv\Scripts\activate
pip install -r requirements.txt
pip install -r requirements-dev.txt
cp .env.example .env
```

Edit `.env` with your local configuration (database URL, secret keys, etc.) before running the server.

Start the backend development server:

```bash
uvicorn app.main:app --reload --port 8000
```

### Frontend (Flutter)

**Requirements:** Flutter 3.10 or higher.

```bash
cd frontend
flutter pub get
```

Start the frontend development server:

```bash
flutter run -d chrome
```

### Docker

To run the full stack with Docker:

```bash
docker compose up
```

This starts both services:

- **Backend** on `http://localhost:8000`
- **Frontend** on `http://localhost:8080`

---

## Coding Standards

### Backend (Python)

- Use **ruff** for both linting and formatting. Run `ruff check .` and `ruff format .` before committing.
- **Type hints** are required on all function signatures (parameters and return types).
- **Docstrings** are required on all public functions and classes. Use Google-style or NumPy-style docstrings consistently.
- Follow PEP 8 conventions (enforced automatically by ruff).

### Frontend (Dart)

- Follow the rules defined in `analysis_options.yaml`, which extends **flutter_lints**.
- Prefer **const constructors** wherever possible to improve widget rebuild performance.
- Use **Riverpod** for state management. Do not introduce other state management solutions without prior discussion.
- Run `flutter analyze` and resolve all warnings before committing.

### General

- All code must pass CI before it can be merged. The CI pipeline runs:
  - `ruff check` and `ruff format --check` for the backend
  - `flutter analyze` for the frontend
  - Full test suites for both backend and frontend

---

## PR Process

1. **Fork the repository** and clone your fork locally.

2. **Create a feature branch** from `main`:
   ```bash
   git checkout main
   git pull origin main
   git checkout -b feature/your-feature-name
   ```

3. **Write tests** for any new features or bug fixes. PRs without adequate test coverage for new code will not be merged.

4. **Keep commits atomic.** Each commit should represent a single logical change. Use **conventional commit messages**:
   - `feat:` -- a new feature
   - `fix:` -- a bug fix
   - `docs:` -- documentation changes only
   - `test:` -- adding or updating tests
   - `refactor:` -- code restructuring without behavior changes
   - `chore:` -- maintenance tasks (dependencies, CI config, etc.)

   Examples:
   ```
   feat: add genre filtering to book recommendations
   fix: resolve token refresh race condition in auth service
   docs: update API endpoint descriptions in README
   ```

5. **Open a pull request** against the `main` branch. In the PR description:
   - Summarize what the PR does and why.
   - Reference any related issues (e.g., `Closes #42`).
   - Note any breaking changes or migration steps.

6. **All CI checks must pass.** Fix any failures before requesting review.

7. **Request a review** from a maintainer. Be responsive to feedback and push follow-up commits as needed.

---

## Testing Guidelines

### Backend

The backend uses **pytest** with **pytest-asyncio** for async test support.

```bash
cd backend
python -m pytest
```

Key practices:

- Use the shared fixtures defined in `tests/conftest.py` for database sessions, test clients, and authentication helpers.
- **Mock external APIs** (book data providers, third-party services) rather than making real network calls in tests.
- Organize tests by module: `test_auth.py`, `test_books.py`, `test_categories.py`, etc.

### Frontend

The frontend uses Flutter's built-in test framework with **mocktail** for mocking.

```bash
cd frontend
flutter test
```

Key practices:

- Place unit and widget tests in the `test/` directory, mirroring the structure under `lib/`.
- Use **mocktail** to mock services, repositories, and providers.
- Test widgets in isolation where possible and verify state transitions via Riverpod providers.

### Coverage

- Aim for meaningful test coverage on all new code. Every new feature or bug fix should include corresponding tests.
- Focus on testing business logic, edge cases, and error handling rather than chasing a coverage percentage.

---

## Project Structure

```
bookswipe/
├── backend/                  # FastAPI backend (Python)
│   ├── app/
│   │   ├── main.py           # Application entry point and FastAPI app
│   │   ├── config.py         # Configuration and environment variables
│   │   ├── database.py       # Database connection and session management
│   │   ├── models.py         # SQLAlchemy ORM models
│   │   ├── schemas.py        # Pydantic request/response schemas
│   │   ├── exceptions.py     # Custom exception classes
│   │   ├── routers/          # API route handlers (auth, books, categories)
│   │   └── services/         # Business logic layer
│   ├── alembic/              # Database migration scripts
│   ├── tests/                # Backend test suite
│   │   ├── conftest.py       # Shared test fixtures
│   │   ├── test_auth.py      # Authentication endpoint tests
│   │   ├── test_books.py     # Books endpoint tests
│   │   └── test_categories.py# Categories endpoint tests
│   ├── requirements.txt      # Production dependencies
│   ├── requirements-dev.txt  # Development/test dependencies
│   └── Dockerfile            # Backend container definition
├── frontend/                 # Flutter frontend (Dart)
│   ├── lib/
│   │   ├── main.dart         # Application entry point
│   │   ├── app.dart          # Root app widget and routing
│   │   ├── models/           # Data models
│   │   ├── providers/        # Riverpod state providers
│   │   ├── screens/          # Full-page screen widgets
│   │   ├── services/         # API clients and external service integrations
│   │   ├── theme/            # App theming and styling
│   │   ├── utils/            # Utility functions and helpers
│   │   └── widgets/          # Reusable UI components
│   ├── test/                 # Frontend test suite
│   ├── pubspec.yaml          # Dart/Flutter dependencies
│   └── Dockerfile            # Frontend container definition
├── docker-compose.yml        # Full-stack orchestration
└── docs/                     # Additional project documentation
```

---

If you have questions or need help getting started, open an issue on the repository and a maintainer will follow up.
