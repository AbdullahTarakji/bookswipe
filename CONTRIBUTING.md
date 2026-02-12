# Contributing to BookSwipe

Thank you for your interest in contributing to BookSwipe! This guide will help you get started.

## Development Setup

### Prerequisites

- Python 3.11+
- Flutter 3.x (with Dart SDK)
- Git

### Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
```

### Frontend

```bash
cd frontend
flutter pub get
```

## Running Tests

### Backend

```bash
cd backend
source .venv/bin/activate
pytest tests/ -v
```

### Frontend

```bash
cd frontend
flutter test
flutter analyze   # Must pass with 0 issues
```

## Code Style

### Backend (Python)

- Follow PEP 8 conventions
- Add docstrings to all public functions, classes, and modules
- Use type hints for function signatures
- Use custom exceptions from `app/exceptions.py` instead of bare `HTTPException`
- Place database queries in repository classes, not in routers

### Frontend (Dart)

- Follow the [Effective Dart](https://dart.dev/effective-dart) style guide
- Add `///` doc comments to public classes and methods
- Use Riverpod `AsyncValue` for all async state
- Keep widgets small and focused

## Architecture Guidelines

- **Routers** handle only HTTP concerns (request parsing, response formatting, status codes)
- **Services** contain business logic and call repositories or external APIs
- **Repositories** encapsulate all database queries (one per aggregate root)
- **Schemas** validate input at the API boundary

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for the full architecture overview.

## Pull Request Process

1. Create a feature branch from `main`
2. Make your changes with clear, focused commits
3. Ensure all tests pass (`pytest`, `flutter test`, `flutter analyze`)
4. Update documentation if you change API endpoints or architecture
5. Open a pull request with a clear description of the changes

## Reporting Issues

Use [GitHub Issues](../../issues) to report bugs or request features. Please include:

- Steps to reproduce (for bugs)
- Expected vs actual behavior
- Environment details (OS, Python/Flutter version)
