from pydantic import BaseModel, EmailStr, SecretStr


class AuthRequest(BaseModel):
    """Schema for log in to ERTY API."""

    email: EmailStr
    password: SecretStr


class AuthResponse(BaseModel):
    """Schema for returning a valid login credentials."""

    access_token: str
    token_type: str = "bearer"
