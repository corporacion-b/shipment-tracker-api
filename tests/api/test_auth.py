import uuid
import pytest

def test_auth_flow(client, db_connection):
    # Generamos un email único para que nunca de 409 Conflict
    unique_id = str(uuid.uuid4())[:8]
    test_email = f"tester_{unique_id}@example.com"
    
    user_data = {
        "email": test_email,
        "password": "password123",
        "full_name": "Tester CI/CD"
    }
    
    # Registro (Esperamos 201)
    register_res = client.post("/auth/register", json=user_data)
    assert register_res.status_code == 201
    
    # Login
    login_data = {
        "username": test_email,
        "password": "password123"
    }
    login_res = client.post("/auth/login", data=login_data)
    assert login_res.status_code == 200