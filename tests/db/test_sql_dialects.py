from src.db.connection import Database
from src.repositories.shipment_repository import ShipmentRepository


def test_mysql_shipments_schema_uses_mysql_syntax():
    database = Database("mysql://root:secret@localhost:3306/shipments")

    sql = database._shipments_schema_sql()

    assert "AUTO_INCREMENT" in sql
    assert "raw_payload JSON NOT NULL" in sql
    assert "ON UPDATE CURRENT_TIMESTAMP" in sql


def test_mysql_tracking_events_schema_uses_mysql_syntax():
    database = Database("mysql://root:secret@localhost:3306/shipments")

    sql = database._tracking_events_schema_sql()

    assert "AUTO_INCREMENT" in sql
    assert "raw_payload JSON" in sql


def test_mysql_upsert_status_uses_mysql_conflict_syntax(monkeypatch):
    monkeypatch.setattr(
        "src.repositories.shipment_repository.database",
        Database("mysql://root:secret@localhost:3306/shipments"),
    )

    sql = ShipmentRepository._upsert_status_sql()

    assert "VALUES (%s, %s, %s, %s, %s, CURRENT_TIMESTAMP)" in sql
    assert "ON DUPLICATE KEY UPDATE" in sql


def test_mysql_upsert_location_uses_mysql_conflict_syntax(monkeypatch):
    monkeypatch.setattr(
        "src.repositories.shipment_repository.database",
        Database("mysql://root:secret@localhost:3306/shipments"),
    )

    sql = ShipmentRepository._upsert_location_sql()

    assert "VALUES (%s, %s, %s, %s, %s, CURRENT_TIMESTAMP)" in sql
    assert "ON DUPLICATE KEY UPDATE" in sql
