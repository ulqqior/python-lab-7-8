"""Представлення (views) додатку catalog (Завдання 6)."""
from decimal import Decimal
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render

from .models import Author, Book


def book_list_view(request: HttpRequest) -> HttpResponse:
    """Відображає каталог книг із фільтрацією за статусом та оптимізацією N+1."""
    status_filter = request.GET.get("status")
    queryset = Book.objects.select_related("author").prefetch_related("genres")
    if status_filter:
        queryset = queryset.filter(status=status_filter)
    return render(
        request,
        "catalog/book_list.html",
        {"books": queryset, "selected_status": status_filter},
    )


def book_detail_view(request: HttpRequest, pk: int) -> HttpResponse:
    """Відображає детальну сторінку книги або повертає 404, якщо книгу не знайдено."""
    book = get_object_or_404(
        Book.objects.select_related("author").prefetch_related("genres", "reviews"),
        pk=pk,
    )
    return render(request, "catalog/book_detail.html", {"book": book})


@login_required
def book_create_view(request: HttpRequest) -> HttpResponse:
    """
    Захищений маршрут створення книги (вимагає авторизації).
    Для неавторизованих користувачів повертає редірект 302 на LOGIN_URL.
    """
    if request.method == "POST":
        title = request.POST.get("title", "").strip()
        isbn = request.POST.get("isbn", "").strip()
        author_id = request.POST.get("author_id")
        price_raw = request.POST.get("price", "250.00")
        pages_raw = request.POST.get("pages", "150")
        published_year_raw = request.POST.get("published_year", "2024")

        if not title or not isbn or not author_id:
            return render(
                request,
                "catalog/book_form.html",
                {"error": "Усі обов'язкові поля мають бути заповнені."},
                status=400,
            )

        author = get_object_or_404(Author, pk=author_id)
        book = Book.objects.create(
            title=title,
            isbn=isbn,
            author=author,
            price=Decimal(price_raw),
            pages=int(pages_raw),
            published_year=int(published_year_raw),
        )
        return redirect("catalog:book_detail", pk=book.pk)

    authors = Author.objects.filter(is_active=True)
    return render(request, "catalog/book_form.html", {"authors": authors})


def catalog_stats_api_view(request: HttpRequest) -> JsonResponse:
    """JSON-ендпоінт зі зведеною статистикою бібліотечного каталогу."""
    from django.db.models import Avg, Count

    stats = Book.objects.aggregate(
        total_books=Count("id"),
        avg_price=Avg("price"),
    )
    return JsonResponse(
        {
            "total_books": stats["total_books"] or 0,
            "avg_price": float(stats["avg_price"] or 0.0),
        }
    )
