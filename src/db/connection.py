from contextlib import contextmanager
from urllib.parse import urlparse

from src.core.config import settings


class Database:
    def __init__(self, database_url: str):
        self.database_url = database_url
        parsed = urlparse(database_url)
        self.scheme = parsed.scheme
        self.parsed = parsed

    @property
    def is_mysql(self) -> bool:
        return self.scheme.startswith("mysql")

    @contextmanager
    def connect(self):
        if not self.is_mysql:
            raise RuntimeError(f"Base de datos no soportada: {self.database_url}")

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
            cursor.execute(self._shipments_schema_sql())
            cursor.execute(self._tracking_events_schema_sql())

    def _shipments_schema_sql(self) -> str:
        return """
            CREATE TABLE IF NOT EXISTS shipments (
                id BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
                tracking_id VARCHAR(255) NOT NULL UNIQUE,
                carrier VARCHAR(100),
                current_status VARCHAR(100),
                current_description TEXT,
                location VARCHAR(255),
                city VARCHAR(255),
                timestamp VARCHAR(255),
                raw_payload JSON NOT NULL,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                last_synced_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """

    def _tracking_events_schema_sql(self) -> str:
        return """
            CREATE TABLE IF NOT EXISTS tracking_events (
                id BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
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


database = Database(settings.DATABASE_URL)


def init_db():
    database.init_schema()
