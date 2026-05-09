from fastapi import HTTPException, status

from src.core.security import create_access_token, hash_password, verify_password
from src.repositories.user_repository import UserRepository


class AuthService:
    def __init__(self, repository: UserRepository | None = None):
        self.repository = repository or UserRepository()

    def register_user(self, email: str, password: str) -> dict:
        existing_user = self.repository.get_by_email(email)
        if existing_user is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="El email ya está registrado.",
            )

        return self.repository.create_user(
            email=email,
            hashed_password=hash_password(password),
        )

    def authenticate_user(self, email: str, password: str) -> dict:
        user = self.repository.get_by_email(email)
        if user is None or not verify_password(password, user["hashed_password"]):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Credenciales inválidas.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if not user["is_active"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Usuario inactivo.",
            )

        return user

    @staticmethod
    def create_token_for_user(user: dict) -> str:
        return create_access_token(subject=str(user["id_user"]))
