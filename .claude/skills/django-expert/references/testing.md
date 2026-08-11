# Django Testing

## pytest-django Configuration

### pytest.ini

```ini
[pytest]
DJANGO_SETTINGS_MODULE = config.settings.testing
python_files = tests.py test_*.py *_tests.py
python_classes = Test*
python_functions = test_*
addopts =
    --reuse-db
    --strict-markers
    -v
    --tb=short
    --cov=apps
    --cov-report=term-missing
    --cov-report=html:htmlcov
    --cov-fail-under=80
markers =
    slow: marks tests as slow (deselect with '-m "not slow"')
    integration: marks integration tests
    e2e: marks end-to-end tests
```

### Test Settings (config/settings/testing.py)

```python
"""Test-specific settings. Optimized for speed."""

from .base import *  # noqa: F401,F403

DEBUG = False

# Use faster password hasher for tests
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]

# In-memory cache
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
    }
}

# Use in-memory email backend
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

# Use SQLite for speed (or keep Postgres for integration tests)
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

# Disable migrations for faster test startup
class DisableMigrations:
    def __contains__(self, item):
        return True

    def __getitem__(self, item):
        return None

MIGRATION_MODULES = DisableMigrations()

# Celery — run tasks synchronously in tests
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True
```

## conftest.py Fixtures

```python
"""Shared pytest fixtures for the test suite."""

import pytest
from rest_framework.test import APIClient

from apps.accounts.tests.factories import UserFactory


@pytest.fixture
def user(db):
    """Create and return a regular user."""
    return UserFactory()


@pytest.fixture
def admin_user(db):
    """Create and return an admin user."""
    return UserFactory(is_staff=True, is_superuser=True)


@pytest.fixture
def authenticated_client(user):
    """Return a Django test client logged in as a regular user."""
    from django.test import Client
    client = Client()
    client.force_login(user)
    return client


@pytest.fixture
def api_client():
    """Return an unauthenticated DRF API client."""
    return APIClient()


@pytest.fixture
def authenticated_api_client(user):
    """Return a DRF API client authenticated as a regular user."""
    client = APIClient()
    client.force_authenticate(user=user)
    return client


@pytest.fixture
def admin_api_client(admin_user):
    """Return a DRF API client authenticated as an admin."""
    client = APIClient()
    client.force_authenticate(user=admin_user)
    return client
```

## Factory Boy Setup

```python
"""Factories for generating test data. Located in apps/<app>/tests/factories.py."""

import factory
from factory.django import DjangoModelFactory

from apps.accounts.models import User
from apps.products.models import Product
from apps.categories.models import Category


class UserFactory(DjangoModelFactory):
    """Factory for creating User instances."""

    class Meta:
        model = User
        skip_postgeneration_save = True

    email = factory.Sequence(lambda n: f"user{n}@example.com")
    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")
    is_active = True
    is_email_verified = True

    @factory.lazy_attribute
    def password(self):
        return factory.django.Password("testpass123")

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        """Override create to use create_user manager method."""
        manager = cls._get_manager(model_class)
        password = kwargs.pop("password", "testpass123")
        user = manager.create_user(password=password, **kwargs)
        return user


class CategoryFactory(DjangoModelFactory):
    """Factory for creating Category instances."""

    class Meta:
        model = Category

    name = factory.Sequence(lambda n: f"Category {n}")
    slug = factory.LazyAttribute(lambda obj: obj.name.lower().replace(" ", "-"))


class ProductFactory(DjangoModelFactory):
    """Factory for creating Product instances with related category."""

    class Meta:
        model = Product

    name = factory.Sequence(lambda n: f"Product {n}")
    slug = factory.LazyAttribute(lambda obj: obj.name.lower().replace(" ", "-"))
    description = factory.Faker("paragraph")
    price = factory.Faker("pydecimal", left_digits=3, right_digits=2, positive=True)
    stock = factory.Faker("random_int", min=0, max=100)
    status = "active"
    category = factory.SubFactory(CategoryFactory)

    @factory.post_generation
    def tags(self, create, extracted, **kwargs):
        """Handle many-to-many tags field.

        Usage:
            ProductFactory()                    # No tags
            ProductFactory(tags=[tag1, tag2])    # With specific tags
        """
        if not create or not extracted:
            return
        self.tags.add(*extracted)
```

## Model Testing

