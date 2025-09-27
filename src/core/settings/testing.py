import os

from .base import *  # noqa: F403

DEBUG = False
TESTING = True


DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("TEST_DB_NAME", "test_db"),
        "USER": os.getenv("TEST_DB_USER", "test_user"),
        "PASSWORD": os.getenv("TEST_DB_PASSWORD", "test_password"),
        "HOST": os.getenv("TEST_DB_HOST", "test_db"),
        "PORT": os.getenv("TEST_DB_PORT", "5432"),
    }
}


class DisableMigrations:
    def __contains__(self, item):
        return True

    def __getitem__(self, item):
        return None


MIGRATION_MODULES = DisableMigrations()

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "unique-snowflake",
    }
}

CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

TELEGRAM_BOT_TOKEN = "test:token"
OPENAI_API_KEY = "test-key"

TELEGRAM_TEST_MODE = True
OPENAI_TEST_MODE = True

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "WARNING",
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
    },
}

PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]

TEMPLATES[0]["OPTIONS"]["debug"] = False  # noqa: F405
