"""Маршрути додатку catalog."""
from django.urls import path
from . import views

app_name = "catalog"

urlpatterns = [
    path("books/", views.book_list_view, name="book_list"),
    path("books/<int:pk>/", views.book_detail_view, name="book_detail"),
    path("books/create/", views.book_create_view, name="book_create"),
    path("api/stats/", views.catalog_stats_api_view, name="catalog_stats"),
]
