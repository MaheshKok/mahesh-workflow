# Django ORM & Models

## Model Best Practices

```python
"""Product model with proper field configuration, Meta, indexes, and constraints."""

from django.db import models
from django.core.validators import MinValueValidator
from django.utils.text import slugify


class Product(models.Model):
    """Represents a product in the catalog."""

    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        ACTIVE = "active", "Active"
        ARCHIVED = "archived", "Archived"

    name = models.CharField(max_length=255, db_index=True)
    slug = models.SlugField(max_length=255, unique=True)
    description = models.TextField(blank=True, default="")
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
    )
    stock = models.PositiveIntegerField(default=0)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
        db_index=True,
    )
    category = models.ForeignKey(
        "categories.Category",
        on_delete=models.PROTECT,
        related_name="products",
    )
    tags = models.ManyToManyField("tags.Tag", blank=True, related_name="products")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status", "created_at"]),
            models.Index(fields=["category", "status"]),
            models.Index(
                fields=["name"],
                name="product_name_trgm_idx",
                opclasses=["gin_trgm_ops"],  # PostgreSQL trigram index for search
            ),
        ]
        constraints = [
            models.CheckConstraint(
                check=models.Q(price__gte=0),
                name="product_price_non_negative",
            ),
            models.UniqueConstraint(
                fields=["category", "slug"],
                name="unique_slug_per_category",
            ),
        ]

    def __str__(self) -> str:
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    @property
    def is_in_stock(self) -> bool:
        """Check if product has available stock."""
        return self.stock > 0
```

## Abstract Base Model

```python
"""Timestamped abstract base model for all project models."""

from django.db import models


class TimeStampedModel(models.Model):
    """Abstract model providing created_at and updated_at timestamps."""

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
```

## Custom QuerySet

```python
"""Custom QuerySet for Product with chainable, reusable filters."""

from django.db import models
from django.db.models import Q


class ProductQuerySet(models.QuerySet):
    """Chainable queryset methods for products."""

    def active(self) -> "ProductQuerySet":
        """Return only active products."""
        return self.filter(status="active")

    def in_stock(self) -> "ProductQuerySet":
        """Return only products with stock > 0."""
        return self.filter(stock__gt=0)

    def with_category(self, category_slug: str) -> "ProductQuerySet":
        """Filter products by category slug."""
        return self.filter(category__slug=category_slug)

    def search(self, query: str) -> "ProductQuerySet":
        """Full-text search across name and description."""
        if not query:
            return self.none()
        return self.filter(
            Q(name__icontains=query) | Q(description__icontains=query)
        )

    def price_range(
        self, min_price: float | None = None, max_price: float | None = None
    ) -> "ProductQuerySet":
        """Filter by price range."""
        qs = self
        if min_price is not None:
            qs = qs.filter(price__gte=min_price)
        if max_price is not None:
            qs = qs.filter(price__lte=max_price)
        return qs

    def with_related(self) -> "ProductQuerySet":
        """Eager-load common relations to prevent N+1 queries."""
        return self.select_related("category").prefetch_related("tags")
```

## Custom Manager

```python
"""Custom Manager exposing ProductQuerySet methods and adding create helpers."""

from django.db import models


class ProductManager(models.Manager):
    """Manager for Product model with convenience methods."""

    def get_queryset(self) -> "ProductQuerySet":
        """Return custom ProductQuerySet."""
        from apps.products.querysets import ProductQuerySet
        return ProductQuerySet(self.model, using=self._db)

    def active(self):
        """Shortcut: Product.objects.active()"""
        return self.get_queryset().active()

    def get_or_none(self, **kwargs):
        """Return object or None instead of raising DoesNotExist.

        Args:
            **kwargs: Lookup parameters.

        Returns:
            Model instance or None.
        """
        try:
            return self.get(**kwargs)
        except self.model.DoesNotExist:
            return None

    def create_with_tags(self, tags: list, **kwargs):
        """Create a product and attach tags in one call.

        Args:
            tags: List of Tag instances or IDs.
            **kwargs: Fields for Product creation.

        Returns:
            Created Product instance with tags attached.
        """
        product = self.create(**kwargs)
        product.tags.set(tags)
        return product

    def bulk_update_stock(self, updates: list[dict]) -> int:
        """Bulk update stock levels.

        Args:
            updates: List of dicts with 'id' and 'stock' keys.

        Returns:
            Number of rows updated.
        """
        products = []
        product_map = {p.id: p for p in self.filter(id__in=[u["id"] for u in updates])}
        for update in updates:
            product = product_map.get(update["id"])
            if product:
                product.stock = update["stock"]
                products.append(product)
        return self.model.objects.bulk_update(products, ["stock"])
```

Attach the manager to the model:

```python
class Product(models.Model):
    # ... fields ...
    objects = ProductManager()
```

## N+1 Query Prevention

### The Problem

```python
# BAD: N+1 — each iteration triggers a separate query for category
products = Product.objects.all()
for product in products:
    print(product.category.name)  # N extra queries
```

### select_related — ForeignKey / OneToOneField (SQL JOIN)

```python
# GOOD: Single query with JOIN
products = Product.objects.select_related("category").all()
for product in products:
    print(product.category.name)  # No extra query

# Chain multiple foreign keys
orders = Order.objects.select_related("user", "shipping_address", "product__category")
```

### prefetch_related — ManyToManyField / Reverse ForeignKey (Separate query)

