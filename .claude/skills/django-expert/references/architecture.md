# Django Architecture Patterns

## Recommended Project Layout

```
project_root/
├── config/                  # Project configuration
│   ├── __init__.py
│   ├── settings/
│   │   ├── __init__.py
│   │   ├── base.py          # Shared settings
│   │   ├── development.py   # Dev overrides
│   │   ├── production.py    # Prod overrides
│   │   └── testing.py       # Test overrides
│   ├── urls.py              # Root URL configuration
│   ├── wsgi.py
│   └── asgi.py
├── apps/                    # All Django apps
│   ├── accounts/
│   │   ├── __init__.py
│   │   ├── admin.py
│   │   ├── apps.py
│   │   ├── models.py
│   │   ├── services.py      # Business logic
│   │   ├── selectors.py     # Read-only queries
│   │   ├── urls.py
│   │   ├── views.py
│   │   ├── serializers.py
│   │   ├── permissions.py
│   │   ├── signals.py
│   │   ├── tasks.py         # Celery tasks
│   │   └── tests/
│   │       ├── __init__.py
│   │       ├── test_models.py
│   │       ├── test_services.py
│   │       ├── test_views.py
│   │       └── test_serializers.py
│   ├── orders/
│   │   └── ...
│   └── products/
│       └── ...
├── common/                  # Shared utilities
│   ├── __init__.py
│   ├── models.py            # Abstract base models
│   ├── permissions.py       # Shared permissions
│   ├── pagination.py        # Custom pagination
│   └── exceptions.py        # Custom exceptions
├── templates/
├── static/
├── media/
├── requirements/
│   ├── base.txt
│   ├── development.txt
│   └── production.txt
├── manage.py
├── pytest.ini
└── Makefile
```

## Split Settings Pattern

### base.py — Shared Settings

```python
"""Base settings shared across all environments."""

import os
from pathlib import Path

import environ

env = environ.Env()

BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Read .env file if it exists
environ.Env.read_env(os.path.join(BASE_DIR, ".env"))

SECRET_KEY = env("DJANGO_SECRET_KEY")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Third-party
    "rest_framework",
    "django_filters",
    "corsheaders",
    # Local apps
    "apps.accounts",
    "apps.orders",
    "apps.products",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

DATABASES = {
    "default": env.db("DATABASE_URL", default="sqlite:///db.sqlite3"),
}

AUTH_USER_MODEL = "accounts.User"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
        "rest_framework.authentication.TokenAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ],
}

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
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

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"
```

### development.py — Development Overrides

```python
"""Development-specific settings. Never use in production."""

from .base import *  # noqa: F401,F403
from .base import env

DEBUG = True

ALLOWED_HOSTS = ["localhost", "127.0.0.1", "0.0.0.0"]

# Django Debug Toolbar
INSTALLED_APPS += ["debug_toolbar"]  # noqa: F405
MIDDLEWARE.insert(0, "debug_toolbar.middleware.DebugToolbarMiddleware")  # noqa: F405
INTERNAL_IPS = ["127.0.0.1"]

# Email backend — print to console
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# CORS — allow all in dev
CORS_ALLOW_ALL_ORIGINS = True

# Cache — local memory
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
    }
}

# Logging — verbose
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
        "level": "DEBUG",
    },
    "loggers": {
        "django.db.backends": {
            "level": env("DJANGO_DB_LOG_LEVEL", default="WARNING"),
            "handlers": ["console"],
            "propagate": False,
        },
    },
}
```

### production.py — Production Settings

```python
"""Production settings. Security-hardened, performance-optimized."""

from .base import *  # noqa: F401,F403
from .base import env

DEBUG = False

ALLOWED_HOSTS = env.list("DJANGO_ALLOWED_HOSTS")

# Security
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = "DENY"

# CORS — explicit origins only
CORS_ALLOWED_ORIGINS = env.list("CORS_ALLOWED_ORIGINS", default=[])

# Cache — Redis
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": env("REDIS_URL", default="redis://127.0.0.1:6379/1"),
    }
}

# Email — SMTP
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = env("EMAIL_HOST")
EMAIL_PORT = env.int("EMAIL_PORT", default=587)
EMAIL_USE_TLS = True
EMAIL_HOST_USER = env("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD")

# Static files — whitenoise
MIDDLEWARE.insert(1, "whitenoise.middleware.WhiteNoiseMiddleware")  # noqa: F405
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# Logging
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "json": {
            "()": "pythonjsonlogger.jsonlogger.JsonFormatter",
            "format": "%(asctime)s %(name)s %(levelname)s %(message)s",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "json",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "WARNING",
    },
    "loggers": {
        "django.security": {
            "level": "WARNING",
            "handlers": ["console"],
            "propagate": False,
        },
    },
}
```

## Service Layer Pattern

Business logic belongs in services, not views or models. Views handle HTTP; models handle persistence; services handle logic.

