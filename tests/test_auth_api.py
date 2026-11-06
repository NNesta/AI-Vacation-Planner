from tests.conftest import register_and_login


async def test_register_and_login_returns_a_usable_token(client):
    headers = await register_and_login(client)

    response = await client.get("/api/v1/auth/me", headers=headers)

    assert response.status_code == 200
    assert response.json()["email"] == "alice@example.com"


async def test_register_rejects_a_duplicate_email(client):
    await register_and_login(client)

    response = await client.post(
        "/api/v1/auth/register",
        json={
            "username": "someone-else",
            "email": "alice@example.com",
            "firstname": "A",
            "lastname": "B",
            "password": "another-password",
        },
    )

    assert response.status_code == 400


async def test_login_rejects_a_wrong_password(client):
    await register_and_login(client)

    response = await client.post(
        "/api/v1/auth/login", data={"username": "alice@example.com", "password": "wrong-password"}
    )

    assert response.status_code == 401


async def test_me_requires_a_token(client):
    assert (await client.get("/api/v1/auth/me")).status_code == 401


async def test_me_rejects_a_forged_token(client):
    response = await client.get("/api/v1/auth/me", headers={"Authorization": "Bearer forged"})

    assert response.status_code == 401
