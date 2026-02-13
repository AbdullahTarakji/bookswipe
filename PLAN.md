# BookSwipe — Project Plan

## Vision
A Swipe-style book discovery app. Users swipe through books, like or skip them, filter by category, and view detailed book info. Cross-platform via Flutter.

## Architecture

### Frontend (Flutter)
- Swipe-style swipe cards (flutter_card_swiper or similar)
- Screens: Home/Swipe, Categories, Liked Books, Book Detail
- State management: Riverpod
- HTTP client: Dio
- Responsive for mobile + desktop

### Backend (FastAPI)
- REST API endpoints
- Google Books API integration (search, categories, details)
- User management (liked books, preferences)
- PostgreSQL database via SQLAlchemy
- Pydantic models for validation

### Database Schema
- **users**: id, email, created_at
- **liked_books**: id, user_id, google_book_id, liked_at
- **skipped_books**: id, user_id, google_book_id, skipped_at
- **categories**: id, name, google_category_key

### API Endpoints
- `GET /api/books/discover?category=romance&page=1` — Get swipeable books
- `POST /api/books/like` — Like a book
- `POST /api/books/skip` — Skip a book
- `GET /api/books/liked` — Get user's liked books
- `GET /api/books/{id}` — Get book details
- `GET /api/categories` — List available categories
- `POST /api/auth/register` — Register
- `POST /api/auth/login` — Login

### Google Books API
- Free, no key required for basic use (1000 req/day without key, more with key)
- Endpoint: `https://www.googleapis.com/books/v1/volumes`
- Provides: title, authors, description, pageCount, categories, imageLinks, averageRating, ratingsCount

## User Stories

### Epic 1: Book Discovery (Swipe)
- US-1: As a user, I can see a stack of book cards with cover, title, and author
- US-2: As a user, I can swipe right to like a book
- US-3: As a user, I can swipe left to skip a book
- US-4: As a user, I see the next book automatically after swiping

### Epic 2: Categories
- US-5: As a user, I can view a list of book categories
- US-6: As a user, I can select a category to filter books
- US-7: As a user, I only see books from my selected category while swiping

### Epic 3: Liked Books
- US-8: As a user, I can view my list of liked books
- US-9: As a user, I can remove a book from my liked list
- US-10: As a user, I can tap a liked book to see its details

### Epic 4: Book Details
- US-11: As a user, I can tap a book card to see full details
- US-12: As a user, I see: description, page count, author, rating, reviews, cover
- US-13: As a user, I can like a book from the detail screen

### Epic 5: Auth & Profile
- US-14: As a user, I can register an account
- US-15: As a user, I can log in
- US-16: As a user, my liked books persist across sessions

### Epic 6: DevOps
- US-17: CI pipeline runs tests on every PR
- US-18: Code linting enforced in CI
- US-19: Backend has >70% test coverage

## Sprint Plan

### Sprint 1 (Features 1-3): Core Swipe + Backend
- Backend: FastAPI project setup, Google Books integration, book endpoints
- Frontend: Flutter project setup, swipe card UI, basic navigation
- DevOps: GitHub Actions CI for both

### Sprint 2 (Features 4-6): Categories + Details + Auth
- Backend: Categories, book details, auth endpoints
- Frontend: Categories screen, book detail screen, liked books screen, auth flow
- DevOps: Test coverage reporting
