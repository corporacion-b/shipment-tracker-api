import sqlite3
from contextlib import contextmanager
from pathlib import Path
from urllib.parse import urlparse

from src.core.config import settings


class Database:
    def __init__(self, database_url: str):
        self.database_url = database_url
        parsed = urlparse(database_url)
        self.scheme = parsed.scheme
        self.parsed = parsed

    @property
    def is_sqlite(self) -> bool:
        return self.scheme == "sqlite"

    @property
    def is_mysql(self) -> bool:
        return self.scheme.startswith("mysql")

    @contextmanager
    def connect(self):
        if self.is_sqlite:
            db_path = self.parsed.path or "/:memory:"
            if db_path != "/:memory:":
                path = Path(db_path.lstrip("/"))
                if path.parent != Path("."):
                    path.parent.mkdir(parents=True, exist_ok=True)
                db_path = str(path)

            connection = sqlite3.connect(db_path, check_same_thread=False)
            connection.row_factory = sqlite3.Row
        elif self.is_mysql:
            try:
                import pymysql
            except ImportError as exc:
                raise RuntimeError(
                    "Para usar MySQL necesitas instalar la dependencia 'pymysql'."
                ) from exc

            connection = pymysql.connect(
                host=self.parsed.hostname or "localhost",
                port=self.parsed.port or 3306,
                user=self.parsed.username,
                password=self.parsed.password,
                database=self.parsed.path.lstrip("/"),
                cursorclass=pymysql.cursors.DictCursor,
                autocommit=False,
            )
        else:
            raise RuntimeError(f"Base de datos no soportada: {self.database_url}")

        try:
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def init_schema(self):
        with self.connect() as connection:
            cursor = connection.cursor()

            if self.is_sqlite:
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS shipments (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        tracking_id TEXT NOT NULL UNIQUE,
                        carrier TEXT NOT NULL,
                        current_status TEXT NOT NULL,
                        current_description TEXT NOT NULL,
                        raw_payload TEXT NOT NULL,
                        created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        last_synced_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                    )
                    """
                )
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS tracking_events (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        shipment_id INTEGER NOT NULL,
                        status TEXT NOT NULL,
                        description TEXT NOT NULL,
                        location TEXT,
                        event_time TIMESTAMP,
                        raw_payload TEXT,
                        created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (shipment_id) REFERENCES shipments(id)
                    )
                    """
                )
            else:
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS shipments (
                        id BIGINT PRIMARY KEY AUTO_INCREMENT,
                        tracking_id VARCHAR(255) NOT NULL UNIQUE,
                        carrier VARCHAR(50) NOT NULL,
                        current_status VARCHAR(100) NOT NULL,
                        current_description TEXT NOT NULL,
                        raw_payload JSON NOT NULL,
                        created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                        last_synced_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                    )
                    """
                )
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS tracking_events (
                        id BIGINT PRIMARY KEY AUTO_INCREMENT,
                        shipment_id BIGINT NOT NULL,
                        status VARCHAR(100) NOT NULL,
                        description TEXT NOT NULL,
                        location VARCHAR(255),
                        event_time TIMESTAMP NULL,
                        raw_payload JSON,
                        created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (shipment_id) REFERENCES shipments(id)
                    )
                    """
                )


database = Database(settings.DATABASE_URL)


def init_db():
    database.init_schema()