```python
# GOOD: Two queries total (one for products, one for tags)
products = Product.objects.prefetch_related("tags").all()
for product in products:
    print([tag.name for tag in product.tags.all()])  # No extra query

# Custom prefetch with filtering
from django.db.models import Prefetch

products = Product.objects.prefetch_related(
    Prefetch(
        "reviews",
        queryset=Review.objects.filter(rating__gte=4).select_related("user"),
        to_attr="top_reviews",
    )
)
for product in products:
    for review in product.top_reviews:  # Cached, filtered, no extra query
        print(review.user.username)
```

### When to Use Which

| Relationship | Method | Why |
|---|---|---|
| ForeignKey | select_related | SQL JOIN, single query |
| OneToOneField | select_related | SQL JOIN, single query |
| ManyToManyField | prefetch_related | Separate query, avoids Cartesian product |
| Reverse FK (related_name) | prefetch_related | Separate query per relation |
| Reverse FK + filter | Prefetch() object | Custom queryset on the prefetch |

## Database Indexing

```python
class Meta:
    indexes = [
        # Single-column index for frequent lookups
        models.Index(fields=["email"]),

        # Composite index — order matters (left-prefix rule)
        models.Index(fields=["status", "created_at"]),

        # Partial index — only index active rows (PostgreSQL)
        models.Index(
            fields=["created_at"],
            name="active_products_idx",
            condition=models.Q(status="active"),
        ),

        # Descending index for ORDER BY ... DESC
        models.Index(fields=["-created_at"]),

        # Covering index (include extra columns to avoid table lookup)
        models.Index(
            fields=["category"],
            include=["name", "price"],
            name="category_covering_idx",
        ),
    ]
```

Guidelines:
- Index columns used in WHERE, ORDER BY, JOIN.
- Composite indexes: put high-selectivity columns first.
- Avoid indexing columns with low cardinality (boolean, status with 2 values) unless combined with another column.
- Use `EXPLAIN ANALYZE` to verify index usage.
- Too many indexes slow writes. Profile before adding.

## Bulk Operations

```python
from django.db import connection

# --- bulk_create: insert many rows in one query ---
products = [
    Product(name=f"Product {i}", price=9.99, stock=100, category=category)
    for i in range(1000)
]
Product.objects.bulk_create(products, batch_size=500)

# bulk_create with ignore_conflicts (skip duplicates)
Product.objects.bulk_create(products, ignore_conflicts=True)

# bulk_create with update_conflicts (upsert, PostgreSQL)
Product.objects.bulk_create(
    products,
    update_conflicts=True,
    unique_fields=["slug"],
    update_fields=["price", "stock"],
)


# --- bulk_update: update specific fields on many rows ---
products = Product.objects.filter(status="draft")
for product in products:
    product.status = "active"
Product.objects.bulk_update(products, ["status"], batch_size=500)


# --- Bulk delete with subquery ---
stale_ids = Product.objects.filter(
    status="archived",
    updated_at__lt=one_year_ago,
).values_list("id", flat=True)

# Delete in batches to avoid long locks
while True:
    batch = list(stale_ids[:1000])
    if not batch:
        break
    deleted, _ = Product.objects.filter(id__in=batch).delete()


# --- F() expressions for atomic updates (no race condition) ---
from django.db.models import F

Product.objects.filter(id=product_id).update(stock=F("stock") - 1)


# --- Subquery and OuterRef for correlated subqueries ---
from django.db.models import Subquery, OuterRef

latest_order = Order.objects.filter(
    user=OuterRef("pk")
).order_by("-created_at").values("created_at")[:1]

users_with_latest_order = User.objects.annotate(
    last_order_date=Subquery(latest_order)
)
```

## Caching Strategies

### View-Level Caching

```python
from django.views.decorators.cache import cache_page

@cache_page(60 * 15)  # 15 minutes
def product_list(request):
    products = Product.objects.active().with_related()
    return render(request, "products/list.html", {"products": products})
```

### Template Fragment Caching

```django
{% load cache %}
{% cache 900 product_detail product.pk product.updated_at %}
    <div class="product">
        <h2>{{ product.name }}</h2>
        <p>{{ product.description }}</p>
    </div>
{% endcache %}
```

### Low-Level Caching

```python
from django.core.cache import cache


def get_product_stats(category_id: int) -> dict:
    """Return cached product stats for a category.

    Args:
        category_id: The category to compute stats for.

    Returns:
        Dict with count, avg_price, total_stock.
    """
    cache_key = f"product_stats:{category_id}"
    stats = cache.get(cache_key)

    if stats is None:
        stats = Product.objects.filter(
            category_id=category_id, status="active"
        ).aggregate(
            count=models.Count("id"),
            avg_price=models.Avg("price"),
            total_stock=models.Sum("stock"),
        )
        cache.set(cache_key, stats, timeout=60 * 30)  # 30 minutes

    return stats
```

### QuerySet Caching Pattern

```python
from django.core.cache import cache


def get_featured_products() -> list:
    """Return cached list of featured products.

    Returns:
        List of Product dicts (id, name, price, slug).
    """
    cache_key = "featured_products"
    products = cache.get(cache_key)

    if products is None:
        products = list(
            Product.objects.filter(
                status="active", is_featured=True
            ).values("id", "name", "price", "slug")[:12]
        )
        cache.set(cache_key, products, timeout=60 * 60)  # 1 hour

    return products
```

### Cache Invalidation via Signals

```python
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.cache import cache

from apps.products.models import Product


@receiver([post_save, post_delete], sender=Product)
def invalidate_product_caches(sender, instance, **kwargs):
    """Clear product-related caches when a product changes."""
    cache.delete(f"product_stats:{instance.category_id}")
    cache.delete("featured_products")
```
