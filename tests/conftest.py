import os

import pymysql
import pytest
from dotenv import load_dotenv
from fastapi.testclient import TestClient

load_dotenv()

os.environ.setdefault("DHL_API_KEY", "dummy-key")
os.environ["DATABASE_URL"] = "mysql://root:secret@127.0.0.1:3307/shipments"

from src.db.connection import init_db
from src.main import src


@pytest.fixture
def clean_test_db():
    init_db()
    connection = pymysql.connect(
        host="127.0.0.1",
        port=3307,
        user="root",
        password="secret",
        database="shipments",
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=True,
    )
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
    connection = pymysql.connect(
        host="127.0.0.1",
        port=3307,
        user="root",
        password="secret",
        database="shipments",
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=True,
    )
    try:
        yield connection
    finally:
        connection.close()
