# Django REST Framework API Patterns

## Serializer Patterns

### ModelSerializer with Validation

```python
"""Product serializers with validation, computed fields, and nested relations."""

from rest_framework import serializers

from apps.products.models import Product
from apps.categories.models import Category


class ProductListSerializer(serializers.ModelSerializer):
    """Read-only serializer for product list views. Includes computed fields."""

    category_name = serializers.CharField(source="category.name", read_only=True)
    is_available = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "slug",
            "price",
            "stock",
            "status",
            "category_name",
            "is_available",
            "created_at",
        ]

    def get_is_available(self, obj: Product) -> bool:
        """Check if product is active and in stock."""
        return obj.status == "active" and obj.stock > 0


class ProductCreateSerializer(serializers.ModelSerializer):
    """Write serializer for creating products. Validates price and category."""

    class Meta:
        model = Product
        fields = [
            "name",
            "description",
            "price",
            "stock",
            "status",
            "category",
            "tags",
        ]

    def validate_price(self, value):
        """Ensure price is positive."""
        if value <= 0:
            raise serializers.ValidationError("Price must be greater than zero.")
        return value

    def validate(self, attrs):
        """Cross-field validation: draft products don't need stock."""
        if attrs.get("status") == "active" and attrs.get("stock", 0) <= 0:
            raise serializers.ValidationError(
                "Active products must have stock greater than zero."
            )
        return attrs


class ProductDetailSerializer(serializers.ModelSerializer):
    """Read-only detail serializer with nested category and tags."""

    category = CategorySerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    reviews_summary = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "slug",
            "description",
            "price",
            "stock",
            "status",
            "category",
            "tags",
            "reviews_summary",
            "created_at",
            "updated_at",
        ]

    def get_reviews_summary(self, obj: Product) -> dict:
        """Return aggregate review stats."""
        from django.db.models import Avg, Count
        stats = obj.reviews.aggregate(
            count=Count("id"),
            avg_rating=Avg("rating"),
        )
        return {
            "count": stats["count"],
            "avg_rating": round(stats["avg_rating"] or 0, 1),
        }
```

### Nested Serializers

```python
class CategorySerializer(serializers.ModelSerializer):
    """Category serializer for nesting inside product responses."""

    class Meta:
        model = Category
        fields = ["id", "name", "slug"]


class TagSerializer(serializers.ModelSerializer):
    """Tag serializer for nesting inside product responses."""

    class Meta:
        model = Tag
        fields = ["id", "name"]
```

### Separate Read/Create Serializers

Use different serializers for reading vs. writing. This avoids bloated serializers with `read_only`/`write_only` field juggling.

```python
class OrderCreateSerializer(serializers.Serializer):
    """Write-only serializer for order creation input."""

    items = serializers.ListField(
        child=serializers.DictField(),
        min_length=1,
    )
    shipping_address = serializers.CharField(max_length=500)

    def validate_items(self, value):
        """Validate each item has product_id and quantity."""
        for item in value:
            if "product_id" not in item or "quantity" not in item:
                raise serializers.ValidationError(
                    "Each item must have 'product_id' and 'quantity'."
                )
            if item["quantity"] < 1:
                raise serializers.ValidationError("Quantity must be at least 1.")
        return value


class OrderDetailSerializer(serializers.ModelSerializer):
    """Read-only serializer for order responses."""

    items = OrderItemSerializer(many=True, read_only=True)
    user = serializers.StringRelatedField()

    class Meta:
        model = Order
        fields = [
            "id",
            "user",
            "status",
            "total",
            "shipping_address",
            "items",
            "created_at",
        ]
```

## ViewSet Patterns

