---
name: django-expert
description: "Comprehensive Django development expert. Use when working with Django projects, DRF APIs, ORM, migrations, or Django security. Requires Django in requirements/imports."
---

# Django Expert

Consolidated Django development skill with progressive disclosure. Read reference files only when the specific topic is relevant.

## When to Activate

- Working on a Django project (Django in requirements.txt or imports)
- Building Django REST Framework APIs
- Designing Django models or migrations
- Configuring Django security or deployment

## Core Rules (Always Apply)

1. Use custom User model (AbstractUser) from day one.
2. Use select_related() for ForeignKey, prefetch_related() for ManyToMany — prevent N+1.
3. Use transaction.atomic() for multi-step database operations.
4. Never interpolate user input into raw SQL — use ORM or parameterized queries.
5. Always run makemigrations --check before committing model changes.
6. Use Django's auto-escaping — never mark user input as safe.
7. Set DEBUG=False, configure ALLOWED_HOSTS, enable HTTPS in production.
8. Use environment variables for SECRET_KEY, database credentials, API keys.
9. Use service layer for business logic — keep views thin.
10. Use factory_boy for test data, not manual object creation.
11. Use pytest-django with --reuse-db for fast tests.
12. Include {% csrf_token %} in all POST forms.

## Reference Guide

| Topic | File | Read when... |
|-------|------|-------------|
| Architecture | references/architecture.md | Project structure, split settings, service layer pattern |
| ORM & Models | references/orm.md | Model design, querysets, managers, N+1 prevention, bulk operations, indexing |
| REST API | references/api.md | DRF serializers, ViewSets, permissions, filtering, pagination |
| Security | references/security.md | Auth, CSRF, XSS, SQL injection, file uploads, rate limiting, headers |
| Testing | references/testing.md | pytest-django, factory_boy, model/view/API testing, mocking |
| Verification | references/verification.md | Pre-PR/deploy pipeline, CI/CD, configuration review, checklist |

## Constraints

- MUST read relevant reference file before writing code in that topic area
- MUST run python-reviewer agent after completing code changes
- MUST follow TDD: write test first, then implement
- MUST achieve 80%+ test coverage
