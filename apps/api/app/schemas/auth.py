import re

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

PHONE_PATTERN = re.compile(r"^(?:\+91)?[6-9]\d{9}$")


def _empty_to_none(value: str | None) -> str | None:
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None


def _normalize_phone(value: str | None) -> str | None:
    phone = _empty_to_none(value)
    if phone is None:
        return None
    normalized = phone.replace(" ", "").replace("-", "")
    if not PHONE_PATTERN.fullmatch(normalized):
        raise ValueError("Phone number must be a valid Indian mobile number")
    if normalized.startswith("+91"):
        return normalized[3:]
    return normalized


class RoleRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    slug: str
    name: str
    description: str | None = None


class PermissionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    slug: str
    name: str
    description: str | None = None


class UserProfileRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    display_name: str | None = None
    phone_number: str | None = None
    preferred_language: str | None = None
    district: str | None = None
    village: str | None = None


class UserRead(BaseModel):
    id: int
    clerk_user_id: str
    email: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    is_active: bool
    profile: UserProfileRead | None = None
    roles: list[RoleRead]
    permissions: list[PermissionRead]


class AuthSyncRequest(BaseModel):
    email: EmailStr | None = None
    first_name: str | None = Field(default=None, max_length=120)
    last_name: str | None = Field(default=None, max_length=120)
    display_name: str | None = Field(default=None, max_length=160)
    phone_number: str | None = None

    @field_validator("first_name", "last_name", "display_name")
    @classmethod
    def validate_optional_text(cls, value: str | None) -> str | None:
        return _empty_to_none(value)

    @field_validator("phone_number")
    @classmethod
    def validate_phone(cls, value: str | None) -> str | None:
        return _normalize_phone(value)


class UserProfileUpdate(BaseModel):
    first_name: str | None = Field(default=None, max_length=120)
    last_name: str | None = Field(default=None, max_length=120)
    display_name: str | None = Field(default=None, max_length=160)
    phone_number: str | None = None
    preferred_language: str | None = Field(default=None, max_length=32)
    district: str | None = Field(default=None, max_length=120)
    village: str | None = Field(default=None, max_length=160)

    @field_validator("first_name", "last_name", "display_name", "preferred_language", "district", "village")
    @classmethod
    def validate_optional_text(cls, value: str | None) -> str | None:
        return _empty_to_none(value)

    @field_validator("phone_number")
    @classmethod
    def validate_phone(cls, value: str | None) -> str | None:
        return _normalize_phone(value)
