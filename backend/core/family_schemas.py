from datetime import date
from typing import Literal
from pydantic import EmailStr, Field, model_validator
from core.schemas import Schema, Registration


class FamilyInvite(Schema):
    full_name: str = Field(min_length=1, max_length=120)
    email: EmailStr
    module: Literal['adult', 'women']
    relationship: str = Field(default='Family member', min_length=1, max_length=50)

    @model_validator(mode='after')
    def clean(self):
        self.full_name=self.full_name.strip()
        self.relationship=self.relationship.strip()
        self.email=str(self.email).lower()
        if not self.full_name or not self.relationship:raise ValueError('Name and relationship must not be blank')
        return self


class FamilySetup(Registration):
    date_of_birth: date

    @model_validator(mode='after')
    def adult_age(self):
        today=date.today()
        age=today.year-self.date_of_birth.year-((today.month,today.day)<(self.date_of_birth.month,self.date_of_birth.day))
        if not 13<=age<=120:raise ValueError('Adult/women member must be age 13 to 120')
        return self


class FamilyOTP(Schema):
    otp: str = Field(pattern=r'^\d{6}$')
