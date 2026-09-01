"""Pytest fixtures and test environment setup."""

import asyncio
from typing import AsyncGenerator
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings
from app.core.security import create_access_token, get_password_hash
from app.db.base import Base
from app.api.deps import get_async_db
from app.main import create_app
from app.models.user import User, UserRole

# Use SQLite in-memory for fast unit/integration testing
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(TEST_DATABASE_URL, echo=False, future=True)
TestAsyncSessionFactory = async_sessionmaker(
    bind=test_engine, class_=AsyncSession, expire_on_commit=False
)


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Create clean database tables and yield a test session."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with TestAsyncSessionFactory() as session:
        yield session

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture(scope="function")
async def test_admin_user(db_session: AsyncSession) -> User:
    """Create and return a test admin user."""
    user = User(
        email="admin_test@example.com",
        hashed_password=get_password_hash("testpass123"),
        full_name="Admin Tester",
        role=UserRole.ADMIN,
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture(scope="function")
async def test_operator_user(db_session: AsyncSession) -> User:
    """Create and return a test operator user."""
    user = User(
        email="operator_test@example.com",
        hashed_password=get_password_hash("testpass123"),
        full_name="Operator Tester",
        role=UserRole.OPERATOR,
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
def admin_token(test_admin_user: User) -> str:
    """Generate a JWT token for the test admin user."""
    return create_access_token(subject=test_admin_user.id, role=test_admin_user.role.value)


@pytest.fixture
def operator_token(test_operator_user: User) -> str:
    """Generate a JWT token for the test operator user."""
    return create_access_token(subject=test_operator_user.id, role=test_operator_user.role.value)


@pytest_asyncio.fixture(scope="function")
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Async HTTP client overriding database dependency."""
    app = create_app()

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_async_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
