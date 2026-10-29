from typing import Annotated, Literal
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator
from flask import request
from core.errors import APIError

Password = Annotated[str, Field(min_length=8, max_length=128)]


class Schema(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=False)


class Registration(Schema):
    full_name: str = Field(min_length=1, max_length=120)
    email: EmailStr
    mobile_number: str = Field(pattern=r'^\+?[1-9][0-9]{7,14}$')
    password: Password
    confirm_password: Password

    @field_validator('full_name')
    @classmethod
    def name(cls, value):
        if not value.strip():
            raise ValueError('Name required')
        return value.strip()

    @field_validator('email')
    @classmethod
    def normalize_email(cls, value):
        return str(value).lower()

    @model_validator(mode='after')
    def matches(self):
        if self.password != self.confirm_password:
            raise ValueError('Passwords do not match')
        return self


class PatientRegistration(Registration):
    referral_id: str | None = Field(default=None, min_length=1, max_length=160, pattern=r'^[A-Za-z0-9]+$')


class ConnectDoctor(Schema):
    referral_id: str = Field(min_length=1, max_length=160, pattern=r'^[A-Za-z0-9]+$')


class DoctorRegistration(Registration):
    qualification: str | None = Field(default=None, min_length=2, max_length=200)
    medical_registration_number: str | None = Field(default=None, pattern=r'^[A-Za-z0-9][A-Za-z0-9/ ._-]{1,99}$')
    registering_council: str | None = Field(default=None, min_length=2, max_length=200)
    specialization: str | None = Field(default=None, max_length=200)
    nmr_id: str | None = Field(default=None, min_length=1, max_length=100)

    @field_validator('qualification', 'registering_council', 'medical_registration_number')
    @classmethod
    def nonempty(cls, value):
        if value is None:
            return value
        if len(value.strip()) < 2:
            raise ValueError('Registration details required')
        return value.strip().upper()


class DoctorProfileSetup(Schema):
    setup_token: str = Field(min_length=1, max_length=4096)
    qualification: str = Field(min_length=2, max_length=200)
    medical_registration_number: str = Field(pattern=r'^[A-Za-z0-9][A-Za-z0-9/ ._-]{1,99}$')
    registering_council: str = Field(min_length=2, max_length=200)
    specialization: str | None = Field(default=None, max_length=200)
    nmr_id: str | None = Field(default=None, min_length=1, max_length=100)
    address: str = Field(min_length=5, max_length=1000)
    clinic_address: str = Field(min_length=5, max_length=1000)
    years_of_experience: int = Field(ge=0, le=80, strict=True)

    @field_validator('qualification', 'medical_registration_number', 'registering_council', 'address', 'clinic_address')
    @classmethod
    def clean_required(cls, value, info):
        value = value.strip()
        if len(value) < (5 if info.field_name in ('address', 'clinic_address') else 2):
            raise ValueError('This field is required')
        return value


class Login(Schema):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class SuperLogin(Schema):
    email: EmailStr | None = None
    username: str | None = Field(default=None, min_length=1, max_length=80)
    password: str = Field(min_length=1, max_length=128)

    @model_validator(mode='after')
    def identifier(self):
        if bool(self.email) == bool(self.username):
            raise ValueError('Provide email, or legacy username, but not both')
        return self


class VerifyOTP(Schema):
    challenge_token: str = Field(min_length=1, max_length=4096)
    otp: str = Field(pattern=r'^\d{6}$')


class Challenge(Schema):
    challenge_token: str = Field(min_length=1, max_length=4096)


class ForgotPassword(Schema):
    email: EmailStr


class ResetPassword(VerifyOTP):
    new_password: Password
    confirm_password: Password

    @model_validator(mode='after')
    def matches(self):
        if self.new_password != self.confirm_password:
            raise ValueError('Passwords do not match')
        return self


class ChangePassword(Schema):
    current_password: str = Field(min_length=1, max_length=128)
    new_password: Password
    confirm_password: Password

    @model_validator(mode='after')
    def matches(self):
        if self.new_password != self.confirm_password:
            raise ValueError('Passwords do not match')
        return self


class InitialPassword(ChangePassword):
    challenge_token: str = Field(min_length=1, max_length=4096)


class Rejection(Schema):
    reason: str = Field(min_length=1, max_length=500)


class Resubmission(Schema):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)
    qualification: str = Field(min_length=2, max_length=200)
    medical_registration_number: str = Field(pattern=r'^[A-Za-z0-9][A-Za-z0-9/ ._-]{1,99}$')
    registering_council: str = Field(min_length=2, max_length=200)


def parse(schema):
    data = request.get_json()
    if not isinstance(data, dict):
        raise APIError(400, 'invalid_json', 'JSON object required')
    return schema.model_validate(data)
