def test_discover_books_guest(client, mock_google_books_search):
    resp = client.get("/api/books/discover?category=fiction")
    assert resp.status_code == 200
    data = resp.json()
    assert "books" in data
    assert "total" in data
    assert "page" in data
    assert "page_size" in data
    assert len(data["books"]) == 2
    assert data["books"][0]["google_book_id"] == "book_1"


def test_discover_books_authenticated(client, auth_headers, mock_google_books_search):
    resp = client.get("/api/books/discover?category=fiction", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["books"]) == 2


def test_discover_books_excludes_liked(client, auth_headers, mock_google_books_search):
    # Like a book first
    client.post("/api/books/like", json={
        "google_book_id": "book_1",
        "title": "Test Book One",
        "authors": "Author A",
        "thumbnail": "https://books.google.com/thumb1.jpg",
    }, headers=auth_headers)

    resp = client.get("/api/books/discover?category=fiction", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    book_ids = [b["google_book_id"] for b in data["books"]]
    assert "book_1" not in book_ids


def test_discover_books_excludes_skipped(client, auth_headers, mock_google_books_search):
    client.post("/api/books/skip", json={
        "google_book_id": "book_2",
    }, headers=auth_headers)

    resp = client.get("/api/books/discover?category=fiction", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    book_ids = [b["google_book_id"] for b in data["books"]]
    assert "book_2" not in book_ids


def test_discover_books_pagination(client, mock_google_books_search):
    resp = client.get("/api/books/discover?category=fiction&page=1&page_size=10")
    assert resp.status_code == 200
    data = resp.json()
    assert data["page"] == 1
    assert data["page_size"] == 10


def test_discover_books_invalid_page(client):
    resp = client.get("/api/books/discover?category=fiction&page=0")
    assert resp.status_code == 422


def test_discover_books_default_category(client, mock_google_books_search):
    resp = client.get("/api/books/discover")
    assert resp.status_code == 200


def test_get_book_detail(client, mock_google_book_detail):
    resp = client.get("/api/books/book_1")
    assert resp.status_code == 200
    data = resp.json()
    assert data["google_book_id"] == "book_1"
    assert data["title"] == "Test Book One"
    assert data["description"] == "A test book description."
    assert data["page_count"] == 200
    assert data["authors"] == ["Author A"]


def test_get_book_detail_no_auth_required(client, mock_google_book_detail):
    resp = client.get("/api/books/book_1")
    assert resp.status_code == 200


def test_like_book(client, auth_headers):
    resp = client.post("/api/books/like", json={
        "google_book_id": "book_1",
        "title": "Test Book One",
        "authors": "Author A",
        "thumbnail": "https://books.google.com/thumb1.jpg",
    }, headers=auth_headers)
    assert resp.status_code == 201
    data = resp.json()
    assert data["google_book_id"] == "book_1"
    assert data["title"] == "Test Book One"


def test_like_book_duplicate(client, auth_headers):
    client.post("/api/books/like", json={
        "google_book_id": "book_1",
        "title": "Test Book One",
        "authors": "Author A",
        "thumbnail": "https://books.google.com/thumb1.jpg",
    }, headers=auth_headers)

    resp = client.post("/api/books/like", json={
        "google_book_id": "book_1",
        "title": "Test Book One",
        "authors": "Author A",
        "thumbnail": "https://books.google.com/thumb1.jpg",
    }, headers=auth_headers)
    assert resp.status_code == 409


def test_like_book_unauthenticated(client):
    resp = client.post("/api/books/like", json={
        "google_book_id": "book_1",
    })
    assert resp.status_code == 401


def test_skip_book(client, auth_headers):
    resp = client.post("/api/books/skip", json={
        "google_book_id": "book_1",
    }, headers=auth_headers)
    assert resp.status_code == 201
    assert "skipped" in resp.json()["message"].lower()


def test_skip_book_duplicate(client, auth_headers):
    client.post("/api/books/skip", json={
        "google_book_id": "book_1",
    }, headers=auth_headers)

    resp = client.post("/api/books/skip", json={
        "google_book_id": "book_1",
    }, headers=auth_headers)
    assert resp.status_code == 201
    assert "already skipped" in resp.json()["message"].lower()


def test_skip_book_unauthenticated(client):
    resp = client.post("/api/books/skip", json={
        "google_book_id": "book_1",
    })
    assert resp.status_code == 401


def test_get_liked_books(client, auth_headers):
    # Like two books
    client.post("/api/books/like", json={
        "google_book_id": "book_1",
        "title": "Test Book One",
        "authors": "Author A",
        "thumbnail": "thumb1.jpg",
    }, headers=auth_headers)
    client.post("/api/books/like", json={
        "google_book_id": "book_2",
        "title": "Test Book Two",
        "authors": "Author B",
        "thumbnail": "thumb2.jpg",
    }, headers=auth_headers)

    resp = client.get("/api/books/liked", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 2
    assert len(data["books"]) == 2


def test_get_liked_books_pagination(client, auth_headers):
    for i in range(5):
        client.post("/api/books/like", json={
            "google_book_id": f"book_{i}",
            "title": f"Book {i}",
            "authors": "Author",
            "thumbnail": "thumb.jpg",
        }, headers=auth_headers)

    resp = client.get("/api/books/liked?page=1&page_size=2", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 5
    assert len(data["books"]) == 2
    assert data["page"] == 1
    assert data["page_size"] == 2


def test_get_liked_books_unauthenticated(client):
    resp = client.get("/api/books/liked")
    assert resp.status_code == 401


def test_unlike_book(client, auth_headers):
    client.post("/api/books/like", json={
        "google_book_id": "book_1",
        "title": "Test Book One",
        "authors": "Author A",
        "thumbnail": "thumb1.jpg",
    }, headers=auth_headers)

    resp = client.delete("/api/books/liked/book_1", headers=auth_headers)
    assert resp.status_code == 200
    assert "removed" in resp.json()["message"].lower()

    # Verify it's gone
    resp = client.get("/api/books/liked", headers=auth_headers)
    assert resp.json()["total"] == 0


def test_unlike_book_not_found(client, auth_headers):
    resp = client.delete("/api/books/liked/nonexistent", headers=auth_headers)
    assert resp.status_code == 404


def test_unlike_book_unauthenticated(client):
    resp = client.delete("/api/books/liked/book_1")
    assert resp.status_code == 401


def test_health_check(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"
