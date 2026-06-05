from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm

from src.api.dependencies import get_current_user
from src.schemas.auth import (
    AuthMessage,
    EmailVerificationRequest,
    ResendVerificationRequest,
    Token,
    UserCreate,
    UserRead,
    UserRegistrationRead,
)
from src.services.auth import AuthService


router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post(
    "/register",
    response_model=UserRegistrationRead,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar usuario",
)
async def register(user_data: UserCreate):
    return AuthService().send_initial_verification(
        email=user_data.email,
        password=user_data.password,
    )


@router.post(
    "/login",
    response_model=Token,
    summary="Iniciar sesión",
)
async def login(credentials: OAuth2PasswordRequestForm = Depends()):
    user = AuthService().authenticate_user(
        email=credentials.username,
        password=credentials.password,
    )
    access_token = AuthService.create_token_for_user(user)

    return Token(access_token=access_token)


@router.post(
    "/verify-email",
    response_model=AuthMessage,
    summary="Verificar correo",
)
async def verify_email(payload: EmailVerificationRequest):
    return AuthService().verify_email(payload.token)


@router.post(
    "/resend-verification",
    response_model=AuthMessage,
    summary="Reenviar verificacion de correo",
)
async def resend_verification(payload: ResendVerificationRequest):
    return AuthService().resend_verification(payload.email)


@router.get(
    "/me",
    response_model=UserRead,
    summary="Obtener usuario autenticado",
)
async def get_me(current_user: dict = Depends(get_current_user)):
    return current_user
