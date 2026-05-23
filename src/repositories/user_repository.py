from src.db.connection import database


class UserRepository:
    @staticmethod
    def _public_user(row: dict) -> dict:
        return {
            "id_user": row["id_user"],
            "email": row["email"],
            "is_active": bool(row["is_active"]),
            "email_verified": row.get("email_verified_at") is not None,
        }

    def create_user(self, email: str, hashed_password: str) -> dict:
        with database.connect() as connection:
            cursor = connection.cursor()
            cursor.execute(
                """
                INSERT INTO users (email, hashed_password)
                VALUES (%s, %s)
                """,
                (email, hashed_password),
            )
            user_id = cursor.lastrowid

            cursor.execute(
                """
                SELECT id_user, email, is_active, email_verified_at
                FROM users
                WHERE id_user = %s
                """,
                (user_id,),
            )
            return self._public_user(cursor.fetchone())

    def get_by_email(self, email: str) -> dict | None:
        with database.connect() as connection:
            cursor = connection.cursor()
            cursor.execute(
                """
                SELECT id_user, email, hashed_password, is_active, email_verified_at
                FROM users
                WHERE email = %s
                """,
                (email,),
            )
            row = cursor.fetchone()

        if row is not None:
            row["is_active"] = bool(row["is_active"])

        return row

    def get_by_id(self, user_id: int) -> dict | None:
        with database.connect() as connection:
            cursor = connection.cursor()
            cursor.execute(
                """
                SELECT id_user, email, is_active, email_verified_at
                FROM users
                WHERE id_user = %s
                """,
                (user_id,),
            )
            row = cursor.fetchone()

        if row is None:
            return None

        return self._public_user(row)

    def create_email_verification_token(
        self,
        user_id: int,
        token_hash: str,
        expires_at,
    ) -> dict:
        with database.connect() as connection:
            cursor = connection.cursor()
            cursor.execute(
                """
                UPDATE email_verification_tokens
                SET consumed_at = CURRENT_TIMESTAMP
                WHERE id_user = %s
                  AND consumed_at IS NULL
                """,
                (user_id,),
            )
            cursor.execute(
                """
                INSERT INTO email_verification_tokens (id_user, token_hash, expires_at)
                VALUES (%s, %s, %s)
                """,
                (user_id, token_hash, expires_at),
            )
            token_id = cursor.lastrowid
            cursor.execute(
                """
                SELECT id_email_verification_token, id_user, token_hash,
                       expires_at, consumed_at, created_at
                FROM email_verification_tokens
                WHERE id_email_verification_token = %s
                """,
                (token_id,),
            )
            return cursor.fetchone()

    def get_email_verification_token(self, token_hash: str) -> dict | None:
        with database.connect() as connection:
            cursor = connection.cursor()
            cursor.execute(
                """
                SELECT
                    evt.id_email_verification_token,
                    evt.id_user,
                    evt.token_hash,
                    evt.expires_at,
                    evt.consumed_at,
                    evt.created_at,
                    u.email,
                    u.email_verified_at
                FROM email_verification_tokens evt
                JOIN users u ON u.id_user = evt.id_user
                WHERE evt.token_hash = %s
                LIMIT 1
                """,
                (token_hash,),
            )
            return cursor.fetchone()

    def verify_user_email(self, user_id: int, token_id: int) -> dict | None:
        with database.connect() as connection:
            cursor = connection.cursor()
            cursor.execute(
                """
                UPDATE users
                SET email_verified_at = COALESCE(email_verified_at, CURRENT_TIMESTAMP)
                WHERE id_user = %s
                """,
                (user_id,),
            )
            cursor.execute(
                """
                UPDATE email_verification_tokens
                SET consumed_at = CURRENT_TIMESTAMP
                WHERE id_email_verification_token = %s
                """,
                (token_id,),
            )
            cursor.execute(
                """
                SELECT id_user, email, is_active, email_verified_at
                FROM users
                WHERE id_user = %s
                """,
                (user_id,),
            )
            row = cursor.fetchone()

        if row is None:
            return None

        return self._public_user(row)

    def get_latest_verification_token(self, user_id: int) -> dict | None:
        with database.connect() as connection:
            cursor = connection.cursor()
            cursor.execute(
                """
                SELECT id_email_verification_token, id_user, created_at, consumed_at
                FROM email_verification_tokens
                WHERE id_user = %s
                ORDER BY created_at DESC
                LIMIT 1
                """,
                (user_id,),
            )
            return cursor.fetchone()
