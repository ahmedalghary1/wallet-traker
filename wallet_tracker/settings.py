import os
from pathlib import Path

from .desktop_paths import app_data_dir, ensure_child_dir, is_desktop_mode, resource_root


BASE_DIR = Path(__file__).resolve().parent.parent
RESOURCE_DIR = resource_root()
DESKTOP_LOCAL_MODE = is_desktop_mode()
DATA_DIR = app_data_dir() if DESKTOP_LOCAL_MODE else BASE_DIR

SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "dev-wallet-tracker-change-me")
DEBUG = os.getenv("DJANGO_DEBUG", "0" if DESKTOP_LOCAL_MODE else "1").lower() in {
    "1",
    "true",
    "yes",
    "on",
}

default_hosts = "127.0.0.1,localhost,testserver"
ALLOWED_HOSTS = [
    host.strip()
    for host in os.getenv("DJANGO_ALLOWED_HOSTS", default_hosts).split(",")
    if host.strip()
]

INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "core",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "wallet_tracker.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [RESOURCE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.messages.context_processors.messages",
                "core.context_processors.system_settings",
            ],
        },
    },
]

WSGI_APPLICATION = "wallet_tracker.wsgi.application"


DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": Path(os.getenv("WALLET_TRACKER_DB_PATH", DATA_DIR / "db.sqlite3")),
    }
}


AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


LANGUAGE_CODE = "ar"
TIME_ZONE = "Africa/Cairo"
USE_I18N = True
USE_TZ = True


STATIC_URL = "static/"
STATICFILES_DIRS = [RESOURCE_DIR / "static"]
STATIC_ROOT = DATA_DIR / "staticfiles"

MEDIA_URL = "media/"
MEDIA_ROOT = DATA_DIR / "media"

if DESKTOP_LOCAL_MODE:
    ensure_child_dir(DATA_DIR, "media")
    ensure_child_dir(DATA_DIR, "logs")

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

if DESKTOP_LOCAL_MODE:
    LOGGING = {
        "version": 1,
        "disable_existing_loggers": False,
        "handlers": {
            "file": {
                "level": "INFO",
                "class": "logging.FileHandler",
                "filename": DATA_DIR / "logs" / "wallet_tracker.log",
                "encoding": "utf-8",
            }
        },
        "loggers": {
            "django": {
                "handlers": ["file"],
                "level": "INFO",
                "propagate": True,
            },
            "core": {
                "handlers": ["file"],
                "level": "INFO",
                "propagate": True,
            },
        },
    }
