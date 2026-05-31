"""
Production settings for Haznex on Railway.
Set DJANGO_SETTINGS_MODULE=vhbridge.settings_production on the host.
"""

import dj_database_url
from decouple import Csv

from .settings import *  # noqa: F403

DEBUG = False

ALLOWED_HOSTS = config("ALLOWED_HOSTS", cast=Csv())  # noqa: F405

SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

CSRF_TRUSTED_ORIGINS = config(  # noqa: F405
    "CSRF_TRUSTED_ORIGINS",
    default="",
    cast=Csv(),
)

# Plain storage — Manifest/compressed storage fails on Django admin assets during collectstatic.
STATICFILES_STORAGE = "django.contrib.staticfiles.storage.StaticFilesStorage"
STATIC_ROOT = BASE_DIR / "staticfiles"  # noqa: F405

DATABASES["default"] = dj_database_url.config(  # noqa: F405
    default=config("DATABASE_URL", default=""),  # noqa: F405
    conn_max_age=600,
    conn_health_checks=True,
)

if not DATABASES["default"]:  # noqa: F405
    raise ValueError(
        "DATABASE_URL is required in production. "
        "Link Railway PostgreSQL or set DATABASE_URL explicitly."
    )
