from datetime import date
import re
from typing import Literal
from pydantic import EmailStr, Field, model_validator
from core.schemas import Schema, Registration


class FamilyInvite(Schema):
    full_name: str = Field(min_length=1, max_length=120)
    email: EmailStr
    module: Literal['adult', 'women']
    relationship: str = Field(default='Family member', max_length=50)

    @model_validator(mode='after')
    def clean(self):
        self.full_name=self.full_name.strip()
        self.relationship=self.relationship.strip() or 'Family member'
        self.email=str(self.email).lower()
        if not self.full_name:raise ValueError('Name must not be blank')
        if self.module=='women' and re.search(r'\b(?:boy|boyfriend|man|male|father|dad|brother|son|husband|uncle|grandfather)\b',self.relationship,re.I):
            raise ValueError("Enter a valid relationship for Women's Health")
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
