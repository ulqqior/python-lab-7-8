"""Пакет Flask-додатку онлайн-бібліотеки (Завдання 3, 4, 6, 7)."""
from .app import create_app, db, migrate

__all__ = ["create_app", "db", "migrate"]
