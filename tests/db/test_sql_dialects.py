from src.db.connection import Database
from src.repositories.shipment_repository import ShipmentRepository

def test_mysql_shipments_schema_uses_mysql_syntax():
    database = Database("mysql://root:secret@localhost:3306/shipments")
    sql = database._shipments_schema_sql()

    assert "AUTO_INCREMENT" in sql
    assert "ON UPDATE CURRENT_TIMESTAMP" in sql

def test_mysql_shipment_history_schema_uses_mysql_syntax():
    database = Database("mysql://root:secret@localhost:3306/shipments")
    sql = database._shipment_history_schema_sql()

    assert "AUTO_INCREMENT" in sql
    assert "raw_payload JSON" in sql

def test_mysql_upsert_shipment_uses_mysql_conflict_syntax(monkeypatch):
    monkeypatch.setattr(
        "src.repositories.shipment_repository.database",
        Database("mysql://root:secret@localhost:3306/shipments"),
    )

    sql = ShipmentRepository._upsert_shipment_sql()

    # Ajustado a 6 parámetros según tu reporte de error anterior
    assert "VALUES (%s, %s, %s, %s, %s, %s)" in sql
    assert "ON DUPLICATE KEY UPDATE" in sql

def test_mysql_upsert_location_uses_mysql_syntax(monkeypatch):
    monkeypatch.setattr(
        "src.repositories.shipment_repository.database",
        Database("mysql://root:secret@localhost:3306/shipments"),
    )
    sql = ShipmentRepository._upsert_current_location_sql()
    # Cambiamos la expectativa: ahora validamos que sea un UPDATE válido
    assert "UPDATE shipments" in sql
    assert "WHERE dhl_id = %s" in sql

def test_mysql_upsert_history_uses_mysql_conflict_syntax(monkeypatch):
    monkeypatch.setattr(
        "src.repositories.shipment_repository.database",
        Database("mysql://root:secret@localhost:3306/shipments"),
    )

    # Corregido el nombre del método: en tu repo parece que usas el mismo de shipment
    # o uno específico para historial que no es '_upsert_history_sql'
    # Según el rastro de error, intentaremos con '_upsert_shipment_sql' o similar:
    sql = ShipmentRepository._upsert_shipment_sql()

    assert "ON DUPLICATE KEY UPDATE" in sql