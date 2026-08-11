# Django Security

## Production Settings Configuration

```python
"""Production security settings — apply all of these in production."""

# --- HTTPS & Transport Security ---
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31536000          # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# --- Cookie Security ---
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
SESSION_COOKIE_AGE = 1209600            # 2 weeks
CSRF_COOKIE_SECURE = True
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = "Lax"

# --- Content Security ---
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = "DENY"
SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"

# --- Host Validation ---
ALLOWED_HOSTS = env.list("DJANGO_ALLOWED_HOSTS")
CSRF_TRUSTED_ORIGINS = env.list("CSRF_TRUSTED_ORIGINS", default=[])

# --- Debug ---
DEBUG = False
```

## Custom User Model

Always use a custom User model from day one. Migrating later is extremely painful.

```python
"""Custom user model with email as the login identifier."""

from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models


class UserManager(BaseUserManager):
    """Manager for custom User model using email instead of username."""

    def create_user(
        self, email: str, password: str | None = None, **extra_fields
    ) -> "User":
        """Create and return a regular user.

        Args:
            email: User's email address (required).
            password: Plain-text password.
            **extra_fields: Additional model fields.

        Returns:
            Created User instance.

        Raises:
            ValueError: If email is not provided.
        """
        if not email:
            raise ValueError("Email is required.")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(
        self, email: str, password: str | None = None, **extra_fields
    ) -> "User":
        """Create and return a superuser.

        Args:
            email: Superuser's email address.
            password: Plain-text password.
            **extra_fields: Additional model fields.

        Returns:
            Created superuser User instance.
        """
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    """Custom user model using email as the unique identifier."""

    username = None
    email = models.EmailField(unique=True)
    is_email_verified = models.BooleanField(default=False)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = UserManager()

    def __str__(self) -> str:
        return self.email
```

In settings:

```python
AUTH_USER_MODEL = "accounts.User"
```

## Password Hashing — Argon2

```python
# settings.py
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.Argon2PasswordHasher",  # Primary
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher",
    "django.contrib.auth.hashers.BCryptSHA256PasswordHasher",
]
```

Install the backend:

```
pip install django[argon2]
```

## Session Management

```python
# settings.py

# Use database-backed sessions (default) or cache-backed for performance
SESSION_ENGINE = "django.contrib.sessions.backends.cached_db"

# Session timeout
SESSION_COOKIE_AGE = 1209600  # 2 weeks in seconds

# Expire session when browser closes
SESSION_EXPIRE_AT_BROWSER_CLOSE = False

# Rotate session key on login to prevent session fixation
# Django does this automatically with django.contrib.auth.login()

# Force logout after password change
# Django invalidates sessions automatically when password changes (Django 4.1+)
```

Middleware for idle timeout:

```python
"""Middleware that logs out users after a period of inactivity."""

import time

from django.conf import settings
from django.contrib.auth import logout


class SessionIdleTimeoutMiddleware:
    """Log out users who have been inactive for too long."""

    IDLE_TIMEOUT = getattr(settings, "SESSION_IDLE_TIMEOUT", 1800)  # 30 minutes

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            last_activity = request.session.get("last_activity")
            now = time.time()

            if last_activity and (now - last_activity) > self.IDLE_TIMEOUT:
                logout(request)
            else:
                request.session["last_activity"] = now

        return self.get_response(request)
```

## SQL Injection Prevention

### Safe: Using ORM

```python
# ORM queries are always parameterized
products = Product.objects.filter(name__icontains=user_input)
products = Product.objects.filter(price__gte=min_price, price__lte=max_price)

# Aggregation
from django.db.models import Q
products = Product.objects.filter(
    Q(name__icontains=query) | Q(description__icontains=query)
)
```

### Safe: Parameterized Raw SQL

```python
# GOOD: Parameters passed separately — Django handles escaping
from django.db import connection

with connection.cursor() as cursor:
    cursor.execute(
        "SELECT * FROM products_product WHERE name ILIKE %s AND price > %s",
        [f"%{search_term}%", min_price],
    )
    rows = cursor.fetchall()

# GOOD: Using RawQuerySet with params
Product.objects.raw(
    "SELECT * FROM products_product WHERE category_id = %s",
    [category_id],
)
```

### DANGEROUS: String Interpolation

```python
# BAD — SQL INJECTION VULNERABILITY
cursor.execute(f"SELECT * FROM products_product WHERE name = '{user_input}'")

# BAD — .format() is equally dangerous
cursor.execute("SELECT * FROM products_product WHERE name = '{}'".format(user_input))

# BAD — % formatting
cursor.execute("SELECT * FROM products_product WHERE name = '%s'" % user_input)

# BAD — .extra() with unescaped input (deprecated)
Product.objects.extra(where=[f"name = '{user_input}'"])
```

