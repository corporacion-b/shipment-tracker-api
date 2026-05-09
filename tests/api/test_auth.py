import pytest


TEST_EMAIL_PREFIX = "auth-test-"


@pytest.fixture
def clean_auth_users(db_connection):
    with db_connection.cursor() as cursor:
        cursor.execute(
            "DELETE FROM users WHERE email LIKE %s",
            (f"{TEST_EMAIL_PREFIX}%@example.com",),
        )

    yield

    with db_connection.cursor() as cursor:
        cursor.execute(
            "DELETE FROM users WHERE email LIKE %s",
            (f"{TEST_EMAIL_PREFIX}%@example.com",),
        )


def test_register_creates_user(client, clean_auth_users):
    response = client.post(
        "/auth/register",
        json={
            "email": f"{TEST_EMAIL_PREFIX}register@example.com",
            "password": "password123",
        },
    )

    assert response.status_code == 201

    body = response.json()
    assert isinstance(body["id_user"], int)
    assert body["email"] == f"{TEST_EMAIL_PREFIX}register@example.com"
    assert body["is_active"] is True
    assert "hashed_password" not in body


def test_register_duplicate_email_returns_409(client, clean_auth_users):
    payload = {
        "email": f"{TEST_EMAIL_PREFIX}duplicate@example.com",
        "password": "password123",
    }

    first_response = client.post("/auth/register", json=payload)
    duplicate_response = client.post("/auth/register", json=payload)

    assert first_response.status_code == 201
    assert duplicate_response.status_code == 409
    assert duplicate_response.json() == {"detail": "El email ya está registrado."}


def test_login_returns_token(client, clean_auth_users):
    payload = {
        "email": f"{TEST_EMAIL_PREFIX}login@example.com",
        "password": "password123",
    }
    client.post("/auth/register", json=payload)

    response = client.post("/auth/login", json=payload)

    assert response.status_code == 200

    body = response.json()
    assert isinstance(body["access_token"], str)
    assert body["access_token"]
    assert body["token_type"] == "bearer"


def test_login_with_wrong_password_returns_401(client, clean_auth_users):
    client.post(
        "/auth/register",
        json={
            "email": f"{TEST_EMAIL_PREFIX}wrong-password@example.com",
            "password": "password123",
        },
    )

    response = client.post(
        "/auth/login",
        json={
            "email": f"{TEST_EMAIL_PREFIX}wrong-password@example.com",
            "password": "wrong-password",
        },
    )

    assert response.status_code == 401
    assert response.json() == {"detail": "Credenciales inválidas."}
