from pydantic import BaseModel, EmailStr, Field


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)


class UserRead(BaseModel):
    id_user: int
    email: EmailStr
    is_active: bool
    email_verified: bool


class UserRegistrationRead(UserRead):
    message: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class EmailVerificationRequest(BaseModel):
    token: str = Field(..., min_length=20)


class ResendVerificationRequest(BaseModel):
    email: EmailStr


class AuthMessage(BaseModel):
    message: str
