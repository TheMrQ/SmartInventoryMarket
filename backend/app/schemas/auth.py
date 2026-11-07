"""Safe public contracts for cookie-session authentication."""

from pydantic import BaseModel, Field, field_validator

from backend.app.db.models import UserRole
from backend.app.services.auth import password_policy_error


class RegisterRequest(BaseModel):
    full_name: str = Field(min_length=2, max_length=255)
    email: str = Field(min_length=3, max_length=255, pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    password: str = Field(min_length=8, max_length=128)

    @field_validator("full_name")
    @classmethod
    def clean_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("must not be blank")
        return value

    @field_validator("password")
    @classmethod
    def validate_password_policy(cls, value: str) -> str:
        if error := password_policy_error(value):
            raise ValueError(error)
        return value


class LoginRequest(BaseModel):
    email: str = Field(min_length=3, max_length=255, pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    password: str = Field(min_length=1, max_length=128)


class UserRead(BaseModel):
    id: int
    full_name: str
    email: str
    role: UserRole
    avatar_url: str | None = None

    model_config = {"from_attributes": True}


class AuthenticatedUser(UserRead):
    csrf_token: str


class ProfileUpdateRequest(BaseModel):
    """The deliberately small, safe surface that an authenticated user may edit."""

    full_name: str = Field(min_length=2, max_length=255)

    model_config = {"extra": "forbid"}

    @field_validator("full_name")
    @classmethod
    def clean_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("must not be blank")
        return value


class PasswordChangeRequest(BaseModel):
    current_password: str = Field(min_length=1, max_length=128)
    new_password: str = Field(min_length=8, max_length=128)

    model_config = {"extra": "forbid"}

    @field_validator("new_password")
    @classmethod
    def validate_password_policy(cls, value: str) -> str:
        if error := password_policy_error(value):
            raise ValueError(error)
        return value
