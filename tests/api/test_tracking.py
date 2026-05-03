import pytest

REAL_ID = "12345688" 

def test_root(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "service" in response.json()

def test_get_full_tracking_integration(client):
    """Verifica que el proxy a DHL funciona."""
    response = client.get(f"/full-tracking/{REAL_ID}")
    if response.status_code == 200:
        assert "shipments" in response.json()
    else:
        assert response.status_code in [404, 429]

def test_get_location_integration(client, db_connection):
    """Prueba real: API DHL -> Normalización -> DB -> Response."""
    response = client.get(f"/location/{REAL_ID}")
    
    if response.status_code == 429:
        pytest.skip("Límite de peticiones de DHL alcanzado (429)")

    assert response.status_code == 200
    data = response.json()
    
    assert data["tracking_id"] == REAL_ID
    assert " - " not in data["location"] 
    assert data["city"] is not None

    row = db_connection.execute(
        "SELECT location, city, timestamp FROM shipments WHERE tracking_id = ?",
        (REAL_ID,)
    ).fetchone()
    
    assert row is not None
    assert row["location"] == data["location"]
    assert row["city"] == data["city"]

def test_get_location_persistence(client, db_connection):
    """Prueba que los datos se guarden en DB tras consultar ubicación."""
    response = client.get(f"/location/{REAL_ID}")
    
    if response.status_code == 200:
        data = response.json()
    
        row = db_connection.execute(
            "SELECT location, city FROM shipments WHERE tracking_id = ?", (REAL_ID,)
        ).fetchone()
        assert row is not None
        assert row["location"] == data["location"]
    elif response.status_code == 429:
        pytest.skip("DHL API Rate limit reached")

def test_get_status_integration(client, db_connection):
    """Prueba real de estado y persistencia."""
    response = client.get(f"/status/{REAL_ID}")
    
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    
    row = db_connection.execute(
        "SELECT current_status FROM shipments WHERE tracking_id = ?",
        (REAL_ID,)
    ).fetchone()
    
    assert row is not None
    assert row["current_status"] == data["status"]

def test_get_status_not_found(client):
    """Verifica el manejo de una guía que no existe (MOCK o Real)."""
    invalid_id = "1234567892"
    response = client.get(f"/status/{invalid_id}")
    
    assert response.status_code == 404
    assert "no encontrada" in response.json()["detail"].lower()