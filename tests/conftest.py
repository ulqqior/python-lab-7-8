"""Спільні фікстури PyTest для тестування Django та Flask проєктів (Завдання 5-7)."""
from decimal import Decimal
import pytest
from django.contrib.auth.models import User

from catalog.models import Author, AuthorProfile, Book, BookReview, Genre
from flask_library.app import create_app
from flask_library.models import (
    Author as FlaskAuthor,
    AuthorProfile as FlaskAuthorProfile,
    Book as FlaskBook,
    Genre as FlaskGenre,
    db as flask_db,
)


# =====================================================================
# Фікстури для Django-проєкту
# =====================================================================

@pytest.fixture
def django_client():
    """Повертає тестовий HTTP-клієнт Django (django.test.Client)."""
    from django.test import Client

    return Client()


@pytest.fixture
def test_user(db):
    """Створює тестового користувача Django."""
    return User.objects.create_user(
        username="librarian",
        email="librarian@library.ua",
        password="TestPassword123!",
    )


@pytest.fixture
def authenticated_client(django_client, test_user):
    """Повертає тестовий HTTP-клієнт Django з виконаним входом користувача."""
    django_client.force_login(test_user)
    return django_client


@pytest.fixture
def sample_author(db):
    """Створює тестового основного автора у базі Django."""
    return Author.objects.create(
        first_name="Ліна",
        last_name="Костенко",
        email="lina.kostenko@library.ua",
        is_active=True,
    )


@pytest.fixture
def second_author(db):
    """Створює другого тестового автора (наприклад, для перевірки SET_NULL)."""
    return Author.objects.create(
        first_name="Сергій",
        last_name="Жадан",
        email="serhiy.zhadan@library.ua",
        is_active=True,
    )


@pytest.fixture
def sample_profile(sample_author):
    """Створює профіль автора (1:1) для sample_author."""
    return AuthorProfile.objects.create(
        author=sample_author,
        biography="Українська письменниця та поетеса.",
        website="https://example.org/kostenko",
        country="Україна",
        awards_count=12,
    )


@pytest.fixture
def sample_genres(db):
    """Створює набір тестових жанрів для перевірки зв'язку M:N."""
    g1 = Genre.objects.create(
        name="Поезія",
        slug="poetry",
        description="Поетичні твори",
        is_featured=True,
    )
    g2 = Genre.objects.create(
        name="Історичний роман",
        slug="historical-novel",
        description="Художні історичні романи",
        is_featured=False,
    )
    return [g1, g2]


@pytest.fixture
def sample_book(sample_author, second_author, sample_genres):
    """Створює тестову книгу з прив'язаним автором, рекомендатором, жанрами та відгуком."""
    book = Book.objects.create(
        title="Маруся Чурай",
        isbn="9789660372011",
        status=Book.STATUS_AVAILABLE,
        price=Decimal("320.00"),
        pages=224,
        published_year=2021,
        language="Українська",
        summary="Історичний роман у віршах.",
        author=sample_author,
        recommended_by=second_author,
    )
    book.genres.set(sample_genres)
    BookReview.objects.create(
        book=book,
        reviewer_name="Оксана Коваль",
        rating=5,
        comment="Неперевершений твір!",
    )
    return book


# =====================================================================
# Фікстури для Flask-проєкту
# =====================================================================

@pytest.fixture
def flask_app():
    """Створює ізольований екземпляр Flask-додатку з базою SQLite у пам'яті."""
    app = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        }
    )
    with app.app_context():
        flask_db.create_all()
        yield app
        flask_db.session.remove()
        flask_db.drop_all()


@pytest.fixture
def flask_client(flask_app):
    """Повертає тестовий HTTP-клієнт Flask."""
    return flask_app.test_client()


@pytest.fixture
def flask_sample_data(flask_app):
    """Наповнює тестову базу Flask початковими даними (автор, профіль, жанр, книга)."""
    with flask_app.app_context():
        author = FlaskAuthor(
            first_name="Іван",
            last_name="Франко",
            email="ivan.franko@library.ua",
        )
        profile = FlaskAuthorProfile(
            author=author,
            biography="Класик української літератури.",
            country="Україна",
            awards_count=10,
        )
        genre = FlaskGenre(
            name="Класика",
            slug="classics",
            description="Класична література",
            is_featured=True,
        )
        book = FlaskBook(
            title="Захар Беркут",
            isbn="9789660381129",
            status="available",
            price=280.0,
            pages=256,
            published_year=2022,
            author=author,
        )
        book.genres.append(genre)
        flask_db.session.add_all([author, profile, genre, book])
        flask_db.session.commit()
        return {
            "author_id": author.id,
            "genre_id": genre.id,
            "book_id": book.id,
            "isbn": book.isbn,
        }
