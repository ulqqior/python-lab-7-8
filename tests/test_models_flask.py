"""Модульні тести моделей Flask-SQLAlchemy (Завдання 5)."""
import pytest
from sqlalchemy.exc import IntegrityError

from flask_library.models import Author, AuthorProfile, Book, BookReview, Genre, db


def test_flask_models_creation_relationships_and_str(flask_app, flask_sample_data):
    """Перевіряє створення моделей Flask, зв'язки 1:1, 1:N, M:N та рядкові представлення."""
    with flask_app.app_context():
        book = db.session.get(Book, flask_sample_data["book_id"])
        author = db.session.get(Author, flask_sample_data["author_id"])
        genre = db.session.get(Genre, flask_sample_data["genre_id"])

        assert str(author) == "Іван Франко"
        assert repr(author) == "<Author Іван Франко>"
        assert author.profile is not None
        assert author.profile.country == "Україна"
        assert str(author.profile) == f"Профіль автора #{author.id} (Україна)"
        assert repr(author.profile) == f"<AuthorProfile author_id={author.id} country=Україна>"

        assert str(genre) == "Класика"
        assert repr(genre) == "<Genre Класика>"

        assert str(book) == "Захар Беркут (9789660381129)"
        assert repr(book) == "<Book Захар Беркут (9789660381129)>"
        assert book.author == author
        assert genre in book.genres
        assert book in genre.books


def test_flask_book_reviews_and_cascade_delete(flask_app, flask_sample_data):
    """Перевіряє додавання відгуку на книгу та каскадне видалення у Flask-SQLAlchemy."""
    with flask_app.app_context():
        book = db.session.get(Book, flask_sample_data["book_id"])
        review = BookReview(
            book=book,
            reviewer_name="Тарас Петренко",
            rating=5,
            comment="Чудове видання!",
        )
        db.session.add(review)
        db.session.commit()

        assert str(review) == "Відгук від Тарас Петренко (5/5)"
        assert repr(review) == "<BookReview by Тарас Петренко (5/5)>"
        assert len(book.reviews) == 1

        db.session.delete(book)
        db.session.commit()
        assert db.session.query(BookReview).count() == 0


def test_flask_unique_constraint_and_rollback(flask_app, flask_sample_data):
    """Перевіряє обмеження унікальності ISBN та атомарний відкат транзакції (rollback)."""
    with flask_app.app_context():
        duplicate = Book(
            title="Дублікат",
            isbn=flask_sample_data["isbn"],
            author_id=flask_sample_data["author_id"],
        )
        db.session.add(duplicate)
        with pytest.raises(IntegrityError):
            db.session.commit()
        db.session.rollback()
        assert db.session.query(Book).count() == 1


@pytest.mark.parametrize(
    "title,isbn,price,pages",
    [
        ("Перехресні стежки", "9789660390001", 260.0, 320),
        ("Мойсей", "9789660390002", 190.0, 128),
        ("Борислав сміється", "9789660390003", 315.5, 384),
    ],
)
def test_flask_book_parametrized(flask_app, flask_sample_data, title, isbn, price, pages):
    """Параметризований тест створення книги у Flask-SQLAlchemy."""
    with flask_app.app_context():
        book = Book(
            title=title,
            isbn=isbn,
            price=price,
            pages=pages,
            author_id=flask_sample_data["author_id"],
        )
        db.session.add(book)
        db.session.commit()
        data = book.to_dict()
        assert data["title"] == title
        assert data["isbn"] == isbn
        assert data["price"] == price
        assert data["pages"] == pages
