from datetime import date
from typing import Literal
from uuid import UUID
from pydantic import Field, HttpUrl, field_validator, model_validator
from core.schemas import Schema


class VaccineInput(Schema):
    code: str = Field(pattern=r'^[A-Z0-9][A-Z0-9_-]{0,39}$')
    name_en: str = Field(min_length=1, max_length=160)
    name_hi: str = Field(default='', max_length=160)
    category: Literal['Government','Optional']
    protects_against: str = Field(min_length=1, max_length=500)
    description_en: str = Field(default='', max_length=2000)
    description_hi: str = Field(default='', max_length=2000)
    active: bool = True

    @field_validator('name_en','protects_against')
    @classmethod
    def nonblank(cls, value):
        if not value.strip():
            raise ValueError('Field cannot be blank')
        return value.strip()


class EligibilityInput(Schema):
    gender: Literal['All','Girls','Boys'] = 'All'
    country: Literal['IN'] = 'IN'
    states: list[str] = Field(default_factory=list, max_length=40)
    districts: list[str] = Field(default_factory=list, max_length=200)
    programme: str = Field(default='', max_length=160)
    requires_clinical_review: bool = True
    active: bool = True

    @field_validator('states','districts')
    @classmethod
    def locations(cls, values):
        if any(not value.strip() or len(value)>120 for value in values):
            raise ValueError('Invalid location')
        return sorted(set(value.strip() for value in values))

    @model_validator(mode='after')
    def district_state(self):
        if self.districts and len(self.states)!=1:
            raise ValueError('District rules require exactly one state to avoid ambiguous district names')
        return self


class ReminderInput(Schema):
    before_days: list[int] = Field(default_factory=lambda:[7], max_length=12)
    on_due: bool = True
    overdue_days: list[int] = Field(default_factory=lambda:[7], max_length=12)
    language: Literal['en','hi'] = 'en'
    in_app: bool = True
    email: bool = False
    enabled: bool = True

    @field_validator('before_days','overdue_days')
    @classmethod
    def offsets(cls, values):
        if any(value<1 or value>365 for value in values):
            raise ValueError('Reminder offsets must be 1–365 days')
        return sorted(set(values))


class ScheduleInput(Schema):
    vaccine_id: UUID
    schedule_type: Literal['UIP','IAP']
    dose_code: str = Field(pattern=r'^[A-Z0-9][A-Z0-9_-]{0,39}$')
    dose_name: str = Field(min_length=1, max_length=120)
    version: str = Field(min_length=1, max_length=80)
    age_label: str = Field(min_length=1, max_length=160)
    age_unit: Literal['days','weeks','months','years']
    age_start: int = Field(ge=0, le=10000)
    age_end: int = Field(ge=0, le=10000)
    minimum_age: int | None = Field(default=None, ge=0, le=10000)
    maximum_age: int | None = Field(default=None, ge=0, le=10000)
    previous_dose_code: str = Field(default='', max_length=40, pattern=r'^(?:[A-Z0-9][A-Z0-9_-]{0,39})?$')
    minimum_interval_days: int | None = Field(default=None, ge=1, le=3650)
    route: Literal['Oral','IM','ID','SC','Other']
    injection_site: str = Field(default='', max_length=160)
    instructions: str = Field(default='', max_length=2000)
    source_url: HttpUrl
    source_reference: str = Field(min_length=1, max_length=500)
    effective_from: date
    effective_to: date | None = None
    eligibility: EligibilityInput = Field(default_factory=EligibilityInput)
    reminders: ReminderInput = Field(default_factory=ReminderInput)

    @model_validator(mode='after')
    def coherent(self):
        if self.source_url.scheme!='https':
            raise ValueError('An HTTPS source URL is required')
        if any(not value.strip() for value in (self.dose_name,self.version,self.age_label,self.source_reference)):
            raise ValueError('Required fields cannot be blank')
        if self.age_end<self.age_start or (self.minimum_age is not None and self.minimum_age>self.age_start) or (self.maximum_age is not None and self.maximum_age<self.age_end):
            raise ValueError('Age windows must fit the specified minimum/maximum ages')
        if self.effective_to and self.effective_to<self.effective_from:
            raise ValueError('Invalid effective date range')
        if bool(self.previous_dose_code)!=bool(self.minimum_interval_days):
            raise ValueError('Previous dose and minimum interval must be supplied together')
        if self.previous_dose_code==self.dose_code:
            raise ValueError('A dose cannot depend on itself')
        if self.age_unit=='years' and self.age_end>18 or self.age_unit=='months' and self.age_end>216 or self.age_unit=='weeks' and self.age_end>940 or self.age_unit=='days' and self.age_end>6575:
            raise ValueError('Child schedules support age windows through 18 years')
        return self


class AssignReview(Schema):
    reviewer_id: UUID


class MedicalReview(Schema):
    decision: Literal['APPROVE','REJECT']
    notes: str = Field(min_length=20, max_length=2000)
    attestation: bool

    @field_validator('notes')
    @classmethod
    def substantive_notes(cls,value):
        if len(value.strip())<20:raise ValueError('Enter at least 20 characters of review notes')
        return value.strip()


class RetireInput(Schema):
    reason: str = Field(min_length=10, max_length=1000)


class ChildContextInput(Schema):
    country: Literal['IN']
    state: str = Field(default='', max_length=120)
    district: str = Field(default='', max_length=120)
    gender: Literal['Unknown','Girls','Boys'] = 'Unknown'
    history_status: Literal['UNKNOWN','PARENT_REPORTED'] = 'UNKNOWN'
    email_reminders: bool = False

    @field_validator('state','district')
    @classmethod
    def trim_location(cls,value):
        return value.strip()
