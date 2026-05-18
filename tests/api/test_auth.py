import uuid

import pytest


@pytest.mark.integration
def test_auth_flow(client, db_connection):
    test_email = f"tester_{uuid.uuid4().hex[:8]}@example.com"
    user_data = {
        "email": test_email,
        "password": "password123",
    }

    register_res = client.post("/auth/register", json=user_data)
    assert register_res.status_code == 201
    assert register_res.json()["email"] == test_email

    login_res = client.post(
        "/auth/login",
        data={"username": test_email, "password": "password123"},
    )
    assert login_res.status_code == 200

    token = login_res.json()["access_token"]
    me_res = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_res.status_code == 200
    assert me_res.json()["email"] == test_email
