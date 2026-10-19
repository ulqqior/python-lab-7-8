"""Моделі даних Flask-SQLAlchemy для онлайн-бібліотеки (Завдання 3)."""
from datetime import datetime, timezone
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# Явна проміжна таблиця (junction table) для зв'язку «багато-до-багатьох» між Book та Genre
book_genres = db.Table(
    "book_genres",
    db.Column(
        "book_id",
        db.Integer,
        db.ForeignKey("books.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    db.Column(
        "genre_id",
        db.Integer,
        db.ForeignKey("genres.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)


class Author(db.Model):
    """Сутність Автора книги у Flask-SQLAlchemy."""

    __tablename__ = "authors"

    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(254), unique=True, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)

    # Зв'язок 1:1 із AuthorProfile (uselist=False у backref)
    profile = db.relationship(
        "AuthorProfile",
        backref=db.backref("author", uselist=False),
        uselist=False,
        cascade="all, delete-orphan",
    )

    # Зв'язок 1:N із Book через backref="author"
    books = db.relationship(
        "Book",
        backref="author",
        lazy="select",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Author {self.first_name} {self.last_name}>"

    def __str__(self) -> str:
        return f"{self.first_name} {self.last_name}"


class AuthorProfile(db.Model):
    """Профіль автора (зв'язок один-до-одного із Author)."""

    __tablename__ = "author_profiles"

    id = db.Column(db.Integer, primary_key=True)
    author_id = db.Column(
        db.Integer,
        db.ForeignKey("authors.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    biography = db.Column(db.Text, default="", nullable=False)
    website = db.Column(db.String(200), nullable=True)
    country = db.Column(db.String(80), default="Україна", nullable=False)
    awards_count = db.Column(db.Integer, default=0, nullable=False)

    def __repr__(self) -> str:
        return f"<AuthorProfile author_id={self.author_id} country={self.country}>"

    def __str__(self) -> str:
        return f"Профіль автора #{self.author_id} ({self.country})"


class Genre(db.Model):
    """Літературний жанр для зв'язку багато-до-багатьох із Book."""

    __tablename__ = "genres"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    slug = db.Column(db.String(80), unique=True, nullable=False)
    description = db.Column(db.Text, default="", nullable=False)
    is_featured = db.Column(db.Boolean, default=False, nullable=False)

    def __repr__(self) -> str:
        return f"<Genre {self.name}>"

    def __str__(self) -> str:
        return self.name


class Book(db.Model):
    """Книга в каталозі онлайн-бібліотеки (Flask-SQLAlchemy)."""

    __tablename__ = "books"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    isbn = db.Column(db.String(13), unique=True, nullable=False)
    status = db.Column(db.String(20), default="available", nullable=False)
    price = db.Column(db.Float, default=250.0, nullable=False)
    pages = db.Column(db.Integer, default=100, nullable=False)
    published_year = db.Column(db.Integer, default=2024, nullable=False)
    language = db.Column(db.String(50), default="Українська", nullable=False, server_default="Українська")
    summary = db.Column(db.Text, default="", nullable=False, server_default="")
    author_id = db.Column(
        db.Integer,
        db.ForeignKey("authors.id", ondelete="RESTRICT"),
        nullable=False,
    )
    created_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Зв'язок M:N через проміжну таблицю book_genres із backref="books"
    genres = db.relationship(
        "Genre",
        secondary=book_genres,
        lazy="subquery",
        backref=db.backref("books", lazy=True),
    )

    # Зв'язок 1:N із BookReview
    reviews = db.relationship(
        "BookReview",
        backref="book",
        lazy="select",
        cascade="all, delete-orphan",
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "isbn": self.isbn,
            "status": self.status,
            "price": self.price,
            "pages": self.pages,
            "published_year": self.published_year,
            "language": getattr(self, "language", "Українська"),
            "author_id": self.author_id,
            "author_name": str(self.author) if self.author else None,
            "genres": [g.name for g in self.genres],
        }

    def __repr__(self) -> str:
        return f"<Book {self.title} ({self.isbn})>"

    def __str__(self) -> str:
        return f"{self.title} ({self.isbn})"


class BookReview(db.Model):
    """Відгук читача на книгу."""

    __tablename__ = "book_reviews"

    id = db.Column(db.Integer, primary_key=True)
    book_id = db.Column(
        db.Integer,
        db.ForeignKey("books.id", ondelete="CASCADE"),
        nullable=False,
    )
    reviewer_name = db.Column(db.String(100), nullable=False)
    rating = db.Column(db.Integer, default=5, nullable=False)
    comment = db.Column(db.Text, nullable=False)
    is_approved = db.Column(db.Boolean, default=True, nullable=False)

    def __repr__(self) -> str:
        return f"<BookReview by {self.reviewer_name} ({self.rating}/5)>"

    def __str__(self) -> str:
        return f"Відгук від {self.reviewer_name} ({self.rating}/5)"
