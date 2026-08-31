"""
Authentication endpoint tests.
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_register(client: AsyncClient):
    """Test user registration."""
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "test@example.com",
            "password": "TestPass123",
            "full_name": "Test User",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["success"] is True
    assert "access_token" in data["data"]
    assert "refresh_token" in data["data"]


@pytest.mark.asyncio
async def test_register_duplicate_email(client: AsyncClient):
    """Test that duplicate email registration fails."""
    # Register first user
    await client.post(
        "/api/v1/auth/register",
        json={"email": "dup@example.com", "password": "TestPass123"},
    )
    # Try duplicate
    response = await client.post(
        "/api/v1/auth/register",
        json={"email": "dup@example.com", "password": "TestPass456"},
    )
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_login(client: AsyncClient):
    """Test login with valid credentials."""
    # Register
    await client.post(
        "/api/v1/auth/register",
        json={"email": "login@example.com", "password": "TestPass123"},
    )
    # Login
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "login@example.com", "password": "TestPass123"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True


@pytest.mark.asyncio
async def test_login_invalid_password(client: AsyncClient):
    """Test login with wrong password."""
    await client.post(
        "/api/v1/auth/register",
        json={"email": "wrong@example.com", "password": "TestPass123"},
    )
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "wrong@example.com", "password": "WrongPass"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_me(client: AsyncClient):
    """Test getting current user info."""
    # Register and get token
    reg_response = await client.post(
        "/api/v1/auth/register",
        json={"email": "me@example.com", "password": "TestPass123", "full_name": "Me User"},
    )
    token = reg_response.json()["data"]["access_token"]

    # Get me
    response = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["email"] == "me@example.com"
    assert data["data"]["full_name"] == "Me User"


@pytest.mark.asyncio
async def test_get_me_no_token(client: AsyncClient):
    """Test accessing /me without authentication."""
    response = await client.get("/api/v1/auth/me")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    """Test health endpoint."""
    response = await client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ("healthy", "degraded")
