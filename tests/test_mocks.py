"""Мок-тестування зовнішніх та внутрішніх залежностей через @patch та MagicMock (Завдання 7)."""
from decimal import Decimal
from unittest.mock import MagicMock, patch
import pytest

from catalog.models import Book
from catalog.services import (
    calculate_discounted_price,
    enrich_book_from_external_api,
    get_loyalty_discount_percent,
    reserve_book_copy,
)


@pytest.mark.django_db
@patch("catalog.services.requests.get")
def test_enrich_book_from_external_api_mocked_http(mock_requests_get, sample_book):
    """
    Мок №1 (зовнішній виклик): підміняє HTTP-запит requests.get до зовнішнього API OpenLibrary.
    Перевіряє, що метод викликано з очікуваним URL і timeout=5 через assert_called_once_with,
    а кількість сторінок книги оновлено без реального мережевого з'єднання.
    """
    fake_response = MagicMock()
    fake_response.json.return_value = {
        "title": "Маруся Чурай (Академічне видання)",
        "publishers": ["А-БА-БА-ГА-ЛА-МА-ГА"],
        "number_of_pages": 256,
    }
    fake_response.raise_for_status.return_value = None
    mock_requests_get.return_value = fake_response

    result = enrich_book_from_external_api(sample_book)

    expected_url = f"https://openlibrary.org/isbn/{sample_book.isbn}.json"
    mock_requests_get.assert_called_once_with(expected_url, timeout=5)
    fake_response.raise_for_status.assert_called_once_with()

    sample_book.refresh_from_db()
    assert sample_book.pages == 256
    assert result["external_title"] == "Маруся Чурай (Академічне видання)"
    assert result["number_of_pages"] == 256


@pytest.mark.django_db
@patch("catalog.services.generate_reservation_code")
def test_reserve_book_copy_mocked_internal_generator(mock_generate_code, sample_book):
    """
    Мок №2 (внутрішня залежність): підміняє генератор випадкових кодів generate_reservation_code.
    Забезпечує детерміновану перевірку результату бронювання та перевіряє виклик
    mock_generate_code.assert_called_once_with(prefix="RES").
    """
    mock_generate_code.return_value = "RES-FIXED777"

    reservation = reserve_book_copy(sample_book, reader_email="reader@library.ua")

    mock_generate_code.assert_called_once_with(prefix="RES")
    assert reservation["reservation_code"] == "RES-FIXED777"
    assert reservation["reader_email"] == "reader@library.ua"
    assert reservation["new_status"] == Book.STATUS_BORROWED

    sample_book.refresh_from_db()
    assert sample_book.status == Book.STATUS_BORROWED

    # Повторне бронювання вже виданої книги має викликати ValueError
    with pytest.raises(ValueError, match="Книга недоступна для бронювання"):
        reserve_book_copy(sample_book, reader_email="another@library.ua")


@pytest.mark.django_db
@patch("catalog.services.get_loyalty_discount_percent")
def test_calculate_discounted_price_with_mocked_discount_helper(
    mock_discount_fn, sample_book, sample_profile
):
    """
    Додатковий мок внутрішньої залежності: підміняє функцію визначення відсотка знижки
    та перевіряє точність виклику з кількістю нагород автора (12).
    """
    mock_discount_fn.return_value = Decimal("10.0")

    final_price = calculate_discounted_price(sample_book)

    mock_discount_fn.assert_called_once_with(12)
    assert final_price == Decimal("288.00")


def test_loyalty_discount_helper_direct_branches():
    """Перевіряє гілки функції get_loyalty_discount_percent для повноти покриття."""
    assert get_loyalty_discount_percent(10) == Decimal("15.0")
    assert get_loyalty_discount_percent(2) == Decimal("5.0")
    assert get_loyalty_discount_percent(0) == Decimal("0.0")
