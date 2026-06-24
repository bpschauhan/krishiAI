from decimal import Decimal
import re

from pydantic import BaseModel, ConfigDict, Field, field_validator

PHONE_PATTERN = re.compile(r"^(?:\+91)?[6-9]\d{9}$")


def _strip_required(value: str) -> str:
    stripped = value.strip()
    if not stripped:
        raise ValueError("Field is required")
    return stripped


def _normalize_phone(value: str) -> str:
    phone = value.strip().replace(" ", "").replace("-", "")
    if not PHONE_PATTERN.fullmatch(phone):
        raise ValueError("Phone number must be a valid Indian mobile number")
    if phone.startswith("+91"):
        return phone[3:]
    return phone


class LanguageRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    name: str


class DistrictRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    state: str


class FarmerCreate(BaseModel):
    full_name: str = Field(min_length=1, max_length=160)
    phone_number: str
    village: str = Field(min_length=1, max_length=160)
    district_id: int = Field(gt=0)
    language_id: int = Field(gt=0)

    @field_validator("full_name", "village")
    @classmethod
    def validate_required_text(cls, value: str) -> str:
        return _strip_required(value)

    @field_validator("phone_number")
    @classmethod
    def validate_phone(cls, value: str) -> str:
        return _normalize_phone(value)


class FarmerRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    full_name: str
    phone_number: str
    village: str
    district_id: int
    language_id: int


class FarmerDetail(FarmerRead):
    district: DistrictRead
    language: LanguageRead
    farm_count: int
    plot_count: int


class FarmCreate(BaseModel):
    farmer_id: int = Field(gt=0)
    district_id: int = Field(gt=0)
    name: str = Field(min_length=1, max_length=160)
    village: str = Field(min_length=1, max_length=160)
    total_acreage: Decimal = Field(gt=0, decimal_places=2)

    @field_validator("name", "village")
    @classmethod
    def validate_required_text(cls, value: str) -> str:
        return _strip_required(value)


class FarmRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    farmer_id: int
    district_id: int
    name: str
    village: str
    total_acreage: Decimal


class PlotCreate(BaseModel):
    farm_id: int = Field(gt=0)
    name: str = Field(min_length=1, max_length=160)
    acreage: Decimal = Field(gt=0, decimal_places=2)
    current_crop: str | None = Field(default=None, max_length=120)

    @field_validator("name")
    @classmethod
    def validate_required_text(cls, value: str) -> str:
        return _strip_required(value)

    @field_validator("current_crop")
    @classmethod
    def validate_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        stripped = value.strip()
        return stripped or None


class PlotRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    farm_id: int
    name: str
    acreage: Decimal
    current_crop: str | None
