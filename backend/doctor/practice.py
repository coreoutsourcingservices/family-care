"""Doctor-owned practice details, separate from verified registration identity."""
from flask import g, jsonify, request
from pydantic import Field, field_validator
from sqlalchemy import select
from core.schemas import Schema, parse
from core.database import db
from core.models import DoctorPracticeProfile, DoctorProfile
from services.repository import audit

class PracticeInput(Schema):
    clinic_name: str = Field(min_length=2, max_length=160)
    city: str = Field(min_length=2, max_length=120)
    address: str = Field(min_length=5, max_length=500)
    experience_years: int = Field(ge=0, le=80)
    languages: list[str] = Field(min_length=1, max_length=15)
    consultation_hours: str = Field(min_length=2, max_length=200)
    bio: str = Field(default='', max_length=1500)

    @field_validator('clinic_name','city','address','consultation_hours')
    @classmethod
    def nonblank(cls, value):
        if not value.strip(): raise ValueError('Value must not be blank')
        return value.strip()

    @field_validator('languages')
    @classmethod
    def clean_languages(cls, values):
        if any(not value.strip() or len(value)>80 for value in values): raise ValueError('Invalid language')
        return list(dict.fromkeys(value.strip() for value in values))

def practice_profile():
    doctor = db().get(DoctorProfile, g.user.id)
    if request.method == 'PUT':
        payload = parse(PracticeInput)
        db().scalar(select(DoctorProfile).where(DoctorProfile.user_id==g.user.id).with_for_update())
        row = db().get(DoctorPracticeProfile,g.user.id)
        if row is None:
            row=DoctorPracticeProfile(user_id=g.user.id)
            db().add(row)
        row.data=payload.model_dump()
        audit('doctor_practice_profile_updated',g.user.id,g.user.id)
        db().commit()
    else:
        row=db().get(DoctorPracticeProfile,g.user.id)
    return jsonify(profile=row.data if row else None, complete=bool(row),
        professional={key:getattr(doctor,key) for key in ('qualification','specialization','medical_registration_number','registering_council','verification_status')})

def get_practice_profile():
    return practice_profile()

def save_practice_profile():
    return practice_profile()
