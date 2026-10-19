"""Інтеграційні тести HTTP-рівня для views і маршрутів Django (Завдання 6)."""
import pytest
from django.urls import reverse

from catalog.models import Book


@pytest.mark.django_db
def test_book_list_view_200_template_and_filter(django_client, sample_book):
    """
    Позитивний сценарій: перевіряє маршрут GET /books/, статус 200,
    шаблон catalog/book_list.html, вміст сторінки та фільтр ?status=available.
    """
    url = reverse("catalog:book_list")
    response = django_client.get(url)
    assert response.status_code == 200
    template_names = [t.name for t in response.templates]
    assert "catalog/book_list.html" in template_names
    content = response.content.decode("utf-8")
    assert "Маруся Чурай" in content
    assert "Ліна Костенко" in content

    # Перевірка фільтрації за статусом
    filtered_response = django_client.get(url, {"status": "borrowed"})
    assert filtered_response.status_code == 200
    assert "Маруся Чурай" not in filtered_response.content.decode("utf-8")


@pytest.mark.django_db
def test_book_detail_view_200_and_404(django_client, sample_book):
    """
    Позитивний і негативний сценарії для GET /books/<pk>/:
    - 200 та шаблон catalog/book_detail.html для існуючої книги;
    - 404 для неіснуючого ідентифікатора.
    """
    valid_url = reverse("catalog:book_detail", kwargs={"pk": sample_book.pk})
    response = django_client.get(valid_url)
    assert response.status_code == 200
    assert "catalog/book_detail.html" in [t.name for t in response.templates]
    assert sample_book.isbn in response.content.decode("utf-8")

    invalid_url = reverse("catalog:book_detail", kwargs={"pk": 99999})
    not_found_response = django_client.get(invalid_url)
    assert not_found_response.status_code == 404


@pytest.mark.django_db
def test_book_create_view_unauthenticated_redirects_302(django_client):
    """
    Негативний сценарій авторизації: неавторизований запит до захищеного маршруту
    GET/POST /books/create/ повертає статус 302 (редірект на сторінку входу).
    """
    create_url = reverse("catalog:book_create")
    response = django_client.get(create_url)
    assert response.status_code == 302
    assert "/accounts/login/" in response["Location"]


@pytest.mark.django_db
def test_book_create_view_authenticated_positive_and_negative(authenticated_client, sample_author):
    """
    Перевіряє поведінку GET/POST /books/create/ для авторизованого користувача:
    - GET повертає 200 і форму catalog/book_form.html;
    - POST із валідними даними створює книгу та повертає 302 редірект;
    - POST із порожніми обов'язковими полями повертає 400 (граничний/негативний сценарій).
    """
    create_url = reverse("catalog:book_create")
    get_resp = authenticated_client.get(create_url)
    assert get_resp.status_code == 200
    assert "catalog/book_form.html" in [t.name for t in get_resp.templates]

    # Негативний сценарій: порожні поля
    import html

    bad_post = authenticated_client.post(create_url, {"title": "", "isbn": ""})
    assert bad_post.status_code == 400
    assert "Усі обов'язкові поля мають бути заповнені" in html.unescape(
        bad_post.content.decode("utf-8")
    )

    # Позитивний сценарій: валідне створення книги
    valid_post = authenticated_client.post(
        create_url,
        {
            "title": "Сад нетанучих скульптур",
            "isbn": "9789660375555",
            "author_id": sample_author.id,
            "price": "340.00",
            "pages": "304",
            "published_year": "2023",
        },
    )
    assert valid_post.status_code == 302
    created_book = Book.objects.get(isbn="9789660375555")
    assert valid_post["Location"] == reverse("catalog:book_detail", kwargs={"pk": created_book.pk})


@pytest.mark.django_db
def test_catalog_stats_api_view(django_client, sample_book):
    """Перевіряє JSON-маршрут GET /api/stats/ у Django."""
    response = django_client.get(reverse("catalog:catalog_stats"))
    assert response.status_code == 200
    payload = response.json()
    assert payload["total_books"] == 1
    assert payload["avg_price"] == 320.0
