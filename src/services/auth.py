from datetime import datetime, timedelta, timezone
import hashlib
import secrets
from urllib.parse import quote

from fastapi import HTTPException, status

from src.core.config import settings
from src.core.security import create_access_token, hash_password, verify_password
from src.repositories.user_repository import UserRepository
from src.services.email import BrevoEmailService, EmailDeliveryError


class AuthService:
    def __init__(
        self,
        repository: UserRepository | None = None,
        email_service: BrevoEmailService | None = None,
    ):
        self.repository = repository or UserRepository()
        self.email_service = email_service or BrevoEmailService()

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
        ) | {
            "message": "Cuenta creada. Revisa tu correo para verificarla.",
        }

    def send_initial_verification(self, email: str, password: str) -> dict:
        self._ensure_email_configured()
        user = self.register_user(email=email, password=password)
        self._create_and_send_verification(user["id_user"], user["email"])
        return user

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

        if user["email_verified_at"] is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Debes verificar tu correo antes de iniciar sesion.",
            )

        return user

    def verify_email(self, token: str) -> dict:
        token_record = self.repository.get_email_verification_token(
            self._hash_token(token)
        )
        if token_record is None or token_record["consumed_at"] is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El enlace de verificacion no es valido.",
            )

        if token_record["expires_at"] <= self._utc_now():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El enlace de verificacion ha expirado.",
            )

        self.repository.verify_user_email(
            user_id=token_record["id_user"],
            token_id=token_record["id_email_verification_token"],
        )
        return {"message": "Correo verificado correctamente."}

    def resend_verification(self, email: str) -> dict:
        generic_response = {
            "message": "Si el correo existe y requiere verificacion, enviaremos un nuevo enlace.",
        }
        user = self.repository.get_by_email(email)
        if user is None or user["email_verified_at"] is not None:
            return generic_response

        self._ensure_email_configured()
        latest_token = self.repository.get_latest_verification_token(user["id_user"])
        if latest_token is not None:
            elapsed = (self._utc_now() - latest_token["created_at"]).total_seconds()
            if elapsed < settings.EMAIL_VERIFICATION_RESEND_COOLDOWN_SECONDS:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Espera antes de solicitar otro correo de verificacion.",
                )

        self._create_and_send_verification(user["id_user"], user["email"])
        return generic_response

    @staticmethod
    def create_token_for_user(user: dict) -> str:
        return create_access_token(subject=str(user["id_user"]))

    def _create_and_send_verification(self, user_id: int, email: str) -> None:
        raw_token = secrets.token_urlsafe(32)
        expires_at = self._utc_now() + timedelta(
            minutes=settings.EMAIL_VERIFICATION_TOKEN_EXPIRE_MINUTES
        )
        self.repository.create_email_verification_token(
            user_id=user_id,
            token_hash=self._hash_token(raw_token),
            expires_at=expires_at,
        )
        verification_url = self._verification_url(raw_token)

        try:
            self.email_service.send_verification_email(email, verification_url)
        except EmailDeliveryError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="No se pudo enviar el correo de verificacion.",
            ) from exc

    @staticmethod
    def _ensure_email_configured() -> None:
        if settings.BREVO_API_KEY and settings.BREVO_SENDER_EMAIL:
            return

        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="El servicio de correo no esta configurado.",
        )

    @staticmethod
    def _hash_token(token: str) -> str:
        return hashlib.sha256(token.encode("utf-8")).hexdigest()

    @staticmethod
    def _verification_url(token: str) -> str:
        base_url = settings.FRONTEND_BASE_URL.rstrip("/")
        return f"{base_url}/verify-email?token={quote(token)}"

    @staticmethod
    def _utc_now() -> datetime:
        return datetime.now(timezone.utc).replace(tzinfo=None)
