"""Сервісний шар бібліотеки: зовнішні інтеграції та внутрішня бізнес-логіка (Завдання 7)."""
from decimal import Decimal
import uuid
import requests

from .models import Book


def fetch_external_book_metadata(isbn: str) -> dict:
    """
    Зовнішня залежність: виконує HTTP-запит до стороннього API OpenLibrary
    для отримання метаданих книги за ISBN.
    """
    url = f"https://openlibrary.org/isbn/{isbn}.json"
    response = requests.get(url, timeout=5)
    response.raise_for_status()
    data = response.json()
    return {
        "isbn": isbn,
        "external_title": data.get("title", "Невідома назва"),
        "publishers": data.get("publishers", []),
        "number_of_pages": data.get("number_of_pages", 0),
    }


def enrich_book_from_external_api(book: Book) -> dict:
    """
    Оновлює кількість сторінок книги на основі відповіді зовнішнього сервісу
    та повертає збагачений словник даних.
    """
    metadata = fetch_external_book_metadata(book.isbn)
    if metadata.get("number_of_pages"):
        book.pages = int(metadata["number_of_pages"])
        book.save(update_fields=["pages"])
    return metadata


def generate_reservation_code(prefix: str = "LIB") -> str:
    """
    Внутрішня залежність: генерує випадковий код бронювання примірника.
    """
    random_part = uuid.uuid4().hex[:8].upper()
    return f"{prefix}-{random_part}"


def reserve_book_copy(book: Book, reader_email: str) -> dict:
    """
    Бронює книгу для читача, використовуючи внутрішній генератор коду,
    та змінює статус примірника на 'borrowed'.
    """
    if book.status != Book.STATUS_AVAILABLE:
        raise ValueError("Книга недоступна для бронювання.")

    code = generate_reservation_code(prefix="RES")
    book.status = Book.STATUS_BORROWED
    book.save(update_fields=["status"])
    return {
        "reservation_code": code,
        "book_id": book.id,
        "isbn": book.isbn,
        "reader_email": reader_email,
        "new_status": book.status,
    }


def get_loyalty_discount_percent(awards_count: int) -> Decimal:
    """
    Внутрішня функція розрахунку акційної знижки залежно від кількості нагород автора.
    """
    if awards_count >= 5:
        return Decimal("15.0")
    if awards_count >= 1:
        return Decimal("5.0")
    return Decimal("0.0")


def calculate_discounted_price(book: Book) -> Decimal:
    """
    Обчислює підсумкову вартість книги з урахуванням знижки.
    """
    awards = getattr(getattr(book.author, "profile", None), "awards_count", 0)
    discount_percent = get_loyalty_discount_percent(awards)
    multiplier = (Decimal("100.0") - discount_percent) / Decimal("100.0")
    return (Decimal(str(book.price)) * multiplier).quantize(Decimal("0.01"))
