"""
Production settings for Haznex on Railway.
Set DJANGO_SETTINGS_MODULE=vhbridge.settings_production on the host.
"""

import os

import dj_database_url
from decouple import Csv

from .settings import *  # noqa: F403

DEBUG = False

# Railway sets RAILWAY_PUBLIC_DOMAIN automatically when a domain is generated.
_railway_domain = os.environ.get("RAILWAY_PUBLIC_DOMAIN", "").strip()
_default_allowed_hosts = "localhost,127.0.0.1"
if _railway_domain:
    _default_allowed_hosts = f"{_default_allowed_hosts},{_railway_domain}"

ALLOWED_HOSTS = config(  # noqa: F405
    "ALLOWED_HOSTS",
    default=_default_allowed_hosts,
    cast=Csv(),
)

SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

_csrf_default = f"https://{_railway_domain}" if _railway_domain else ""
CSRF_TRUSTED_ORIGINS = config(  # noqa: F405
    "CSRF_TRUSTED_ORIGINS",
    default=_csrf_default,
    cast=Csv(),
)

# Plain local static files for WhiteNoise (no manifest storage — breaks admin assets).
STATIC_ROOT = BASE_DIR / "staticfiles"  # noqa: F405
STORAGES = {  # noqa: F405
    **STORAGES,  # noqa: F405
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
        "OPTIONS": {
            "location": STATIC_ROOT,
            "base_url": STATIC_URL,  # noqa: F405
        },
    },
}

_database_url = config("DATABASE_URL", default="")  # noqa: F405
if _database_url:
    DATABASES["default"] = dj_database_url.config(  # noqa: F405
        default=_database_url,
        conn_max_age=600,
        conn_health_checks=True,
    )
else:
    raise ValueError(
        "DATABASE_URL is required in production. "
        "In Railway: open your web service → Variables → New Variable → "
        "Add Reference → select PostgreSQL → DATABASE_URL."
    )
