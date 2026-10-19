"""WSGI-конфігурація для проєкту django_library."""
import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "django_library.settings")
application = get_wsgi_application()
