"""Django settings for local development and UAT deployments."""

import os
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
PROJECT_DIR = BASE_DIR.parent

# Local development can use a private .env file. Hosting-platform variables win.
load_dotenv(PROJECT_DIR / ".env")


def env_bool(name: str, default: bool = False) -> bool:
    """Read an explicit true/false environment setting."""
    raw_value = os.getenv(name)
    if raw_value is None:
        return default

    normalized = raw_value.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    raise ImproperlyConfigured(
        f"{name} must be true or false (received {raw_value!r})."
    )


def env_list(name: str, default: list[str] | None = None) -> list[str]:
    """Read a comma-separated environment setting and remove blank entries."""
    raw_value = os.getenv(name)
    if raw_value is None:
        return list(default or [])
    return [item.strip() for item in raw_value.split(",") if item.strip()]


MAILFORGE_UAT = env_bool("MAILFORGE_UAT", False)
DEBUG = env_bool("DJANGO_DEBUG", not MAILFORGE_UAT)
if MAILFORGE_UAT and DEBUG:
    raise ImproperlyConfigured(
        "DJANGO_DEBUG must be false when MAILFORGE_UAT=true."
    )

SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "").strip()
if not SECRET_KEY:
    if MAILFORGE_UAT:
        raise ImproperlyConfigured(
            "DJANGO_SECRET_KEY is required when MAILFORGE_UAT=true."
        )
    SECRET_KEY = "development-only-key"
if MAILFORGE_UAT and (
    SECRET_KEY == "development-only-key"
    or SECRET_KEY.startswith("replace-")
    or len(SECRET_KEY) < 50
):
    raise ImproperlyConfigured(
        "DJANGO_SECRET_KEY must be a unique random value of at least 50 characters in UAT."
    )

ALLOWED_HOSTS = env_list(
    "DJANGO_ALLOWED_HOSTS",
    ["localhost", "127.0.0.1"] if not MAILFORGE_UAT else [],
)
if MAILFORGE_UAT and not ALLOWED_HOSTS:
    raise ImproperlyConfigured(
        "DJANGO_ALLOWED_HOSTS is required when MAILFORGE_UAT=true."
    )

UAT_FRONTEND_URL = "https://mailforge.dev.acuvisor.com"
CORS_ALLOWED_ORIGINS = env_list(
    "DJANGO_CORS_ALLOWED_ORIGINS",
    [UAT_FRONTEND_URL]
    if MAILFORGE_UAT
    else ["http://localhost:8501", "http://127.0.0.1:8501"],
)
CSRF_TRUSTED_ORIGINS = env_list(
    "DJANGO_CSRF_TRUSTED_ORIGINS",
    [UAT_FRONTEND_URL] if MAILFORGE_UAT else [],
)

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "rest_framework.authtoken",
    "corsheaders",
    "accounts",
    "templates_api",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ]
        },
    }
]

database_path = Path(os.getenv("DJANGO_DATABASE_PATH", str(BASE_DIR / "db.sqlite3")))
if not database_path.is_absolute():
    database_path = PROJECT_DIR / database_path

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": database_path,
        "CONN_MAX_AGE": int(
            os.getenv("DJANGO_DB_CONN_MAX_AGE", "60" if MAILFORGE_UAT else "0")
        ),
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "Asia/Kolkata"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATIC_ROOT = PROJECT_DIR / "staticfiles"
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
EMAIL_TEMPLATE_ROOT = PROJECT_DIR / "email_templates"

# Keep these enabled when UAT is served over HTTPS.
SECURE_SSL_REDIRECT = env_bool("DJANGO_SECURE_SSL_REDIRECT", MAILFORGE_UAT)
SESSION_COOKIE_SECURE = env_bool("DJANGO_SESSION_COOKIE_SECURE", MAILFORGE_UAT)
CSRF_COOKIE_SECURE = env_bool("DJANGO_CSRF_COOKIE_SECURE", MAILFORGE_UAT)
SECURE_HSTS_SECONDS = int(
    os.getenv("DJANGO_SECURE_HSTS_SECONDS", "3600" if MAILFORGE_UAT else "0")
)
SECURE_HSTS_INCLUDE_SUBDOMAINS = env_bool(
    "DJANGO_SECURE_HSTS_INCLUDE_SUBDOMAINS", False
)
SECURE_HSTS_PRELOAD = env_bool("DJANGO_SECURE_HSTS_PRELOAD", False)
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"

if env_bool("DJANGO_TRUST_PROXY_HEADERS", False):
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.TokenAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon": os.getenv("DJANGO_LOGIN_THROTTLE_RATE", "30/minute"),
    },
}
