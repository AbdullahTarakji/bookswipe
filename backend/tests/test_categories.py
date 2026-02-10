def test_list_categories(client):
    resp = client.get("/api/categories")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 14
    names = [c["name"] for c in data]
    assert "Fiction" in names
    assert "Romance" in names
    assert "Horror" in names
    assert "Comics" in names


def test_categories_sorted_by_name(client):
    resp = client.get("/api/categories")
    data = resp.json()
    names = [c["name"] for c in data]
    assert names == sorted(names)


def test_category_has_required_fields(client):
    resp = client.get("/api/categories")
    data = resp.json()
    for cat in data:
        assert "id" in cat
        assert "name" in cat
        assert "google_category_key" in cat


def test_get_category_by_id(client):
    # First get all categories to find a valid ID
    all_cats = client.get("/api/categories").json()
    cat_id = all_cats[0]["id"]

    resp = client.get(f"/api/categories/{cat_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == cat_id
    assert data["name"] == all_cats[0]["name"]


def test_get_category_not_found(client):
    resp = client.get("/api/categories/9999")
    assert resp.status_code == 404


def test_categories_no_auth_required(client):
    resp = client.get("/api/categories")
    assert resp.status_code == 200
