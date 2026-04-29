import os
import sqlite3
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

TEST_DB_PATH = Path("test_tracking.db")

os.environ.setdefault("DHL_API_KEY", "dummy-key")
os.environ.setdefault("DHL_API_SECRET", "dummy-secret")
os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB_PATH}"

from src.main import src


@pytest.fixture(autouse=True)
def clean_test_db():
    """Reinicia la base de datos SQLite entre pruebas."""
    if TEST_DB_PATH.exists():
        TEST_DB_PATH.unlink()

    yield

    if TEST_DB_PATH.exists():
        TEST_DB_PATH.unlink()


@pytest.fixture
def client():
    """Fixture que provee un cliente de pruebas para la app."""
    with TestClient(src) as test_client:
        yield test_client


@pytest.fixture
def db_connection():
    """Conexión SQLite para validar persistencia desde las pruebas."""
    connection = sqlite3.connect(TEST_DB_PATH)
    connection.row_factory = sqlite3.Row
    try:
        yield connection
    finally:
        connection.close()
