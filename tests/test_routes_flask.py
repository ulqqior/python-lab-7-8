"""Інтеграційні тести HTTP-рівня для REST API маршрутів Flask (Завдання 6)."""


def test_flask_health_and_get_books_list(flask_client, flask_sample_data):
    """
    Позитивний сценарій: перевіряє GET /api/health та GET /api/books (із фільтрацією).
    """
    health_resp = flask_client.get("/api/health")
    assert health_resp.status_code == 200
    assert health_resp.get_json()["status"] == "ok"

    resp = flask_client.get("/api/books")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["count"] == 1
    assert data["books"][0]["title"] == "Захар Беркут"

    filtered_resp = flask_client.get("/api/books?status=available")
    assert filtered_resp.status_code == 200
    assert filtered_resp.get_json()["count"] == 1


def test_flask_get_book_by_id_200_and_404(flask_client, flask_sample_data):
    """
    Позитивний і негативний сценарії для GET /api/books/<id>:
    - 200 для існуючої книги;
    - 404 для неіснуючого ID.
    """
    book_id = flask_sample_data["book_id"]
    resp = flask_client.get(f"/api/books/{book_id}")
    assert resp.status_code == 200
    assert resp.get_json()["isbn"] == flask_sample_data["isbn"]

    not_found = flask_client.get("/api/books/99999")
    assert not_found.status_code == 404
    assert "error" in not_found.get_json()


def test_flask_post_create_book_json_positive(flask_client, flask_sample_data):
    """
    Позитивний сценарій POST /api/books із передачею JSON-даних:
    створює нову книгу та повертає статус 201 Created.
    """
    payload = {
        "title": "Украдене щастя",
        "isbn": "9789660389999",
        "author_id": flask_sample_data["author_id"],
        "price": 230.0,
        "pages": 160,
        "published_year": 2024,
        "genre_ids": [flask_sample_data["genre_id"]],
    }
    resp = flask_client.post("/api/books", json=payload)
    assert resp.status_code == 201
    created = resp.get_json()
    assert created["title"] == "Украдене щастя"
    assert created["isbn"] == "9789660389999"
    assert "Класика" in created["genres"]


def test_flask_post_create_book_negative_and_boundary_scenarios(flask_client, flask_sample_data):
    """
    Негативні та граничні сценарії для POST /api/books:
    - відсутні обов'язкові поля (400);
    - некоректна довжина ISBN (граничний сценарій, 400);
    - неіснуючий author_id (404);
    - дублікат ISBN (400).
    """
    # 1. Відсутні обов'язкові поля
    resp_missing = flask_client.post("/api/books", json={"title": "Тільки назва"})
    assert resp_missing.status_code == 400

    # 2. Граничний сценарій: ISBN не з 13 цифр
    resp_bad_isbn = flask_client.post(
        "/api/books",
        json={
            "title": "Тест ISBN",
            "isbn": "12345",
            "author_id": flask_sample_data["author_id"],
        },
    )
    assert resp_bad_isbn.status_code == 400

    # 3. Неіснуючий автор
    resp_no_author = flask_client.post(
        "/api/books",
        json={
            "title": "Книга без автора",
            "isbn": "9789660387777",
            "author_id": 9999,
        },
    )
    assert resp_no_author.status_code == 404

    # 4. Дублікат ISBN
    resp_dup = flask_client.post(
        "/api/books",
        json={
            "title": "Дублікат ISBN",
            "isbn": flask_sample_data["isbn"],
            "author_id": flask_sample_data["author_id"],
        },
    )
    assert resp_dup.status_code == 400


def test_flask_delete_book_200_and_404(flask_client, flask_sample_data):
    """Перевіряє DELETE /api/books/<id> для існуючої (200) та вже видаленої книги (404)."""
    book_id = flask_sample_data["book_id"]
    del_resp = flask_client.delete(f"/api/books/{book_id}")
    assert del_resp.status_code == 200
    assert del_resp.get_json()["status"] == "deleted"

    del_again = flask_client.delete(f"/api/books/{book_id}")
    assert del_again.status_code == 404
