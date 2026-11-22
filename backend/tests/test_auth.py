import pytest


@pytest.mark.asyncio
async def test_health_endpoints(client):
    res = await client.get("/health")
    assert res.status_code == 200
    assert res.json()["status"] == "healthy"

    res_api = await client.get("/api/v1/health/")
    assert res_api.status_code == 200

    res_stats = await client.get("/api/v1/health/stats")
    assert res_stats.status_code == 200
    data = res_stats.json()
    assert "total_projects" in data
    assert "total_runs" in data


@pytest.mark.asyncio
async def test_register_and_login(client):
    # Register
    reg_res = await client.post(
        "/api/v1/auth/register",
        json={"email": "newuser@example.com", "password": "Password123!", "full_name": "New User"},
    )
    assert reg_res.status_code == 201
    user_data = reg_res.json()
    assert user_data["email"] == "newuser@example.com"

    # Login
    login_res = await client.post(
        "/api/v1/auth/login",
        json={"email": "newuser@example.com", "password": "Password123!"},
    )
    assert login_res.status_code == 200
    token_data = login_res.json()
    assert "access_token" in token_data
    token = token_data["access_token"]

    # Verify /auth/me
    me_res = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_res.status_code == 200
    assert me_res.json()["email"] == "newuser@example.com"
