import os
import pymysql
import pytest
from dotenv import load_dotenv
from fastapi.testclient import TestClient
from urllib.parse import urlparse

load_dotenv()

os.environ.setdefault("DHL_API_KEY", "dummy-key")
os.environ.setdefault("DATABASE_URL", "mysql://root:secret@127.0.0.1:3307/shipments")

from src.db.connection import init_db
from src.main import src

def get_db_params():
    url = urlparse(os.environ["DATABASE_URL"])
    return {
        "host": url.hostname,
        "port": url.port,
        "user": url.username,
        "password": url.password,
        "database": url.path.lstrip("/"),
        "cursorclass": pymysql.cursors.DictCursor,
        "autocommit": True,
    }

@pytest.fixture
def clean_test_db():
    init_db()
    connection = pymysql.connect(**get_db_params())
    try:
        with connection.cursor() as cursor:
            cursor.execute("DELETE FROM tracking_events")
            cursor.execute("DELETE FROM shipments")
        yield
    finally:
        connection.close()


@pytest.fixture
def client():
    with TestClient(src) as test_client:
        yield test_client


@pytest.fixture
def db_connection():
    init_db()
    connection = pymysql.connect(**get_db_params())
    try:
        yield connection
    finally:
        connection.close()