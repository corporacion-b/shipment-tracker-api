from src.db.connection import database


class UserRepository:
    @staticmethod
    def _public_user(row: dict) -> dict:
        return {
            "id_user": row["id_user"],
            "email": row["email"],
            "is_active": bool(row["is_active"]),
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
                SELECT id_user, email, is_active
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
                SELECT id_user, email, hashed_password, is_active
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
                SELECT id_user, email, is_active
                FROM users
                WHERE id_user = %s
                """,
                (user_id,),
            )
            row = cursor.fetchone()

        if row is None:
            return None

        return self._public_user(row)
