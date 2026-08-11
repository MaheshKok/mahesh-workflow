---
name: fastapi-patterns
description: FastAPI best practices covering project structure, Pydantic v2 schemas, dependency injection, async handlers, authentication, authorization, transactional service layers, and testing with httpx and pytest.
metadata:
  origin: ECC
---

# FastAPI Patterns

Modern, production-grade FastAPI development: project layout, Pydantic v2 schemas, dependency injection, async patterns, auth, transactional service methods, and testing.

## Project Structure

```text
my_app/
|-- app/
|   |-- main.py               # App factory, lifespan, middleware
|   |-- config.py             # Settings via pydantic-settings
|   |-- dependencies.py       # Shared FastAPI dependencies
|   |-- database/
|   |   |-- base.py           # SQLAlchemy declarative base
|   |   `-- session_manager/
|   |       `-- db_session.py # Async engine + task-local session manager
|   |-- routers/
|   |   `-- users.py
|   |-- models/               # SQLAlchemy ORM models
|   |   `-- user.py
|   |-- schemas/              # Pydantic request/response schemas
|   |   `-- user.py
|   `-- services/             # Business logic layer
|       `-- user_service.py
|-- tests/
|   |-- conftest.py
|   `-- test_users.py
|-- pyproject.toml
`-- .env
```

---

## App Factory and Lifespan

```python
# app/main.py
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database.session_manager.db_session import Database
from app.routers import users


@asynccontextmanager
async def lifespan(app: FastAPI):
    Database.init(settings.database_url)
    try:
        yield
    finally:
        await Database.dispose()


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=settings.allow_credentials,
        allow_methods=settings.allowed_methods,
        allow_headers=settings.allowed_headers,
    )

    app.include_router(users.router, prefix="/users", tags=["users"])

    return app


app = create_app()
```

---

## Database Session Manager

```python
# app/database/session_manager/db_session.py
from contextvars import ContextVar

from sqlalchemy.engine import URL
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

_engine: AsyncEngine | None = None
_session_maker: async_sessionmaker[AsyncSession] | None = None
_session: ContextVar[AsyncSession | None] = ContextVar("database_session", default=None)


class Database:
    def __init__(self, *, session_args: dict | None = None, commit_on_exit: bool = False):
        self._session_args = session_args or {}
        self._commit_on_exit = commit_on_exit
        self._active_session: AsyncSession | None = None
        self._token = None

    @classmethod
    def init(
        cls,
        db_url: str | URL | None = None,
        *,
        custom_engine: AsyncEngine | None = None,
        engine_kw: dict | None = None,
        session_args: dict | None = None,
    ) -> None:
        global _engine, _session_maker
        if (db_url is None) == (custom_engine is None):
            raise ValueError("Pass exactly one of db_url or custom_engine")

        _engine = custom_engine or create_async_engine(db_url, **(engine_kw or {}))
        _session_maker = async_sessionmaker(
            _engine, expire_on_commit=False, **(session_args or {})
        )

    @classmethod
    def engine(cls) -> AsyncEngine:
        if _engine is None:
            raise RuntimeError("Database is not initialized")
        return _engine

    @classmethod
    def session(cls) -> AsyncSession:
        session = _session.get()
        if session is None:
            raise RuntimeError("No database session in this async context")
        return session

    async def __aenter__(self) -> AsyncSession:
        if _session_maker is None:
            raise RuntimeError("Database is not initialized")
        self._active_session = _session_maker(**self._session_args)
        self._token = _session.set(self._active_session)
        return self.session()

    async def __aexit__(self, exc_type, exc_value, traceback) -> bool:
        try:
            if exc_type is not None:
                await self._active_session.rollback()
            elif self._commit_on_exit:
                try:
                    await self._active_session.commit()
                except Exception:
                    await self._active_session.rollback()
                    raise
        finally:
            try:
                await self._active_session.close()
            finally:
                _session.reset(self._token)
        return False

    @classmethod
    async def dispose(cls) -> None:
        global _engine, _session_maker
        engine_to_dispose = _engine
        _engine = None
        _session_maker = None
        if engine_to_dispose is not None:
            await engine_to_dispose.dispose()
