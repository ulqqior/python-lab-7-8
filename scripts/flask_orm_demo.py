"""
Демонстрація можливостей Flask-SQLAlchemy ORM (Завдання 4):
- Повний цикл CRUD через db.session (Unit of Work)
- Фільтрація (filter, filter_by, or_), агрегація (func.count, func.avg), eager loading (joinedload)
- Сценарій транзакційної атомарності: успішний commit та автоматичний rollback при помилці
"""
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from sqlalchemy import func, or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import joinedload

from flask_library.app import create_app
from flask_library.models import Author, AuthorProfile, Book, BookReview, Genre, book_genres, db


def run_flask_orm_demo() -> None:
    print("=" * 72)
    print("ДЕМОНСТРАЦІЯ ЗАПИТІВ FLASK-SQLALCHEMY ТА ТРАНЗАКЦІЙ (ЗАВДАННЯ 4)")
    print("=" * 72)

    app = create_app()
    with app.app_context():
        db.create_all()
        # Очищення перед демонстрацією
        db.session.execute(book_genres.delete())
        db.session.query(BookReview).delete()
        db.session.query(Book).delete()
        db.session.query(AuthorProfile).delete()
        db.session.query(Genre).delete()
        db.session.query(Author).delete()
        db.session.commit()

        # 1. CREATE через шаблон Unit of Work (db.session.add + db.session.commit)
        print("\n--- 1. CREATE (Unit of Work: db.session.add -> db.session.commit) ---")
        author1 = Author(
            first_name="Іван",
            last_name="Франко",
            email="ivan.franko@library.ua",
        )
        profile1 = AuthorProfile(
            author=author1,
            biography="Український письменник, поет, вчений і громадський діяч.",
            country="Україна",
            awards_count=10,
        )
        author2 = Author(
            first_name="Леся",
            last_name="Українка",
            email="lesya.ukrainka@library.ua",
        )
        profile2 = AuthorProfile(
            author=author2,
            biography="Видатна українська письменниця, поетеса та драматургиня.",
            country="Україна",
            awards_count=9,
        )

        g_drama = Genre(name="Драма-феєрія", slug="drama", is_featured=True)
        g_classic = Genre(name="Класична проза", slug="classic-prose", is_featured=True)

        book1 = Book(
            title="Захар Беркут",
            isbn="9789660381129",
            status="available",
            price=275.0,
            pages=256,
            published_year=2022,
            author=author1,
        )
        book1.genres.append(g_classic)

        book2 = Book(
            title="Лісова пісня",
            isbn="9789660385448",
            status="available",
            price=310.0,
            pages=192,
            published_year=2023,
            author=author2,
        )
        book2.genres.append(g_drama)

        db.session.add_all([author1, profile1, author2, profile2, g_drama, g_classic, book1, book2])
        db.session.commit()
        print(
            f"Зафіксовано в БД: авторів={db.session.query(Author).count()}, "
            f"книг={db.session.query(Book).count()}, жанрів={db.session.query(Genre).count()}"
        )

        # 2. READ: вибірки filter_by, filter з or_, агрегація func.count / func.avg та joinedload
        print("\n--- 2. READ: Вибірки, агрегація та eager loading (joinedload) ---")
        available = db.session.query(Book).filter_by(status="available").all()
        print(f"[filter_by] Доступні книги: {[b.title for b in available]}")

        complex_filter = (
            db.session.query(Book)
            .filter(or_(Book.price >= 300.0, Book.pages >= 250))
            .all()
        )
        print(f"[filter + or_] Книги з ціною >= 300 АБО сторінками >= 250: {[b.title for b in complex_filter]}")

        total_count, avg_price = (
            db.session.query(func.count(Book.id), func.avg(Book.price)).one()
        )
        print(f"[func.count / func.avg] Всього книг: {total_count}, середня ціна: {avg_price:.2f} грн")

        eager_books = db.session.query(Book).options(joinedload(Book.author)).all()
        print(
            f"[joinedload] Книги з попередньо завантаженими авторами: "
            f"{[f'{b.title} — {b.author}' for b in eager_books]}"
        )

        # 3. UPDATE
        print("\n--- 3. UPDATE: Модифікація атрибута об'єкта у сесії ---")
        book1.price = 295.0
        db.session.commit()
        print(f"Оновлена ціна книги «{book1.title}»: {book1.price} грн")

        # 4. СЦЕНАРІЙ ТРАНЗАКЦІЙНОЇ АТОМАРНОСТІ (rollback при помилці)
        print("\n--- 4. ТРАНЗАКЦІЙНА АТОМАРНІСТЬ: Відкат (rollback) при порушенні цілісності ---")
        books_before = db.session.query(Book).count()
        print(f"Кількість книг до транзакції: {books_before}")
        try:
            valid_new_book = Book(
                title="Перехресні стежки",
                isbn="9789660390015",
                status="available",
                price=280.0,
                pages=320,
                published_year=2024,
                author_id=author1.id,
            )
            duplicate_isbn_book = Book(
                title="Дублікат ISBN (спричинить помилку)",
                isbn="9789660381129",  # такий самий ISBN, як у «Захар Беркут»
                status="available",
                price=200.0,
                pages=150,
                published_year=2024,
                author_id=author1.id,
            )
            db.session.add(valid_new_book)
            db.session.add(duplicate_isbn_book)
            db.session.commit()
        except IntegrityError as exc:
            db.session.rollback()
            print(f"Перехоплено IntegrityError! Виконано db.session.rollback(). Деталі: дублікат UNIQUE поля isbn.")

        books_after = db.session.query(Book).count()
        print(
            f"Кількість книг після rollback: {books_after} "
            f"(валідна книга з тієї ж транзакції також була скасована — атомарність збережено!)"
        )

        # 5. DELETE
        print("\n--- 5. DELETE: Видалення запису через db.session.delete ---")
        db.session.delete(book2)
        db.session.commit()
        print(f"Після видалення «Лісова пісня» у БД залишилося книг: {db.session.query(Book).count()}")


if __name__ == "__main__":
    run_flask_orm_demo()
