"""Реєстрація моделей каталогу в панелі адміністратора Django."""
from django.contrib import admin
from .models import Author, AuthorProfile, Book, BookReview, Genre

admin.site.register(Author)
admin.site.register(AuthorProfile)
admin.site.register(Genre)
admin.site.register(Book)
admin.site.register(BookReview)