```

Dependency-injected service sessions use `Database(commit_on_exit=False)` because services own commit and rollback. A direct context that owns a write uses `Database(commit_on_exit=True)`, which commits only after its body completes successfully.

---

## Configuration with pydantic-settings

```python
# app/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    app_name: str = "My App"
    app_version: str = "0.1.0"
    debug: bool = False

    database_url: str
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # Pydantic-settings v2 safely evaluates mutable list literals directly
    allowed_origins: list[str] = ["http://localhost:3000"]
    allowed_methods: list[str] = ["GET", "POST", "PATCH", "DELETE", "OPTIONS"]
    allowed_headers: list[str] = ["Authorization", "Content-Type"]
    allow_credentials: bool = True


settings = Settings()
```

---

## Pydantic Schemas (v2)

```python
# app/schemas/user.py
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, model_validator


class UserBase(BaseModel):
    email: EmailStr
    username: str = Field(min_length=3, max_length=50)


class UserCreate(UserBase):
    password: str = Field(min_length=8)
    password_confirm: str

    @model_validator(mode="after")
    def passwords_match(self) -> "UserCreate":
        if self.password != self.password_confirm:
            raise ValueError("Passwords do not match")
        return self


class UserUpdate(BaseModel):
    username: str | None = Field(default=None, min_length=3, max_length=50)
    email: EmailStr | None = None


class UserResponse(UserBase):
    id: int
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class UserListResponse(BaseModel):
    total: int
    items: list[UserResponse]
```

---

## Dependency Injection

```python
# app/dependencies.py
from typing import Annotated, AsyncGenerator
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database.session_manager.db_session import Database
from app.models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/users/token")


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with Database(commit_on_exit=False) as session:
        yield session


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        subject = payload.get("sub")
        if subject is None:
            raise credentials_exception
        user_id = int(subject)
    except (JWTError, TypeError, ValueError):
        raise credentials_exception

    user = await db.get(User, user_id)
    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    if not current_user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Inactive user")
    return current_user


DbDep = Annotated[AsyncSession, Depends(get_db)]
CurrentUserDep = Annotated[User, Depends(get_current_user)]
ActiveUserDep = Annotated[User, Depends(get_current_active_user)]
```

---

## Router and Endpoint Design

```python
# app/routers/users.py
from typing import Annotated
from fastapi import APIRouter, HTTPException, Query, status
from fastapi.security import OAuth2PasswordRequestForm

from app.dependencies import ActiveUserDep, DbDep
from app.schemas.user import UserCreate, UserResponse, UserUpdate, UserListResponse
from app.services.user_service import DuplicateUserError, UserService

router = APIRouter()


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(payload: UserCreate, db: DbDep) -> UserResponse:
    service = UserService(db)
    try:
        return await service.create(payload)
    except DuplicateUserError:
        raise HTTPException(status_code=400, detail="Email already registered")


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: ActiveUserDep) -> UserResponse:
    return current_user


@router.get("/", response_model=UserListResponse)
async def list_users(
    db: DbDep,
    current_user: ActiveUserDep,
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
) -> UserListResponse:
    service = UserService(db)
    users, total = await service.list(skip=skip, limit=limit)
    return UserListResponse(total=total, items=users)


@router.patch("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    payload: UserUpdate,
    db: DbDep,
    current_user: ActiveUserDep,
) -> UserResponse:
    if current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized")
    service = UserService(db)
    try:
        user = await service.update(user_id, payload)
    except DuplicateUserError:
        raise HTTPException(status_code=400, detail="Email already registered")
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.post("/token")
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: DbDep,
) -> dict[str, str]:
    service = UserService(db)
    token = await service.authenticate(form_data.username, form_data.password)
    if token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return {"access_token": token, "token_type": "bearer"}
```

---

## Service Layer

```python
# app/services/user_service.py
from datetime import datetime, timedelta, timezone

from jose import jwt
from passlib.context import CryptContext
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class DuplicateUserError(Exception):
    """Raised when a unique user field conflicts with an existing row."""