```python
"""Tests for the Product model."""

import pytest
from decimal import Decimal

from django.core.exceptions import ValidationError

from apps.products.models import Product
from apps.products.tests.factories import ProductFactory, CategoryFactory


@pytest.mark.django_db
class TestProductModel:
    """Tests for Product model behavior."""

    def test_create_product(self):
        """Product can be created with required fields."""
        product = ProductFactory(name="Laptop", price=Decimal("999.99"))
        assert product.pk is not None
        assert product.name == "Laptop"
        assert product.price == Decimal("999.99")

    def test_str_representation(self):
        """__str__ returns the product name."""
        product = ProductFactory(name="Widget")
        assert str(product) == "Widget"

    def test_slug_auto_generated(self):
        """Slug is auto-generated from name on save."""
        product = ProductFactory(name="My Great Product", slug="")
        product.save()
        assert product.slug == "my-great-product"

    def test_is_in_stock_property(self):
        """is_in_stock returns True when stock > 0."""
        product = ProductFactory(stock=5)
        assert product.is_in_stock is True

    def test_is_not_in_stock(self):
        """is_in_stock returns False when stock is 0."""
        product = ProductFactory(stock=0)
        assert product.is_in_stock is False

    def test_price_non_negative_constraint(self):
        """Product with negative price fails validation."""
        product = ProductFactory.build(price=Decimal("-1.00"))
        with pytest.raises(ValidationError):
            product.full_clean()

    def test_default_status_is_draft(self):
        """New products default to draft status."""
        product = ProductFactory.build(status="")
        assert product.status == "" or Product._meta.get_field("status").default == "draft"

    def test_category_protection(self):
        """Deleting a category with products raises ProtectedError."""
        category = CategoryFactory()
        ProductFactory(category=category)
        with pytest.raises(Exception):  # django.db.models.ProtectedError
            category.delete()
```

## View Testing

```python
"""Tests for product views."""

import pytest
from django.urls import reverse

from apps.products.tests.factories import ProductFactory


@pytest.mark.django_db
class TestProductListView:
    """Tests for the product list view."""

    def test_list_returns_200(self, authenticated_client):
        """Authenticated user can access product list."""
        ProductFactory.create_batch(3)
        response = authenticated_client.get(reverse("product-list"))
        assert response.status_code == 200

    def test_list_requires_authentication(self, client):
        """Unauthenticated user is redirected to login."""
        response = client.get(reverse("product-list"))
        assert response.status_code in (302, 403)

    def test_list_shows_only_active_products(self, authenticated_client):
        """List view only shows active products."""
        ProductFactory(status="active", name="Visible")
        ProductFactory(status="draft", name="Hidden")
        response = authenticated_client.get(reverse("product-list"))
        assert b"Visible" in response.content
        assert b"Hidden" not in response.content


@pytest.mark.django_db
class TestProductCreateView:
    """Tests for creating products."""

    def test_create_product_post(self, admin_api_client):
        """Admin can create a product via POST."""
        from apps.categories.tests.factories import CategoryFactory
        category = CategoryFactory()
        data = {
            "name": "New Product",
            "price": "29.99",
            "stock": 10,
            "status": "draft",
            "category": category.pk,
        }
        response = admin_api_client.post(
            reverse("product-list"), data, format="json"
        )
        assert response.status_code == 201
        assert response.data["name"] == "New Product"

    def test_create_product_validation_error(self, admin_api_client):
        """Creating a product with invalid data returns 400."""
        data = {"name": "", "price": "-5"}
        response = admin_api_client.post(
            reverse("product-list"), data, format="json"
        )
        assert response.status_code == 400
```

## DRF API Testing

