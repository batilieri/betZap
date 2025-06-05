import asyncio
import pytest
from httpx import AsyncClient
from web.main import app
from web.core.database import AsyncSessionLocal, engine
from web.models import Base


@pytest.fixture
async def client():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest.fixture(autouse=True)
async def setup_database():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


async def test_login():
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Test user registration
        response = await client.post("/api/v1/auth/register", json={
            "email": "test@test.com",
            "name": "Test User",
            "password": "test123"
        })
        assert response.status_code == 200

        # Test login
        response = await client.post("/api/v1/auth/login", data={
            "username": "test@test.com",
            "password": "test123"
        })
        assert response.status_code == 200
        assert "access_token" in response.json()