class UserService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_email(self, email: str) -> User | None:
        result = await self.db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def create(self, payload: UserCreate) -> User:
        user = User(
            email=payload.email,
            username=payload.username,
            hashed_password=pwd_context.hash(payload.password),
        )
        self.db.add(user)
        try:
            # Rely on atomic DB constraints rather than race-prone application-level prechecks
            await self.db.commit()
        except IntegrityError as exc:
            await self.db.rollback()
            raise DuplicateUserError from exc
        await self.db.refresh(user)
        return user

    async def list(self, skip: int = 0, limit: int = 20) -> tuple[list[User], int]:
        total_result = await self.db.execute(select(func.count(User.id)))
        total = total_result.scalar_one()
        # Enforce explicit deterministic ordering to ensure reliable pagination
        result = await self.db.execute(
            select(User).order_by(User.id).offset(skip).limit(limit)
        )
        return list(result.scalars()), total

    async def update(self, user_id: int, payload: UserUpdate) -> User | None:
        user = await self.db.get(User, user_id)
        if user is None:
            return None
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(user, field, value)
        try:
            await self.db.commit()
        except IntegrityError as exc:
            await self.db.rollback()
            raise DuplicateUserError from exc
        await self.db.refresh(user)
        return user

    async def authenticate(self, email: str, password: str) -> str | None:
        user = await self.get_by_email(email)
        if user is None or not pwd_context.verify(password, user.hashed_password):
            return None
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.access_token_expire_minutes
        )
        return jwt.encode(
            {"sub": str(user.id), "exp": expire},
            settings.secret_key,
            algorithm=settings.algorithm,
        )
```

> **Note on Database Design:** Application-level unique handling requires an underlying unique database index (e.g., `unique=True` on your SQLAlchemy mapping attributes). Without underlying constraints, application layer error-catching cannot safely prevent concurrent race conditions.

---

## Testing with httpx and pytest

Choose test isolation to fit the database and suite size. Create and drop the schema per test for a small suite or SQLite; it is the straightforward portable pattern, but use only a disposable test database. For a large suite on a dedicated database with reliable SAVEPOINT support, create the schema once and roll back an outer transaction per test. Neither pattern is universally best. SQLite drivers have SAVEPOINT caveats, so prefer the portable pattern unless the exact driver behavior is verified.

### Portable schema-per-test fixture

```python
# tests/conftest.py
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine

from app.database.base import Base
from app.database.session_manager.db_session import Database
from app.main import create_app

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture(autouse=True)
async def setup_db():
    engine = create_async_engine(TEST_DATABASE_URL)
    Database.init(custom_engine=engine)
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        yield
    finally:
        try:
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.drop_all)
        finally:
            await Database.dispose()


@pytest_asyncio.fixture
async def db_session():
    async with Database(commit_on_exit=False) as session:
        yield session


@pytest_asyncio.fixture
async def client():
    app = create_app()

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac


@pytest_asyncio.fixture
async def registered_user(client: AsyncClient) -> dict:
    resp = await client.post("/users/", json={
        "email": "test@example.com",
        "username": "testuser",
        "password": "securepass1",
        "password_confirm": "securepass1",
    })
    assert resp.status_code == 201
    return resp.json()


@pytest_asyncio.fixture
async def auth_token(client: AsyncClient, registered_user: dict) -> str:
    resp = await client.post("/users/token", data={
        "username": "test@example.com",
        "password": "securepass1",
    })
    assert resp.status_code == 200
    return resp.json()["access_token"]


@pytest_asyncio.fixture
async def auth_client(client: AsyncClient, auth_token: str) -> AsyncClient:
    client.headers.update({"Authorization": f"Bearer {auth_token}"})
    return client
```

Plain `ASGITransport` intentionally skips ASGI startup and shutdown. Use this form when request tests do not need lifespan resources; `setup_db` owns the disposable database while the app lifespan stays inactive.

### Fast SAVEPOINT fixture for a dedicated test database

Create the schema once, then bind each test session to one connection and outer transaction. `join_transaction_mode="create_savepoint"` keeps service-owned `commit()` and `rollback()` within a SAVEPOINT; roll back the outer transaction after the test.

```toml
# pyproject.toml
[tool.pytest.ini_options]
asyncio_default_fixture_loop_scope = "session"
asyncio_default_test_loop_scope = "session"
```

Keep session-scoped async engine fixtures and their consumers on compatible pytest-asyncio loop scopes. Under xdist, provide worker isolation with a separate test database or schema per worker. Sequences and other non-transactional state may not reset after an outer rollback.

```python
# tests/conftest.py
import pytest_asyncio
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from app.database.base import Base
from app.dependencies import get_db
from app.main import create_app