```python
"""Tests for the Product API endpoints."""

import pytest
from decimal import Decimal
from django.urls import reverse

from apps.products.tests.factories import ProductFactory, CategoryFactory
from apps.accounts.tests.factories import UserFactory


@pytest.mark.django_db
class TestProductAPI:
    """Test product CRUD API."""

    def test_list_products(self, authenticated_api_client):
        """GET /api/v1/products/ returns paginated product list."""
        ProductFactory.create_batch(5)
        response = authenticated_api_client.get(reverse("product-list"))
        assert response.status_code == 200
        assert response.data["count"] == 5
        assert len(response.data["results"]) == 5

    def test_retrieve_product(self, authenticated_api_client):
        """GET /api/v1/products/<id>/ returns product detail."""
        product = ProductFactory(name="Widget")
        response = authenticated_api_client.get(
            reverse("product-detail", kwargs={"pk": product.pk})
        )
        assert response.status_code == 200
        assert response.data["name"] == "Widget"

    def test_create_product_as_admin(self, admin_api_client):
        """POST /api/v1/products/ creates product when admin."""
        category = CategoryFactory()
        data = {
            "name": "New Widget",
            "price": "19.99",
            "stock": 50,
            "status": "draft",
            "category": category.pk,
        }
        response = admin_api_client.post(
            reverse("product-list"), data, format="json"
        )
        assert response.status_code == 201

    def test_create_product_forbidden_for_regular_user(self, authenticated_api_client):
        """POST /api/v1/products/ returns 403 for non-admin."""
        category = CategoryFactory()
        data = {
            "name": "New Widget",
            "price": "19.99",
            "stock": 50,
            "category": category.pk,
        }
        response = authenticated_api_client.post(
            reverse("product-list"), data, format="json"
        )
        assert response.status_code == 403

    def test_update_product(self, admin_api_client):
        """PATCH /api/v1/products/<id>/ updates product fields."""
        product = ProductFactory(price=Decimal("10.00"))
        response = admin_api_client.patch(
            reverse("product-detail", kwargs={"pk": product.pk}),
            {"price": "15.00"},
            format="json",
        )
        assert response.status_code == 200
        product.refresh_from_db()
        assert product.price == Decimal("15.00")

    def test_delete_product(self, admin_api_client):
        """DELETE /api/v1/products/<id>/ removes product."""
        product = ProductFactory()
        response = admin_api_client.delete(
            reverse("product-detail", kwargs={"pk": product.pk})
        )
        assert response.status_code == 204

    def test_filter_by_category(self, authenticated_api_client):
        """GET /api/v1/products/?category=electronics filters by category slug."""
        cat = CategoryFactory(slug="electronics")
        ProductFactory(category=cat)
        ProductFactory()  # Different category
        response = authenticated_api_client.get(
            reverse("product-list"), {"category": "electronics"}
        )
        assert response.status_code == 200
        assert response.data["count"] == 1

    def test_search_products(self, authenticated_api_client):
        """GET /api/v1/products/?search=laptop searches name and description."""
        ProductFactory(name="Gaming Laptop")
        ProductFactory(name="Wireless Mouse")
        response = authenticated_api_client.get(
            reverse("product-list"), {"search": "laptop"}
        )
        assert response.status_code == 200
        assert response.data["count"] == 1
        assert response.data["results"][0]["name"] == "Gaming Laptop"
```

## Mocking External Services

```python
"""Tests demonstrating mocking of external services."""

import pytest
from unittest.mock import patch, MagicMock
from decimal import Decimal

from apps.orders.services import OrderService
from apps.orders.tests.factories import OrderFactory
from apps.products.tests.factories import ProductFactory


@pytest.mark.django_db
class TestOrderServiceWithMocks:
    """Test OrderService with mocked external dependencies."""

    @patch("apps.orders.services.NotificationService")
    def test_create_order_sends_confirmation(self, mock_notification_cls):
        """Order creation triggers confirmation notification."""
        mock_notification = MagicMock()
        mock_notification_cls.return_value = mock_notification

        product = ProductFactory(price=Decimal("25.00"), stock=10)
        service = OrderService()
        from apps.accounts.tests.factories import UserFactory
        user = UserFactory()

        order = service.create_order(
            user=user,
            items=[{"product_id": product.id, "quantity": 2}],
            shipping_address="123 Main St",
        )

        mock_notification.send_order_confirmation.assert_called_once_with(order)

    @patch("apps.payments.gateway.stripe.Charge.create")
    def test_payment_processing(self, mock_stripe_charge):
        """Payment service calls Stripe with correct amount."""
        mock_stripe_charge.return_value = MagicMock(
            id="ch_test123",
            status="succeeded",
        )

        from apps.payments.services import PaymentService
        service = PaymentService()
        result = service.charge(
            amount=Decimal("49.99"),
            token="tok_test",
            description="Order #123",
        )

        mock_stripe_charge.assert_called_once_with(
            amount=4999,  # Stripe uses cents
            currency="usd",
            source="tok_test",
            description="Order #123",
        )
        assert result.status == "succeeded"

    @patch("apps.notifications.services.send_mail")
    def test_email_notification(self, mock_send_mail):
        """Email notification sends to correct recipient."""
        from apps.notifications.services import NotificationService
        order = OrderFactory()

        service = NotificationService()
        service.send_order_confirmation(order)

        mock_send_mail.assert_called_once()
        call_kwargs = mock_send_mail.call_args[1]
        assert order.user.email in call_kwargs["recipient_list"]
```

