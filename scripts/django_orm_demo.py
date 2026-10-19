"""
Демонстрація можливостей Django ORM (Завдання 4):
- Повний цикл CRUD (Create, Read, Update, Delete)
- Три типи вибірок: filter(), exclude(), Q-об'єкти (OR / NOT) та F-об'єкти
- Агрегація (aggregate) та анотація (annotate)
- Зворотні зв'язки та оптимізація проблеми N+1 через select_related / prefetch_related
"""
from decimal import Decimal
import os
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "django_library.settings")

import django

django.setup()

from django.db import connection
from django.db.models import Avg, Count, F, Max, Min, Q, Sum
from django.test.utils import CaptureQueriesContext

from catalog.models import Author, AuthorProfile, Book, BookReview, Genre


def run_django_orm_demo() -> None:
    print("=" * 72)
    print("ДЕМОНСТРАЦІЯ ЗАПИТІВ DJANGO ORM (ЗАВДАННЯ 4)")
    print("=" * 72)

    # Очищення перед запуском для детермінованого результату
    BookReview.objects.all().delete()
    Book.objects.all().delete()
    AuthorProfile.objects.all().delete()
    Genre.objects.all().delete()
    Author.objects.all().delete()

    # 1. CREATE (Створення пов'язаних об'єктів)
    print("\n--- 1. CREATE: Створення авторів, профілів, жанрів, книг та відгуків ---")
    a1 = Author.objects.create(
        first_name="Ліна",
        last_name="Костенко",
        email="lina.kostenko@library.ua",
    )
    AuthorProfile.objects.create(
        author=a1,
        biography="Видатна українська поетеса-шістдесятниця та письменниця.",
        country="Україна",
        awards_count=12,
    )

    a2 = Author.objects.create(
        first_name="Сергій",
        last_name="Жадан",
        email="serhiy.zhadan@library.ua",
    )
    AuthorProfile.objects.create(
        author=a2,
        biography="Сучасний український письменник, перекладач і громадський діяч.",
        country="Україна",
        awards_count=8,
    )

    g_poetry = Genre.objects.create(
        name="Поезія", slug="poetry", description="Ліричні та епічні поетичні твори", is_featured=True
    )
    g_history = Genre.objects.create(
        name="Історичний роман", slug="historical-novel", description="Твори на історичну тематику", is_featured=True
    )
    g_modern = Genre.objects.create(
        name="Сучасна проза", slug="modern-prose", description="Сучасна художня проза", is_featured=False
    )

    b1 = Book.objects.create(
        title="Маруся Чурай",
        isbn="9789660372011",
        status=Book.STATUS_AVAILABLE,
        price=Decimal("320.00"),
        pages=224,
        published_year=2021,
        language="Українська",
        author=a1,
    )
    b1.genres.add(g_poetry, g_history)

    b2 = Book.objects.create(
        title="Записки українського самашедшого",
        isbn="9789667047887",
        status=Book.STATUS_BORROWED,
        price=Decimal("380.00"),
        pages=416,
        published_year=2020,
        language="Українська",
        author=a1,
    )
    b2.genres.add(g_modern)

    b3 = Book.objects.create(
        title="Інтернат",
        isbn="9786176794387",
        status=Book.STATUS_AVAILABLE,
        price=Decimal("290.00"),
        pages=336,
        published_year=2023,
        language="Українська",
        author=a2,
        recommended_by=a1,
    )
    b3.genres.add(g_modern)

    b4 = Book.objects.create(
        title="Ворошиловград",
        isbn="9789660359487",
        status=Book.STATUS_ARCHIVED,
        price=Decimal("240.00"),
        pages=442,
        published_year=2018,
        language="Українська",
        author=a2,
    )
    b4.genres.add(g_modern)

    BookReview.objects.create(
        book=b1, reviewer_name="Олена Бондар", rating=5, comment="Шедевр української літератури!"
    )
    BookReview.objects.create(
        book=b3, reviewer_name="Ігор Мельник", rating=5, comment="Надзвичайно сильний роман."
    )

    print(f"Створено авторів: {Author.objects.count()}, книг: {Book.objects.count()}, жанрів: {Genre.objects.count()}")

    # 2. READ та 3 ТИПИ ВИБІРОК (filter, exclude, Q-об'єкти)
    print("\n--- 2. READ: Три типи вибірок (filter, exclude, Q-об'єкти) ---")
    available_books = Book.objects.filter(status=Book.STATUS_AVAILABLE, price__lte=Decimal("350.00"))
    print(f"[2.1 filter()] Доступні книги ціною <= 350 грн: {[b.title for b in available_books]}")

    non_archived = Book.objects.exclude(status=Book.STATUS_ARCHIVED)
    print(f"[2.2 exclude()] Книги не в архіві: {[b.title for b in non_archived]}")

    q_books = Book.objects.filter(
        (Q(published_year__gte=2022) | Q(pages__gt=400)) & ~Q(status=Book.STATUS_ARCHIVED)
    )
    print(
        f"[2.3 Q-objects (OR + NOT)] Книги (рік >= 2022 АБО сторінок > 400) І НЕ архівні: "
        f"{[f'{b.title} ({b.published_year}, {b.pages} стор.)' for b in q_books]}"
    )

    # 3. UPDATE (Оновлення через save() та F-об'єкти)
    print("\n--- 3. UPDATE: Оновлення записів та використання F-об'єктів ---")
    Book.objects.filter(status=Book.STATUS_AVAILABLE).update(price=F("price") + Decimal("15.00"))
    b1.refresh_from_db()
    print(f"Нова ціна «{b1.title}» після індексації через F('price') + 15: {b1.price} грн")

    # 4. AGGREGATE та ANNOTATE
    print("\n--- 4. АГРЕГАЦІЯ (aggregate) ТА АНОТАЦІЯ (annotate) ---")
    summary_stats = Book.objects.aggregate(
        total_books=Count("id"),
        avg_price=Avg("price"),
        min_price=Min("price"),
        max_price=Max("price"),
        total_pages=Sum("pages"),
    )
    print(f"Зведена статистика каталогу (aggregate): {summary_stats}")

    annotated_authors = Author.objects.annotate(
        books_count=Count("books"),
        avg_book_price=Avg("books__price"),
    )
    for author in annotated_authors:
        print(
            f"Автор (annotate): {author} -> книг: {author.books_count}, "
            f"середня ціна: {author.avg_book_price:.2f} грн"
        )

    # 5. ЗВОРОТНІ ЗВ'ЯЗКИ ТА ОПТИМІЗАЦІЯ N+1 (select_related / prefetch_related)
    print("\n--- 5. ЗВОРОТНІ ЗВ'ЯЗКИ ТА ОПТИМІЗАЦІЯ N+1 (select_related / prefetch_related) ---")
    print(f"Книги автора {a1} через зворотний зв'язок a1.books.all(): {[b.title for b in a1.books.all()]}")
    print(f"Книги жанру «{g_modern}» через g_modern.books.all(): {[b.title for b in g_modern.books.all()]}")

    with CaptureQueriesContext(connection) as unoptimized_ctx:
        for book in Book.objects.all():
            _ = book.author.last_name
            _ = [g.name for g in book.genres.all()]
    print(f"Кількість SQL-запитів БЕЗ оптимізації (проблема N+1): {len(unoptimized_ctx)}")

    with CaptureQueriesContext(connection) as optimized_ctx:
        for book in Book.objects.select_related("author").prefetch_related("genres"):
            _ = book.author.last_name
            _ = [g.name for g in book.genres.all()]
    print(
        f"Кількість SQL-запитів ІЗ select_related('author').prefetch_related('genres'): "
        f"{len(optimized_ctx)} (1 JOIN-запит для книг та авторів + 1 запит для жанрів)"
    )

    # 6. DELETE (Видалення запису)
    print("\n--- 6. DELETE: Видалення архівної книги ---")
    deleted_count, deleted_details = b4.delete()
    print(f"Видалено об'єктів: {deleted_count} ({deleted_details}). Залишилося книг: {Book.objects.count()}")


if __name__ == "__main__":
    run_django_orm_demo()
