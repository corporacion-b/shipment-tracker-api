import pytest
from fastapi.testclient import TestClient
from urllib.parse import urlparse
import pymysql

from src.main import src as fastapi_app
from src.core.config import settings
from src.db.connection import init_db

@pytest.fixture(scope="session", autouse=True)
def setup_database():
    """Inicializa la base de datos una sola vez para toda la sesión de pruebas."""
    init_db()

@pytest.fixture
def db_connection():
    """Provee una conexión limpia de pymysql basada en el .env/config."""
    url = urlparse(settings.DATABASE_URL)
    connection = pymysql.connect(
        host=url.hostname or "localhost",
        port=url.port or 3306,
        user=url.username,
        password=url.password,
        database=url.path.lstrip("/"),
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=False  # Importante para poder hacer rollback
    )
    yield connection
    connection.rollback() # Revierte cambios para que el siguiente test empiece limpio
    connection.close()

@pytest.fixture
def client():
    """Cliente para realizar peticiones a los endpoints."""
    with TestClient(fastapi_app) as test_client:
        yield test_client