@pytest_asyncio.fixture(scope="session")
async def engine():
    engine = create_async_engine("postgresql+asyncpg://test:test@localhost/test")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    try:
        yield engine
    finally:
        try:
            async with engine.begin() as connection:
                await connection.run_sync(Base.metadata.drop_all)
        finally:
            await engine.dispose()


@pytest_asyncio.fixture
async def db_session(engine):
    async with engine.connect() as connection:
        outer_transaction = await connection.begin()
        session = AsyncSession(
            bind=connection,
            expire_on_commit=False,
            join_transaction_mode="create_savepoint",
        )
        try:
            yield session
        finally:
            try:
                await session.close()
            finally:
                await outer_transaction.rollback()


@pytest_asyncio.fixture
async def client(db_session: AsyncSession):
    test_app: FastAPI = create_app()

    async def override_get_db():
        yield db_session

    test_app.dependency_overrides[get_db] = override_get_db
    try:
        async with AsyncClient(
            transport=ASGITransport(app=test_app), base_url="http://test"
        ) as ac:
            yield ac
    finally:
        test_app.dependency_overrides.clear()
```

Use this fixture session exactly through `test_app.dependency_overrides`; do not let a request create a separate `Database` manager session. Services still own `commit()` and `rollback()`.

### Lifespan-aware client

Add `asgi-lifespan` to test dependencies when startup or shutdown must run. Build `test_app` with test-only database, cache, and other resources before startup. Do not combine a lifespan that calls `Database.init` with another fixture owning the global `Database` manager unless their lifecycle is explicitly coordinated.

```python
from asgi_lifespan import LifespanManager
from httpx import ASGITransport, AsyncClient
import pytest_asyncio


@pytest_asyncio.fixture
async def lifespan_client(test_app):
    async with LifespanManager(test_app) as manager:
        async with AsyncClient(
            transport=ASGITransport(app=manager.app), base_url="http://test"
        ) as client:
            yield client
```

---

## Anti-Patterns

```python
# Bad: business logic inside route handlers.
@router.post("/users/")
async def create_user(payload: UserCreate, db: DbDep):
    hashed = bcrypt.hash(payload.password)
    user = User(email=payload.email, hashed_password=hashed)
    db.add(user)
    await db.commit()
    return user

# Good: thin route, transactional service handling.
@router.post("/users/", response_model=UserResponse, status_code=201)
async def create_user(payload: UserCreate, db: DbDep):
    try:
        return await UserService(db).create(payload)
    except DuplicateUserError:
        raise HTTPException(status_code=400, detail="Email already registered")


# Bad: sync DB calls in async routes block the event loop.
@router.get("/items/")
async def list_items(db: Session = Depends(get_db)):
    return db.query(Item).all()

# Good: use async SQLAlchemy executions.
@router.get("/items/")
async def list_items(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Item))
    return result.scalars().all()
```

---

## Best Practices

- Always declare a typed `response_model` to prevent accidental PII/data leaks and output clean OpenAPI schemas.
- Consolidate standard middleware dependency injections via type-aliasing: `DbDep = Annotated[AsyncSession, Depends(get_db)]`.
- Wrap database mutation boundaries gracefully within transactions inside your service layer, catching structural database errors directly.
- Initialize `Database` once in the lifespan; dependency sessions use `commit_on_exit=False` when services own commits.
- Use a disposable test DB with schema-per-test fixtures for portable test isolation; use outer transactions and SAVEPOINTs only on a dedicated database with verified driver support.
- Treat plain `ASGITransport` as request-only. Use `LifespanManager` and test-only resources when startup or shutdown behavior is part of the test.
- Parse JWT parameters defensively, expecting potential string/integer cast mismatches from modern payload variations.
- Enforce deterministic sorting (e.g., `.order_by(Model.id)`) on all offset/limit paginated endpoints to avoid data skips.
- Isolate authorization checks from core authentication dependencies to provide precise REST status signals (`401` vs `403`).
