import os
import sqlite3
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from dotenv import load_dotenv # <--- Carga automática de .env

# Cargar variables desde el archivo .env real
load_dotenv()

TEST_DB_PATH = Path("test_tracking.db")

# Si no están en el .env, usará dummy para no romper la app, 
# pero fallarán los tests reales.
os.environ.setdefault("DHL_API_KEY", "dummy-key")
os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB_PATH}"

from src.db.connection import init_db
from src.main import src

@pytest.fixture(autouse=True)
def clean_test_db():
    if TEST_DB_PATH.exists():
        try:
            TEST_DB_PATH.unlink()
        except PermissionError:
            pass 
    init_db()
    yield

@pytest.fixture
def client():
    with TestClient(src) as test_client:
        yield test_client

@pytest.fixture
def db_connection():
    init_db()
    connection = sqlite3.connect(TEST_DB_PATH)
    connection.row_factory = sqlite3.Row
    try:
        yield connection
    finally:
        connection.close()