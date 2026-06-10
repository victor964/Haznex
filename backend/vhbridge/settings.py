"""
Django settings for vhbridge project.
"""

from pathlib import Path

from decouple import AutoConfig, Csv

# backend/ — Django apps and manage.py live here
BASE_DIR = Path(__file__).resolve().parent.parent
# d:\vhbridge\ — .env and requirements.txt live at repo root
PROJECT_ROOT = BASE_DIR.parent

config = AutoConfig(search_path=PROJECT_ROOT)

SECRET_KEY = config("SECRET_KEY", default="django-insecure-dev-only-change-me")
DEBUG = config("DEBUG", default=True, cast=bool)
ALLOWED_HOSTS = config("ALLOWED_HOSTS", default="localhost,127.0.0.1", cast=Csv())

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "cloudinary_storage",
    "django.contrib.staticfiles",
    "cloudinary",
    "rest_framework",
    "corsheaders",
    "store.apps.StoreConfig",
    "orders.apps.OrdersConfig",
    "accounts.apps.AccountsConfig",
    "admin_panel.apps.AdminPanelConfig",
    "payments.apps.PaymentsConfig",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "vhbridge.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [PROJECT_ROOT / "templates", PROJECT_ROOT / "frontend"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "vhbridge.context_processors.site_settings",
                "store.context_processors.whatsapp",
            ],
        },
    },
]

WSGI_APPLICATION = "vhbridge.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": config("DB_NAME", default="vhbridge"),
        "USER": config("DB_USER", default="postgres"),
        "PASSWORD": config("DB_PASSWORD", default=""),
        "HOST": config("DB_HOST", default="localhost"),
        "PORT": config("DB_PORT", default="5432"),
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "Africa/Nairobi"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

STORAGES = {
    "default": {
        "BACKEND": "cloudinary_storage.storage.MediaCloudinaryStorage",
    },
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
        "OPTIONS": {
            "location": STATIC_ROOT,
            "base_url": STATIC_URL,
        },
    },
}

# GBP → KES rate for product price calculator (all fee fields entered in GBP).
GBP_TO_KES_RATE = config("GBP_TO_KES_RATE", default="165.00", cast=str)

CLOUDINARY_STORAGE = {
    "CLOUD_NAME": config("CLOUDINARY_CLOUD_NAME", default=""),
    "API_KEY": config("CLOUDINARY_API_KEY", default=""),
    "API_SECRET": config("CLOUDINARY_API_SECRET", default=""),
}

# Ensure the Cloudinary SDK is configured (CloudinaryField uploads need this).
# django-cloudinary-storage only calls cloudinary.config() when its app_settings
# module is imported, which may happen after the first upload attempt.
import cloudinary

cloudinary.config(
    cloud_name=CLOUDINARY_STORAGE["CLOUD_NAME"],
    api_key=CLOUDINARY_STORAGE["API_KEY"],
    api_secret=CLOUDINARY_STORAGE["API_SECRET"],
    secure=True,
)

if not all(
    (
        CLOUDINARY_STORAGE["CLOUD_NAME"],
        CLOUDINARY_STORAGE["API_KEY"],
        CLOUDINARY_STORAGE["API_SECRET"],
    )
):
    import warnings

    warnings.warn(
        "Cloudinary credentials are missing in .env. "
        "Set CLOUDINARY_CLOUD_NAME, CLOUDINARY_API_KEY, and CLOUDINARY_API_SECRET.",
        stacklevel=1,
    )

CORS_ALLOWED_ORIGINS = config(
    "CORS_ALLOWED_ORIGINS",
    default="http://localhost:3000,http://127.0.0.1:3000",
    cast=Csv(),
)
CORS_ALLOW_CREDENTIALS = True

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# M-Pesa Daraja API (https://developer.safaricom.co.ke)
MPESA_ENVIRONMENT = config("MPESA_ENVIRONMENT", default="sandbox")
MPESA_CONSUMER_KEY = config("MPESA_CONSUMER_KEY", default="")
MPESA_CONSUMER_SECRET = config("MPESA_CONSUMER_SECRET", default="")
MPESA_SHORTCODE = config("MPESA_SHORTCODE", default="174379")
MPESA_PASSKEY = config(
    "MPESA_PASSKEY",
    default="bfb279f9aa9bdbcf158e97dd71a467cd2e0c893059b10f78e6b72ada1ed2c919",
)
MPESA_CALLBACK_URL = config(
    "MPESA_CALLBACK_URL",
    default="https://placeholder.ngrok.io/payments/callback/",
)
MPESA_STK_ENABLED = config("MPESA_STK_ENABLED", default=False, cast=bool)

# Gmail SMTP — Django built-in email (App Password, not account password)
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = config("EMAIL_HOST", default="smtp.gmail.com")
EMAIL_PORT = config("EMAIL_PORT", default=587, cast=int)
EMAIL_USE_TLS = config("EMAIL_USE_TLS", default=True, cast=bool)
EMAIL_HOST_USER = config("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = config("EMAIL_HOST_PASSWORD", default="")
DEFAULT_FROM_EMAIL = config(
    "DEFAULT_FROM_EMAIL",
    default="Haznex <noreply@haznex.com>",
)
EMAIL_NOTIFICATIONS_ENABLED = config(
    "EMAIL_NOTIFICATIONS_ENABLED",
    default=False,
    cast=bool,
)
# Absolute URLs in notification emails (signals have no HTTP request)
SITE_URL = config("SITE_URL", default="http://127.0.0.1:8000")

# WhatsApp chat button (international format, no + prefix)
WHATSAPP_NUMBER = config("WHATSAPP_NUMBER", default="")

LOGIN_URL = "/haznex-admin/login/"
LOGIN_REDIRECT_URL = "/haznex-admin/dashboard/"
LOGOUT_REDIRECT_URL = "/haznex-admin/login/"
