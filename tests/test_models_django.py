"""Модульні тести моделей Django ORM (Завдання 5)."""
from decimal import Decimal
import pytest
from django.db import IntegrityError
from django.db.models import ProtectedError

from catalog.models import Author, AuthorProfile, Book, BookReview, Genre


@pytest.mark.django_db
def test_author_and_profile_creation_and_str(sample_author, sample_profile):
    """Перевіряє створення автора та профілю (1:1), значення за замовчуванням та __str__."""
    assert sample_author.is_active is True
    assert str(sample_author) == "Ліна Костенко"
    assert sample_author.profile == sample_profile
    assert sample_profile.country == "Україна"
    assert sample_profile.awards_count == 12
    assert str(sample_profile) == "Профіль: Ліна Костенко (Україна)"


@pytest.mark.django_db
def test_book_creation_defaults_and_absolute_url(sample_author):
    """Перевіряє значення полів Book за замовчуванням, __str__ та get_absolute_url."""
    book = Book.objects.create(
        title="Берестечко",
        isbn="9789667047999",
        author=sample_author,
    )
    assert book.status == Book.STATUS_AVAILABLE
    assert book.price == Decimal("250.00")
    assert book.pages == 100
    assert book.published_year == 2024
    assert book.language == "Українська"
    assert str(book) == "Берестечко (9789667047999)"
    assert book.get_absolute_url() == f"/books/{book.pk}/"


@pytest.mark.django_db
def test_unique_constraints_isbn_and_author_email(sample_author, sample_book):
    """Перевіряє обмеження unique для email автора та ISBN книги."""
    from django.db import transaction

    with pytest.raises(IntegrityError):
        with transaction.atomic():
            Author.objects.create(
                first_name="Дублікат",
                last_name="Автор",
                email=sample_author.email,
            )

    with pytest.raises(IntegrityError):
        with transaction.atomic():
            Book.objects.create(
                title="Інша книга з тим самим ISBN",
                isbn=sample_book.isbn,
                author=sample_author,
            )


@pytest.mark.django_db
def test_many_to_many_and_reverse_relations(sample_author, sample_book, sample_genres):
    """Перевіряє зв'язок ManyToManyField між Book та Genre і зворотні зв'язки."""
    assert sample_book.genres.count() == 2
    poetry_genre = sample_genres[0]
    assert sample_book in poetry_genre.books.all()
    assert sample_book in sample_author.books.all()
    assert str(poetry_genre) == "Поезія"


@pytest.mark.django_db
def test_on_delete_protect_prevents_author_deletion(sample_author, sample_book):
    """Перевіряє політику on_delete=PROTECT: не можна видалити автора, який має книги."""
    with pytest.raises(ProtectedError):
        sample_author.delete()
    assert Author.objects.filter(pk=sample_author.pk).exists()


@pytest.mark.django_db
def test_on_delete_cascade_for_reviews_and_profile(sample_book, second_author):
    """Перевіряє політику on_delete=CASCADE: видалення книги видаляє її відгуки, а видалення автора — профіль."""
    review_id = sample_book.reviews.first().id
    assert str(sample_book.reviews.first()).startswith("Відгук від Оксана Коваль")
    sample_book.delete()
    assert not BookReview.objects.filter(id=review_id).exists()

    profile = AuthorProfile.objects.create(author=second_author, country="Україна")
    profile_id = profile.id
    second_author.delete()
    assert not AuthorProfile.objects.filter(id=profile_id).exists()


@pytest.mark.django_db
def test_on_delete_set_null_for_recommended_by(sample_book, second_author):
    """Перевіряє політику on_delete=SET_NULL: видалення автора-рекомендатора залишає книгу з recommended_by=None."""
    assert sample_book.recommended_by == second_author
    second_author.delete()
    sample_book.refresh_from_db()
    assert sample_book.recommended_by is None
    assert Book.objects.filter(pk=sample_book.pk).exists()


@pytest.mark.django_db
@pytest.mark.parametrize(
    "title,isbn,status,price,pages",
    [
        ("Кобзар", "9789660310015", Book.STATUS_AVAILABLE, Decimal("450.00"), 640),
        ("Тигролови", "9789660310022", Book.STATUS_BORROWED, Decimal("290.50"), 312),
        ("Місто", "9789660310039", Book.STATUS_ARCHIVED, Decimal("210.00"), 280),
        ("Енеїда", "9789660310046", Book.STATUS_AVAILABLE, Decimal("399.99"), 480),
    ],
)
def test_book_creation_parametrized(sample_author, title, isbn, status, price, pages):
    """Параметризований тест створення книги з різними наборами вхідних даних."""
    book = Book.objects.create(
        title=title,
        isbn=isbn,
        status=status,
        price=price,
        pages=pages,
        author=sample_author,
    )
    assert book.pk is not None
    assert book.title == title
    assert book.isbn == isbn
    assert book.status == status
    assert book.price == price
    assert book.pages == pages
    assert str(book) == f"{title} ({isbn})"
