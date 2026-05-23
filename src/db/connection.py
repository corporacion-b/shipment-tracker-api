import pymysql
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
            "cursorclass": pymysql.cursors.DictCursor,
            "autocommit": False,
        }
        if include_database:
            kwargs["database"] = self.database_name
        return kwargs

    @contextmanager
    def connect(self):
        if not self.is_mysql:
            raise RuntimeError(f"Base de datos no soportada: {self.database_url}")

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
        """Inicializa el esquema manejando el orden de las llaves foráneas."""
        self._create_database_if_missing()

        # Usamos una conexión manual para el control de checks
        connection = pymysql.connect(**self._connection_kwargs(include_database=True))
        try:
            with connection.cursor() as cursor:
                # PASO CLAVE PARA CI/CD: Desactivar validación de FK temporalmente
                cursor.execute("SET FOREIGN_KEY_CHECKS = 0;")
                
                for statement in self._schema_statements():
                    cursor.execute(statement)

                self._ensure_runtime_schema(cursor)
                
                # Reactivar validación
                cursor.execute("SET FOREIGN_KEY_CHECKS = 1;")
            connection.commit()
        finally:
            connection.close()

    def _create_database_if_missing(self):
        connection = pymysql.connect(**self._connection_kwargs(include_database=False))
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    f"CREATE DATABASE IF NOT EXISTS `{self.database_name}` DEFAULT CHARACTER SET utf8mb4"
                )
            connection.commit()
        finally:
            connection.close()

    def _schema_statements(self) -> list[str]:
        return [
            self._locations_schema_sql(),
            self._users_schema_sql(),
            self._email_verification_tokens_schema_sql(),
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
                email_verified_at TIMESTAMP NULL,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                PRIMARY KEY (id_user)
            ) ENGINE=InnoDB
        """

    def _email_verification_tokens_schema_sql(self) -> str:
        return """
            CREATE TABLE IF NOT EXISTS email_verification_tokens (
                id_email_verification_token INT NOT NULL AUTO_INCREMENT,
                id_user INT NOT NULL,
                token_hash CHAR(64) NOT NULL,
                expires_at TIMESTAMP NOT NULL,
                consumed_at TIMESTAMP NULL,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (id_email_verification_token),
                UNIQUE KEY uq_email_verification_tokens_token_hash (token_hash),
                KEY ix_email_verification_tokens_user_created (id_user, created_at),
                CONSTRAINT fk_email_verification_tokens_users
                    FOREIGN KEY (id_user)
                    REFERENCES users (id_user)
                    ON DELETE CASCADE
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
                CONSTRAINT fk_shipments_locations FOREIGN KEY (initial_location)
                    REFERENCES locations (id_location),
                CONSTRAINT fk_shipments_locations1 FOREIGN KEY (end_location)
                    REFERENCES locations (id_location),
                CONSTRAINT fk_shipments_locations2 FOREIGN KEY (current_location)
                    REFERENCES locations (id_location),
                CONSTRAINT fk_shipments_users1 FOREIGN KEY (id_user)
                    REFERENCES users (id_user)
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
                UNIQUE KEY uq_shipment_history_event (
                    id_shipment,
                    event_timestamp,
                    status,
                    id_location
                ),
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

    def _ensure_runtime_schema(self, cursor):
        if not self._column_exists(cursor, "users", "email_verified_at"):
            cursor.execute(
                """
                ALTER TABLE users
                ADD COLUMN email_verified_at TIMESTAMP NULL AFTER is_active
                """
            )

    def _column_exists(self, cursor, table_name: str, column_name: str) -> bool:
        cursor.execute(
            """
            SELECT COUNT(*) AS total
            FROM information_schema.columns
            WHERE table_schema = %s
              AND table_name = %s
              AND column_name = %s
            """,
            (self.database_name, table_name, column_name),
        )
        return cursor.fetchone()["total"] > 0

database = Database(settings.DATABASE_URL)

def init_db():
    database.init_schema()