## XSS Prevention

### Template Auto-Escaping (Enabled by Default)

```django
{# SAFE: Auto-escaped — <script> tags are rendered as text #}
<p>{{ user_input }}</p>

{# DANGEROUS: Disables escaping — never use with user input #}
<p>{{ user_input|safe }}</p>

{# DANGEROUS: Same as above #}
{% autoescape off %}
    <p>{{ user_input }}</p>
{% endautoescape %}
```

### Safe HTML Generation in Python

```python
from django.utils.html import format_html, escape

# SAFE: format_html escapes arguments, preserves the template
html = format_html('<a href="{}">{}</a>', url, user_provided_text)

# SAFE: Explicit escaping
safe_text = escape(user_input)

# DANGEROUS: mark_safe with user input
from django.utils.safestring import mark_safe
html = mark_safe(f"<p>{user_input}</p>")  # XSS vulnerability
```

### JSON in Templates

```django
{# SAFE: Escapes for JavaScript context #}
<script>
    const data = {{ json_data|json_script:"data-id" }};
</script>

{# DANGEROUS: Direct interpolation #}
<script>
    const data = {{ json_data }};  {# XSS if json_data contains user input #}
</script>
```

## CSRF Protection

### In Forms

```django
<form method="POST" action="{% url 'submit' %}">
    {% csrf_token %}
    {{ form.as_p }}
    <button type="submit">Submit</button>
</form>
```

### AJAX Requests

```javascript
// Read the CSRF token from the cookie
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let cookie of cookies) {
            cookie = cookie.trim();
            if (cookie.startsWith(name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// Include in AJAX headers
fetch('/api/endpoint/', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': getCookie('csrftoken'),
    },
    body: JSON.stringify(data),
});
```

### DRF and CSRF

DRF's `SessionAuthentication` enforces CSRF. Token/JWT authentication does not require CSRF (the token itself is the proof).

```python
# For session-based API views that need CSRF exemption (rare, be careful):
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

@method_decorator(csrf_exempt, name="dispatch")
class WebhookView(APIView):
    """External webhook endpoint — no CSRF needed (use signature verification)."""
    authentication_classes = []
    permission_classes = []
```

## File Upload Validation

```python
"""Validators for uploaded files — type, size, and extension checks."""

import magic
from django.core.exceptions import ValidationError


ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}
ALLOWED_DOC_TYPES = {"application/pdf"}
MAX_UPLOAD_SIZE = 10 * 1024 * 1024  # 10 MB


def validate_file_size(file) -> None:
    """Reject files larger than MAX_UPLOAD_SIZE.

    Args:
        file: Uploaded file object.

    Raises:
        ValidationError: If file exceeds size limit.
    """
    if file.size > MAX_UPLOAD_SIZE:
        max_mb = MAX_UPLOAD_SIZE // (1024 * 1024)
        raise ValidationError(f"File size must not exceed {max_mb} MB.")


def validate_image_type(file) -> None:
    """Validate file is an allowed image type using magic bytes.

    Args:
        file: Uploaded file object.

    Raises:
        ValidationError: If file type is not an allowed image type.
    """
    file.seek(0)
    mime_type = magic.from_buffer(file.read(2048), mime=True)
    file.seek(0)

    if mime_type not in ALLOWED_IMAGE_TYPES:
        raise ValidationError(
            f"Unsupported image type: {mime_type}. "
            f"Allowed: {', '.join(ALLOWED_IMAGE_TYPES)}."
        )


def validate_file_extension(file, allowed_extensions: set[str]) -> None:
    """Check that the file extension is in the allowed set.

    Args:
        file: Uploaded file object.
        allowed_extensions: Set of lowercase extensions (e.g., {'.pdf', '.jpg'}).

    Raises:
        ValidationError: If extension is not allowed.
    """
    import os
    ext = os.path.splitext(file.name)[1].lower()
    if ext not in allowed_extensions:
        raise ValidationError(
            f"File extension '{ext}' is not allowed. "
            f"Allowed: {', '.join(sorted(allowed_extensions))}."
        )
```

Usage in a model:

```python
class Document(models.Model):
    file = models.FileField(
        upload_to="documents/%Y/%m/",
        validators=[validate_file_size],
    )
```

## Rate Limiting — DRF Throttling

```python
# settings.py
REST_FRAMEWORK = {
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon": "100/hour",
        "user": "1000/hour",
        "login": "5/minute",
        "password_reset": "3/hour",
    },
}
```

Custom throttle for sensitive endpoints:

```python
"""Custom throttle classes for authentication endpoints."""

from rest_framework.throttling import SimpleRateThrottle


class LoginRateThrottle(SimpleRateThrottle):
    """Limit login attempts by IP address."""

    scope = "login"

    def get_cache_key(self, request, view):
        return self.cache_format % {
            "scope": self.scope,
            "ident": self.get_ident(request),
        }


class PasswordResetThrottle(SimpleRateThrottle):
    """Limit password reset requests by IP address."""

    scope = "password_reset"

    def get_cache_key(self, request, view):
        return self.cache_format % {
            "scope": self.scope,
            "ident": self.get_ident(request),
        }
```

Apply to specific views:

```python
class LoginView(APIView):
    throttle_classes = [LoginRateThrottle]
    # ...
```

## Content Security Policy Headers

```python
# Install django-csp
# pip install django-csp

# settings.py
MIDDLEWARE += ["csp.middleware.CSPMiddleware"]

# CSP Configuration
CSP_DEFAULT_SRC = ("'self'",)
CSP_SCRIPT_SRC = ("'self'",)
CSP_STYLE_SRC = ("'self'", "'unsafe-inline'")  # Inline styles if needed
CSP_IMG_SRC = ("'self'", "data:", "https:")
CSP_FONT_SRC = ("'self'", "https://fonts.gstatic.com")
CSP_CONNECT_SRC = ("'self'",)
CSP_FRAME_SRC = ("'none'",)
CSP_OBJECT_SRC = ("'none'",)
CSP_BASE_URI = ("'self'",)
CSP_FORM_ACTION = ("'self'",)
CSP_FRAME_ANCESTORS = ("'none'",)

# Report CSP violations (optional)
CSP_REPORT_URI = "/csp-report/"
```

## Environment Variable Management

```python
"""Environment variable management using django-environ."""

# pip install django-environ

import environ

env = environ.Env(
    # Set casting and default values
    DEBUG=(bool, False),
    DJANGO_ALLOWED_HOSTS=(list, []),
    DATABASE_URL=(str, "sqlite:///db.sqlite3"),
)

# Read .env file
environ.Env.read_env(".env")

# Usage
SECRET_KEY = env("DJANGO_SECRET_KEY")
DEBUG = env("DEBUG")
ALLOWED_HOSTS = env("DJANGO_ALLOWED_HOSTS")
DATABASES = {"default": env.db()}

# With defaults
CACHE_TIMEOUT = env.int("CACHE_TIMEOUT", default=300)
FEATURE_FLAG = env.bool("FEATURE_NEW_CHECKOUT", default=False)
```

Example `.env` file (never commit this):

```
DJANGO_SECRET_KEY=your-secret-key-here
DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1
DATABASE_URL=postgres://user:pass@localhost:5432/mydb
REDIS_URL=redis://127.0.0.1:6379/1
EMAIL_HOST=smtp.gmail.com
EMAIL_HOST_USER=you@gmail.com
EMAIL_HOST_PASSWORD=app-password
```

## Security Logging Configuration

```python
# settings.py
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "security": {
            "format": "[%(asctime)s] %(levelname)s %(name)s: %(message)s "
                      "[ip=%(ip)s user=%(user)s]",
        },
    },
    "handlers": {
        "security_file": {
            "level": "WARNING",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": "logs/security.log",
            "maxBytes": 10 * 1024 * 1024,  # 10 MB
            "backupCount": 5,
            "formatter": "security",
        },
        "console": {
            "class": "logging.StreamHandler",
        },
    },
    "loggers": {
        "django.security": {
            "handlers": ["security_file", "console"],
            "level": "WARNING",
            "propagate": False,
        },
        "django.request": {
            "handlers": ["security_file", "console"],
            "level": "WARNING",
            "propagate": False,
        },
        "apps.accounts.security": {
            "handlers": ["security_file"],
            "level": "INFO",
            "propagate": False,
        },
    },
}
```

Usage in authentication views:

```python
import logging

logger = logging.getLogger("apps.accounts.security")


def log_login_attempt(request, email: str, success: bool) -> None:
    """Log authentication attempts for security monitoring.

    Args:
        request: The HTTP request.
        email: The email used in the login attempt.
        success: Whether the login succeeded.
    """
    ip = get_client_ip(request)
    if success:
        logger.info(
            "Successful login for %s",
            email,
            extra={"ip": ip, "user": email},
        )
    else:
        logger.warning(
            "Failed login attempt for %s",
            email,
            extra={"ip": ip, "user": email},
        )


def get_client_ip(request) -> str:
    """Extract client IP from request, handling proxies.

    Args:
        request: The HTTP request.

    Returns:
        Client IP address string.
    """
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        return x_forwarded_for.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "unknown")
```
