from datetime import date
from typing import Literal
from uuid import UUID
from pydantic import Field, field_validator, model_validator
from core.schemas import Schema


class EmergencyContact(Schema):
    name: str = Field(min_length=1, max_length=120)
    mobile_number: str = Field(pattern=r'^\+?[1-9][0-9]{7,14}$')
    relationship: str = Field(min_length=1, max_length=50)


class CareProfileCreate(Schema):
    profile_type: Literal['self', 'member']
    module: Literal['child', 'adult', 'women']
    full_name: str = Field(min_length=1, max_length=120)
    date_of_birth: date
    parent_profile_id: UUID | None = None
    guardian_name: str = Field(default='', max_length=120)
    guardian_contact: str = Field(default='', max_length=20, pattern=r'^(?:\+?[1-9][0-9]{7,14})?$')
    emergency_contacts: list[EmergencyContact] = Field(default_factory=list, max_length=5)
    referral_id: str | None = Field(default=None, min_length=1, max_length=160, pattern=r'^[A-Za-z0-9]+$')

    @field_validator('full_name')
    @classmethod
    def nonempty_name(cls, value):
        if not value.strip():
            raise ValueError('Name required')
        return value.strip()

    @field_validator('date_of_birth')
    @classmethod
    def valid_birth_date(cls, value):
        if value > date.today():
            raise ValueError('Birth date cannot be in the future')
        return value

    @model_validator(mode='after')
    def parent_option(self):
        if self.parent_profile_id and (self.module != 'child' or self.profile_type != 'member'):
            raise ValueError('Parent connection is only available for child members')
        return self


class CareProfileReferral(Schema):
    referral_id: str = Field(min_length=1, max_length=160, pattern=r'^[A-Za-z0-9]+$')


class CareProfileUpdate(Schema):
    full_name: str = Field(min_length=1, max_length=120)
    date_of_birth: date
    guardian_name: str = Field(default='', max_length=120)
    guardian_contact: str = Field(default='', max_length=20, pattern=r'^(?:\+?[1-9][0-9]{7,14})?$')
    emergency_contacts: list[EmergencyContact] = Field(default_factory=list, max_length=5)

    @model_validator(mode='after')
    def valid(self):
        self.full_name=self.full_name.strip()
        if not self.full_name or self.date_of_birth>date.today():
            raise ValueError('Enter a name and a birth date that is not in the future')
        return self
