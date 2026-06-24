"""
Django settings for yoga_shop project.
Лабораторная работа №23 — настройки для деплоя на Railway.

Все чувствительные значения читаются из переменных окружения.
Для локальной разработки создайте файл .env в корне проекта (см. .env.example).
"""

import os
from pathlib import Path

import dj_database_url
from dotenv import load_dotenv

# Загружаем .env файл при локальной разработке.
# На Railway переменные окружения задаются в интерфейсе платформы
# и load_dotenv() их не перезаписывает.
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

BASE_DIR = Path(__file__).resolve().parent.parent

# ─────────────────────────── БЕЗОПАСНОСТЬ ────────────────────────────
# SECRET_KEY обязательно задаётся через переменную окружения.
# Значение по умолчанию — только для первоначального запуска локально.
SECRET_KEY = os.environ.get(
    "DJANGO_SECRET_KEY",
    "django-insecure-dev-only-CHANGE-ME-before-deploy",
)

# На Railway задайте переменную DJANGO_DEBUG=False.
# При отсутствии переменной (локальная разработка) DEBUG=True.
DEBUG = os.environ.get("DJANGO_DEBUG", "True") == "True"

# Локально: пустой список (Django сам разрешает localhost).
# На Railway: Railway-домен задаётся через переменную RAILWAY_PUBLIC_DOMAIN
# (устанавливается платформой автоматически) или ручной ALLOWED_HOSTS.
RAILWAY_DOMAIN = os.environ.get("RAILWAY_PUBLIC_DOMAIN", "")
_allowed = os.environ.get("ALLOWED_HOSTS", "127.0.0.1,localhost")
ALLOWED_HOSTS = [h.strip() for h in _allowed.split(",") if h.strip()]
if RAILWAY_DOMAIN and RAILWAY_DOMAIN not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append(RAILWAY_DOMAIN)

# На Railway CSRF_TRUSTED_ORIGINS должен включать публичный домен.
CSRF_TRUSTED_ORIGINS = []
if RAILWAY_DOMAIN:
    CSRF_TRUSTED_ORIGINS.append(f"https://{RAILWAY_DOMAIN}")
# Дополнительные origins из переменной окружения (через запятую):
_extra_origins = os.environ.get("CSRF_TRUSTED_ORIGINS", "")
if _extra_origins:
    CSRF_TRUSTED_ORIGINS += [o.strip() for o in _extra_origins.split(",") if o.strip()]

# ──────────────── СЕССИИ И КУКИ (продакшн-режим) ─────────────────────
# SESSION_COOKIE_SECURE=True требует HTTPS — безопасно на Railway,
# но ломает вход по http://localhost → поэтому только при DEBUG=False.
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG

# Редирект HTTP → HTTPS и HSTS (только в продакшне).
# Railway всегда работает по HTTPS, поэтому эти настройки безопасны.
# На localhost они будут False и не нарушат разработку.
SECURE_SSL_REDIRECT = not DEBUG
SECURE_HSTS_SECONDS = 0 if DEBUG else 31536000  # 1 год в продакшне
SECURE_HSTS_INCLUDE_SUBDOMAINS = not DEBUG
SECURE_HSTS_PRELOAD = not DEBUG


# ─────────────────────────── ПРИЛОЖЕНИЯ ──────────────────────────────
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "shop",
]

# ─────────────────────────── MIDDLEWARE ──────────────────────────────
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    # WhiteNoise идёт сразу после SecurityMiddleware — раздаёт статику
    # в продакшне без отдельного Nginx/CDN. (лр23)
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "yoga_shop.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "yoga_shop.wsgi.application"


# ──────────────────────────── БАЗА ДАННЫХ ────────────────────────────
# На Railway переменная DATABASE_URL задаётся автоматически при добавлении
# PostgreSQL-сервиса. Локально — используется SQLite по умолчанию.
_database_url = os.environ.get("DATABASE_URL", "")

if _database_url:
    # Продакшн (Railway + PostgreSQL)
    DATABASES = {
        "default": dj_database_url.config(
            default=_database_url,
            conn_max_age=600,
        )
    }
else:
    # Локальная разработка (SQLite)
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }


# ─────────────────────── ВАЛИДАЦИЯ ПАРОЛЕЙ ───────────────────────────
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]


# ────────────────────────── ЛОКАЛИЗАЦИЯ ──────────────────────────────
LANGUAGE_CODE = "ru"
TIME_ZONE = "Europe/Minsk"
USE_I18N = True
USE_TZ = True


# ───────────────────────── СТАТИЧЕСКИЕ ФАЙЛЫ ─────────────────────────
STATIC_URL = "/static/"

STATICFILES_DIRS = [
    BASE_DIR / "static",
]

# Директория для collectstatic — Railway/Gunicorn читает файлы отсюда.
STATIC_ROOT = BASE_DIR / "staticfiles"

# WhiteNoise: сжатие + кэш-заголовки для статики в продакшне. (лр23)
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

# Медиафайлы (фото товаров)
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"


# ───────────────────────── PRIMARY KEY ───────────────────────────────
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# ─────────────────────── АУТЕНТИФИКАЦИЯ ──────────────────────────────
LOGIN_URL = "login"
LOGIN_REDIRECT_URL = "shop:cart_view"
LOGOUT_REDIRECT_URL = "shop:home"
PASSWORD_CHANGE_REDIRECT_URL = "password_change_done"


# ─────────────────────────────── EMAIL ───────────────────────────────
# Параметры SMTP задаются через переменные окружения.
# Без них — письма выводятся в консоль (console backend).
EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD", "")

if EMAIL_HOST_USER and EMAIL_HOST_PASSWORD:
    EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
    EMAIL_HOST = "smtp.yandex.ru"
    EMAIL_PORT = 465
    EMAIL_USE_SSL = True
    EMAIL_USE_TLS = False
else:
    EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

DEFAULT_FROM_EMAIL = EMAIL_HOST_USER or "yoga-shop@example.com"


# ──────────────── DJANGO REST FRAMEWORK ──────────────────────────────
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
        "rest_framework.authentication.BasicAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 10,
}
