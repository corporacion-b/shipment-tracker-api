from fastapi import APIRouter, Depends, status

from src.api.dependencies import get_current_user
from src.schemas.auth import Token, UserCreate, UserLogin, UserRead
from src.services.auth import AuthService


router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post(
    "/register",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar usuario",
)
async def register(user_data: UserCreate):
    return AuthService().register_user(
        email=user_data.email,
        password=user_data.password,
    )


@router.post(
    "/login",
    response_model=Token,
    summary="Iniciar sesión",
)
async def login(credentials: UserLogin):
    user = AuthService().authenticate_user(
        email=credentials.email,
        password=credentials.password,
    )
    access_token = AuthService.create_token_for_user(user)

    return Token(access_token=access_token)


@router.get(
    "/me",
    response_model=UserRead,
    summary="Obtener usuario autenticado",
)
async def get_me(current_user: dict = Depends(get_current_user)):
    return current_user