```python
"""Order processing service. Coordinates business logic for order creation,
payment, inventory, and notifications."""

from decimal import Decimal

from django.db import transaction
from django.core.exceptions import ValidationError

from apps.orders.models import Order, OrderItem
from apps.products.models import Product
from apps.notifications.services import NotificationService


class OrderService:
    """Handles order creation, payment processing, and fulfillment logic."""

    def __init__(self, notification_service: NotificationService | None = None) -> None:
        self._notification_service = notification_service or NotificationService()

    @transaction.atomic
    def create_order(
        self,
        user,
        items: list[dict],
        shipping_address: str,
    ) -> Order:
        """Create an order with validation, stock reservation, and notification.

        Args:
            user: The user placing the order.
            items: List of dicts with 'product_id' and 'quantity'.
            shipping_address: Delivery address string.

        Returns:
            The created Order instance.

        Raises:
            ValidationError: If cart is empty or stock is insufficient.
        """
        if not items:
            raise ValidationError("Cannot create an order with no items.")

        total = Decimal("0.00")
        order = Order.objects.create(
            user=user,
            shipping_address=shipping_address,
            status=Order.Status.PENDING,
        )

        for item_data in items:
            product = Product.objects.select_for_update().get(
                id=item_data["product_id"]
            )
            quantity = item_data["quantity"]

            if product.stock < quantity:
                raise ValidationError(
                    f"Insufficient stock for {product.name}. "
                    f"Available: {product.stock}, requested: {quantity}."
                )

            product.stock -= quantity
            product.save(update_fields=["stock"])

            line_total = product.price * quantity
            OrderItem.objects.create(
                order=order,
                product=product,
                quantity=quantity,
                unit_price=product.price,
                line_total=line_total,
            )
            total += line_total

        order.total = total
        order.save(update_fields=["total"])

        self._notification_service.send_order_confirmation(order)

        return order

    @transaction.atomic
    def cancel_order(self, order: Order) -> Order:
        """Cancel an order and restore stock.

        Args:
            order: The order to cancel.

        Returns:
            The updated Order instance.

        Raises:
            ValidationError: If order is already shipped or delivered.
        """
        if order.status in (Order.Status.SHIPPED, Order.Status.DELIVERED):
            raise ValidationError(
                f"Cannot cancel order in '{order.status}' status."
            )

        for item in order.items.select_related("product"):
            product = Product.objects.select_for_update().get(id=item.product_id)
            product.stock += item.quantity
            product.save(update_fields=["stock"])

        order.status = Order.Status.CANCELLED
        order.save(update_fields=["status"])

        self._notification_service.send_order_cancellation(order)

        return order
```

### Using the Service in a View

```python
"""Order views — thin wrappers around OrderService."""

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.orders.serializers import OrderCreateSerializer, OrderDetailSerializer
from apps.orders.services import OrderService


class OrderCreateView(APIView):
    """Create a new order. Delegates all logic to OrderService."""

    def post(self, request):
        serializer = OrderCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        service = OrderService()
        order = service.create_order(
            user=request.user,
            items=serializer.validated_data["items"],
            shipping_address=serializer.validated_data["shipping_address"],
        )

        return Response(
            OrderDetailSerializer(order).data,
            status=status.HTTP_201_CREATED,
        )
```

## Custom Middleware

```python
"""Request timing and correlation ID middleware."""

import time
import uuid
import logging

logger = logging.getLogger(__name__)


class RequestTimingMiddleware:
    """Log the wall-clock time of every request."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start = time.monotonic()
        response = self.get_response(request)
        duration_ms = (time.monotonic() - start) * 1000

        logger.info(
            "Request completed",
            extra={
                "method": request.method,
                "path": request.path,
                "status": response.status_code,
                "duration_ms": round(duration_ms, 2),
            },
        )

        response["X-Request-Duration-Ms"] = str(round(duration_ms, 2))
        return response


class CorrelationIdMiddleware:
    """Attach a unique correlation ID to each request for tracing."""

    HEADER = "X-Correlation-ID"

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        correlation_id = request.headers.get(self.HEADER, str(uuid.uuid4()))
        request.correlation_id = correlation_id

        response = self.get_response(request)
        response[self.HEADER] = correlation_id
        return response
```

## Signals Pattern

Signals decouple side effects from model logic. Register them in `apps.py` via `ready()`.

### signals.py

```python
"""Post-save signals for the accounts app."""

from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.accounts.models import UserProfile


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_user_profile(sender, instance, created, **kwargs):
    """Create a UserProfile automatically when a new User is created."""
    if created:
        UserProfile.objects.create(user=instance)


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def save_user_profile(sender, instance, **kwargs):
    """Persist profile changes when the User is saved."""
    if hasattr(instance, "profile"):
        instance.profile.save()
```

### apps.py — Register Signals

```python
"""Accounts app configuration. Imports signals on ready()."""

from django.apps import AppConfig


class AccountsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.accounts"

    def ready(self):
        import apps.accounts.signals  # noqa: F401
```
