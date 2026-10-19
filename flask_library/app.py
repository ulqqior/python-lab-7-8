"""Фабрика додатку Flask, підключення Flask-SQLAlchemy, Flask-Migrate та REST API маршрути."""
from pathlib import Path
from flask import Flask, jsonify, request
from flask_migrate import Migrate
from sqlalchemy.exc import IntegrityError

from .models import Author, Book, Genre, db

BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_DB_URI = f"sqlite:///{BASE_DIR / 'library_flask.db'}"

migrate = Migrate()


def create_app(test_config: dict | None = None) -> Flask:
    """Створює та налаштовує екземпляр додатку Flask."""
    app = Flask(__name__)
    app.config.from_mapping(
        SECRET_KEY="flask-lab7-8-secret-key",
        SQLALCHEMY_DATABASE_URI=DEFAULT_DB_URI,
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
    )

    if test_config is not None:
        app.config.update(test_config)

    db.init_app(app)
    migrate.init_app(app, db)

    @app.route("/api/health", methods=["GET"])
    def health_check():
        return jsonify({"status": "ok", "service": "flask_library"}), 200

    @app.route("/api/books", methods=["GET"])
    def list_books():
        """Повертає список книг у форматі JSON з опційною фільтрацією за статусом."""
        status_filter = request.args.get("status")
        query = db.session.query(Book)
        if status_filter:
            query = query.filter_by(status=status_filter)
        books = query.order_by(Book.published_year.desc(), Book.title.asc()).all()
        return jsonify({"count": len(books), "books": [b.to_dict() for b in books]}), 200

    @app.route("/api/books/<int:book_id>", methods=["GET"])
    def get_book(book_id: int):
        """Повертає деталі однієї книги за ID або 404."""
        book = db.session.get(Book, book_id)
        if book is None:
            return jsonify({"error": "Книгу не знайдено"}), 404
        return jsonify(book.to_dict()), 200

    @app.route("/api/books", methods=["POST"])
    def create_book():
        """Створює нову книгу з JSON-тіла запиту."""
        payload = request.get_json(silent=True) or {}
        title = (payload.get("title") or "").strip()
        isbn = (payload.get("isbn") or "").strip()
        author_id = payload.get("author_id")

        if not title or not isbn or not author_id:
            return (
                jsonify(
                    {
                        "error": "Поля 'title', 'isbn' та 'author_id' є обов'язковими."
                    }
                ),
                400,
            )

        if len(isbn) != 13 or not isbn.isdigit():
            return jsonify({"error": "ISBN має складатися рівно з 13 цифр."}), 400

        author = db.session.get(Author, author_id)
        if author is None:
            return jsonify({"error": "Автора із вказаним ID не знайдено."}), 404

        book = Book(
            title=title,
            isbn=isbn,
            author_id=author.id,
            price=float(payload.get("price", 250.0)),
            pages=int(payload.get("pages", 150)),
            published_year=int(payload.get("published_year", 2024)),
            status=payload.get("status", "available"),
        )

        genre_ids = payload.get("genre_ids", [])
        for gid in genre_ids:
            genre = db.session.get(Genre, gid)
            if genre:
                book.genres.append(genre)

        try:
            db.session.add(book)
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            return jsonify({"error": "Книга з таким ISBN вже існує."}), 400

        return jsonify(book.to_dict()), 201

    @app.route("/api/books/<int:book_id>", methods=["DELETE"])
    def delete_book(book_id: int):
        """Видаляє книгу за ID."""
        book = db.session.get(Book, book_id)
        if book is None:
            return jsonify({"error": "Книгу не знайдено"}), 404
        db.session.delete(book)
        db.session.commit()
        return jsonify({"deleted_id": book_id, "status": "deleted"}), 200

    return app


app = create_app()