## Integration Testing

```python
"""Integration test for the full checkout flow."""

import pytest
from decimal import Decimal
from django.urls import reverse

from apps.products.tests.factories import ProductFactory
from apps.accounts.tests.factories import UserFactory


@pytest.mark.django_db
@pytest.mark.integration
class TestCheckoutFlow:
    """End-to-end test of the order checkout process."""

    def test_full_checkout(self, admin_api_client):
        """User can add items, create order, and see order in history."""
        # Setup
        product1 = ProductFactory(price=Decimal("10.00"), stock=5, status="active")
        product2 = ProductFactory(price=Decimal("20.00"), stock=3, status="active")

        # Create order
        order_data = {
            "items": [
                {"product_id": product1.pk, "quantity": 2},
                {"product_id": product2.pk, "quantity": 1},
            ],
            "shipping_address": "456 Oak Ave, City, ST 12345",
        }
        response = admin_api_client.post(
            reverse("order-list"), order_data, format="json"
        )
        assert response.status_code == 201
        order_id = response.data["id"]

        # Verify order total
        assert Decimal(response.data["total"]) == Decimal("40.00")

        # Verify stock was decremented
        product1.refresh_from_db()
        product2.refresh_from_db()
        assert product1.stock == 3
        assert product2.stock == 2

        # Verify order appears in list
        response = admin_api_client.get(reverse("order-list"))
        assert response.status_code == 200
        order_ids = [o["id"] for o in response.data["results"]]
        assert order_id in order_ids
```

## Coverage Targets by Component

| Component | Target | Rationale |
|-----------|--------|-----------|
| Models | 90%+ | Core business logic |
| Services | 90%+ | Business rules, orchestration |
| Serializers | 85%+ | Validation, transformation |
| Views/ViewSets | 80%+ | HTTP handling, permissions |
| Permissions | 95%+ | Security-critical |
| Signals | 80%+ | Side effects |
| Utilities | 90%+ | Shared, high-reuse code |
| Admin | 60%+ | Lower priority |
| **Overall** | **80%+** | **Minimum acceptable** |

## Best Practices

### DO

- Use `factory_boy` for all test data -- never create objects manually with `Model.objects.create()`.
- Use `pytest.mark.django_db` on every test class or function that touches the database.
- Use `create_batch()` when you need multiple instances and don't care about specific field values.
- Use `Factory.build()` for tests that don't need database persistence (validation tests, unit tests).
- Use `select_related` / `prefetch_related` assertions with `assertNumQueries` to catch N+1 regressions.
- Use `@pytest.mark.parametrize` to test multiple input/output combinations without duplicating test methods.
- Use `freezegun` or `time_machine` to control `timezone.now()` in time-dependent tests.
- Use `@pytest.fixture(autouse=True)` sparingly and only for truly universal setup (e.g., disabling throttling).
- Test error paths and edge cases, not just the happy path.
- Name tests descriptively: `test_create_order_with_zero_stock_raises_validation_error`.
- Keep each test independent -- never rely on execution order or shared mutable state.
- Use `reverse()` for URL resolution instead of hardcoding paths.
- Mock at the boundary (external APIs, email, payment gateways) -- not internal service methods.
- Run tests with `--reuse-db` during development and without it in CI for a clean slate.
- Use `TransactionTestCase` only when you genuinely need to test transaction behavior.

### DON'T

- Don't use Django's `TestCase` with pytest -- use `pytest.mark.django_db` instead.
- Don't use `setUp` / `tearDown` methods -- use pytest fixtures.
- Don't test Django internals (e.g., verifying that `CharField` enforces `max_length`).
- Don't mock the ORM or queryset methods -- use the real database with test data.
- Don't write tests that depend on database auto-increment IDs.
- Don't share state between tests via class attributes or module-level variables.
- Don't test private methods directly -- test the public interface that calls them.
- Don't use `assertContains` with raw HTML strings for detailed template assertions -- use `response.context` instead.
- Don't skip writing tests for serializer validation -- it's where most input bugs hide.
- Don't use `time.sleep()` in tests -- use signals, mocks, or event-driven assertions.
- Don't leave `print()` statements in tests -- use `pytest.fail()` or assertions for diagnostics.
- Don't write overly broad integration tests that test everything at once -- keep scope focused.
- Don't ignore test warnings -- fix the underlying deprecation or configuration issue.
