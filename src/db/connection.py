from contextlib import contextmanager
from urllib.parse import urlparse

from src.core.config import settings


class Database:
    def __init__(self, database_url: str):
        self.database_url = database_url
        parsed = urlparse(database_url)
        self.scheme = parsed.scheme
        self.parsed = parsed
        self.database_name = parsed.path.lstrip("/")

        if not self.database_name:
            raise RuntimeError("DATABASE_URL debe incluir el nombre de la base de datos.")

    @property
    def is_mysql(self) -> bool:
        return self.scheme.startswith("mysql")

    def _connection_kwargs(self, include_database: bool = True) -> dict:
        kwargs = {
            "host": self.parsed.hostname or "localhost",
            "port": self.parsed.port or 3306,
            "user": self.parsed.username,
            "password": self.parsed.password,
            "cursorclass": self._dict_cursor_class(),
            "autocommit": False,
        }

        if include_database:
            kwargs["database"] = self.database_name

        return kwargs

    @staticmethod
    def _dict_cursor_class():
        try:
            import pymysql
        except ImportError as exc:
            raise RuntimeError(
                "Para usar MySQL necesitas instalar la dependencia 'pymysql'."
            ) from exc

        return pymysql.cursors.DictCursor

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

        connection = pymysql.connect(**self._connection_kwargs(include_database=True))

        try:
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def init_schema(self):
        self._create_database_if_missing()

        with self.connect() as connection:
            cursor = connection.cursor()

            for statement in self._schema_statements():
                cursor.execute(statement)

    def _create_database_if_missing(self):
        try:
            import pymysql
        except ImportError as exc:
            raise RuntimeError(
                "Para usar MySQL necesitas instalar la dependencia 'pymysql'."
            ) from exc

        connection = pymysql.connect(**self._connection_kwargs(include_database=False))
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    f"CREATE DATABASE IF NOT EXISTS `{self.database_name}` DEFAULT CHARACTER SET utf8"
                )
            connection.commit()
        finally:
            connection.close()

    def _schema_statements(self) -> list[str]:
        return [
            self._locations_schema_sql(),
            self._users_schema_sql(),
            self._shipments_schema_sql(),
            self._shipment_history_schema_sql(),
        ]

    def _locations_schema_sql(self) -> str:
        return """
            CREATE TABLE IF NOT EXISTS locations (
                id_location INT NOT NULL AUTO_INCREMENT,
                country_code VARCHAR(45) NOT NULL,
                city VARCHAR(45) NOT NULL,
                latitude DECIMAL(9,6) NOT NULL,
                longitude DECIMAL(9,6) NOT NULL,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                PRIMARY KEY (id_location)
            ) ENGINE=InnoDB
        """

    def _users_schema_sql(self) -> str:
        return """
            CREATE TABLE IF NOT EXISTS users (
                id_user INT NOT NULL AUTO_INCREMENT,
                email VARCHAR(255) NOT NULL UNIQUE,
                hashed_password VARCHAR(255) NOT NULL,
                is_active TINYINT NOT NULL DEFAULT 1,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                PRIMARY KEY (id_user)
            ) ENGINE=InnoDB
        """

    def _shipments_schema_sql(self) -> str:
        return """
            CREATE TABLE IF NOT EXISTS shipments (
                id_shipment INT NOT NULL AUTO_INCREMENT,
                dhl_id VARCHAR(100) NOT NULL UNIQUE,
                status VARCHAR(45) NOT NULL,
                weight DECIMAL(10,2) NULL,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                initial_location INT NOT NULL,
                end_location INT NOT NULL,
                current_location INT NULL,
                id_user INT NOT NULL,
                PRIMARY KEY (id_shipment),
                CONSTRAINT fk_shipments_locations
                    FOREIGN KEY (initial_location)
                    REFERENCES locations (id_location)
                    ON DELETE NO ACTION
                    ON UPDATE NO ACTION,
                CONSTRAINT fk_shipments_locations1
                    FOREIGN KEY (end_location)
                    REFERENCES locations (id_location)
                    ON DELETE NO ACTION
                    ON UPDATE NO ACTION,
                CONSTRAINT fk_shipments_locations2
                    FOREIGN KEY (current_location)
                    REFERENCES locations (id_location)
                    ON DELETE NO ACTION
                    ON UPDATE NO ACTION,
                CONSTRAINT fk_shipments_users1
                    FOREIGN KEY (id_user)
                    REFERENCES users (id_user)
                    ON DELETE NO ACTION
                    ON UPDATE NO ACTION
            ) ENGINE=InnoDB
        """

    def _shipment_history_schema_sql(self) -> str:
        return """
            CREATE TABLE IF NOT EXISTS shipment_history (
                id_shipment_history INT NOT NULL AUTO_INCREMENT,
                event_timestamp TIMESTAMP NOT NULL,
                status VARCHAR(50) NOT NULL,
                description TEXT NULL,
                raw_payload JSON NULL,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                id_shipment INT NOT NULL,
                id_location INT NOT NULL,
                PRIMARY KEY (id_shipment_history),
                CONSTRAINT fk_shipment_history_shipments1
                    FOREIGN KEY (id_shipment)
                    REFERENCES shipments (id_shipment)
                    ON DELETE NO ACTION
                    ON UPDATE NO ACTION,
                CONSTRAINT fk_shipment_history_locations1
                    FOREIGN KEY (id_location)
                    REFERENCES locations (id_location)
                    ON DELETE NO ACTION
                    ON UPDATE NO ACTION
            ) ENGINE=InnoDB
        """

database = Database(settings.DATABASE_URL)


def init_db():
    database.init_schema()