```python
"""Product ViewSet with dynamic serializer selection, custom actions, and filtering."""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from apps.products.models import Product
from apps.products.serializers import (
    ProductListSerializer,
    ProductCreateSerializer,
    ProductDetailSerializer,
)
from apps.products.filters import ProductFilter
from apps.products.permissions import IsOwnerOrReadOnly


class ProductViewSet(viewsets.ModelViewSet):
    """Full CRUD for products with role-based serializer selection."""

    queryset = Product.objects.select_related("category").prefetch_related("tags")
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = ProductFilter
    search_fields = ["name", "description"]
    ordering_fields = ["price", "created_at", "name"]
    ordering = ["-created_at"]

    def get_serializer_class(self):
        """Return the appropriate serializer for the action."""
        if self.action == "list":
            return ProductListSerializer
        if self.action in ("create", "update", "partial_update"):
            return ProductCreateSerializer
        return ProductDetailSerializer

    def get_permissions(self):
        """Admins can create/update/delete; others can only read."""
        if self.action in ("create", "update", "partial_update", "destroy"):
            return [IsAdminUser()]
        return [IsAuthenticated()]

    def perform_create(self, serializer):
        """Attach the requesting user as the product creator."""
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated])
    def favorite(self, request, pk=None):
        """Toggle favorite status for the authenticated user."""
        product = self.get_object()
        user = request.user

        if user.favorite_products.filter(pk=product.pk).exists():
            user.favorite_products.remove(product)
            return Response({"status": "unfavorited"})

        user.favorite_products.add(product)
        return Response({"status": "favorited"}, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=["get"])
    def featured(self, request):
        """Return featured products."""
        products = self.get_queryset().filter(is_featured=True, status="active")
        page = self.paginate_queryset(products)
        if page is not None:
            serializer = ProductListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = ProductListSerializer(products, many=True)
        return Response(serializer.data)
```

## Permission Patterns

```python
"""Custom DRF permissions for object-level and role-based access control."""

from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsOwnerOrReadOnly(BasePermission):
    """Allow owners full access; everyone else read-only."""

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        return obj.user == request.user


class IsAdminOrReadOnly(BasePermission):
    """Allow admin users full access; everyone else read-only."""

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return request.user and request.user.is_staff


class IsVerifiedUser(BasePermission):
    """Only allow users who have verified their email."""

    message = "Email verification is required to perform this action."

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and getattr(request.user, "is_email_verified", False)
        )
```

## Filter Backends

```python
"""Product filter using django-filter for structured query parameters."""

import django_filters

from apps.products.models import Product


class ProductFilter(django_filters.FilterSet):
    """Filter products by price range, category, status, and date."""

    min_price = django_filters.NumberFilter(field_name="price", lookup_expr="gte")
    max_price = django_filters.NumberFilter(field_name="price", lookup_expr="lte")
    category = django_filters.CharFilter(field_name="category__slug")
    status = django_filters.ChoiceFilter(choices=Product.Status.choices)
    created_after = django_filters.DateTimeFilter(
        field_name="created_at", lookup_expr="gte"
    )
    created_before = django_filters.DateTimeFilter(
        field_name="created_at", lookup_expr="lte"
    )
    in_stock = django_filters.BooleanFilter(method="filter_in_stock")

    class Meta:
        model = Product
        fields = ["status", "category"]

    def filter_in_stock(self, queryset, name, value):
        """Filter to products with stock > 0 when in_stock=true."""
        if value:
            return queryset.filter(stock__gt=0)
        return queryset.filter(stock=0)
```

### URL Configuration for ViewSets

```python
"""URL configuration using DRF routers."""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from apps.products.views import ProductViewSet

router = DefaultRouter()
router.register("products", ProductViewSet, basename="product")

urlpatterns = [
    path("api/v1/", include(router.urls)),
]
```

### Search and Ordering in the API

```
# Search (matches name or description)
GET /api/v1/products/?search=laptop

# Ordering
GET /api/v1/products/?ordering=-price
GET /api/v1/products/?ordering=name

# Filtering
GET /api/v1/products/?min_price=100&max_price=500&category=electronics&in_stock=true

# Combined
GET /api/v1/products/?search=laptop&min_price=500&ordering=-created_at&status=active
```

## API Response Format Conventions

Use consistent response envelopes for non-DRF views or custom actions:

```python
from rest_framework.response import Response
from rest_framework import status


def success_response(data, status_code=status.HTTP_200_OK, message="Success"):
    """Standard success response envelope."""
    return Response(
        {"status": "success", "message": message, "data": data},
        status=status_code,
    )


def error_response(message, status_code=status.HTTP_400_BAD_REQUEST, errors=None):
    """Standard error response envelope."""
    return Response(
        {"status": "error", "message": message, "errors": errors},
        status=status_code,
    )
```

## Pagination

```python
"""Custom pagination classes."""

from rest_framework.pagination import PageNumberPagination, CursorPagination


class StandardPagination(PageNumberPagination):
    """Standard offset-based pagination with configurable page size."""

    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100


class TimelinePagination(CursorPagination):
    """Cursor-based pagination for chronological feeds. Efficient for large datasets."""

    page_size = 20
    ordering = "-created_at"
    cursor_query_param = "cursor"
```
