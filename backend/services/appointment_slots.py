"""Doctor availability and serialized appointment conflict checks."""
from datetime import datetime,timedelta,timezone
from flask import g,jsonify
from sqlalchemy import select
from pydantic import Field,field_validator
from core.database import db
from core.models import DoctorAvailability,DoctorConsultation,User,now
from core.schemas import Schema,parse
from core.errors import APIError
from core.routing import route
from services.consultation_directory import bp,approved
from services.repository import audit

class SlotInput(Schema):
    starts_at:datetime
    duration_minutes:int=Field(default=30,ge=5,le=240)
    @field_validator('starts_at')
    @classmethod
    def future(cls,value):
        if not value.tzinfo:raise ValueError('Include a timezone')
        value=value.astimezone(timezone.utc).replace(tzinfo=None)
        if value<=now():raise ValueError('Choose a future time')
        return value

def lock_doctor(doctor_id):
    db().scalar(select(User).where(User.id==doctor_id).with_for_update())

def check_conflicts(doctor_id,start,duration,exclude=None):
    end=start+timedelta(minutes=duration)
    rows=db().scalars(select(DoctorConsultation).where(DoctorConsultation.doctor_id==doctor_id,DoctorConsultation.status=='CONFIRMED',DoctorConsultation.id!=exclude,DoctorConsultation.confirmed_at<end))
    if any((row.confirmed_at+timedelta(minutes=row.duration_minutes or 30))>start for row in rows):
        raise APIError(409,'appointment_conflict','This doctor already has an overlapping appointment')

def slot_data(row):return dict(id=row.id,starts_at=row.starts_at.isoformat()+'Z',duration_minutes=row.duration_minutes)

def slots(doctor_id=None):
    doctor_id=str(doctor_id) if doctor_id else g.user.id
    approved(doctor_id)
    rows=db().scalars(select(DoctorAvailability).where(DoctorAvailability.doctor_id==doctor_id,DoctorAvailability.active.is_(True),DoctorAvailability.starts_at>now()).order_by(DoctorAvailability.starts_at).limit(200))
    items=[]
    for row in rows:
        try:check_conflicts(doctor_id,row.starts_at,row.duration_minutes)
        except APIError:continue
        items.append(slot_data(row))
    return jsonify(items=items)

def add_slot():
    value=parse(SlotInput);lock_doctor(g.user.id)
    check_conflicts(g.user.id,value.starts_at,value.duration_minutes)
    existing=db().scalars(select(DoctorAvailability).where(DoctorAvailability.doctor_id==g.user.id,DoctorAvailability.active.is_(True)))
    if any(row.starts_at<value.starts_at+timedelta(minutes=value.duration_minutes) and row.starts_at+timedelta(minutes=row.duration_minutes)>value.starts_at for row in existing):
        raise APIError(409,'slot_conflict','Availability overlaps an existing slot')
    row=DoctorAvailability(doctor_id=g.user.id,starts_at=value.starts_at,duration_minutes=value.duration_minutes)
    db().add(row);audit('appointment_slot_created',actor_id=g.user.id);db().commit();return jsonify(slot=slot_data(row)),201

def remove_slot(slot_id):
    lock_doctor(g.user.id)
    row=db().scalar(select(DoctorAvailability).where(DoctorAvailability.id==str(slot_id),DoctorAvailability.doctor_id==g.user.id).with_for_update())
    if not row:raise APIError(404,'slot_not_found','Availability not found')
    check_conflicts(g.user.id,row.starts_at,row.duration_minutes)
    row.active=False;audit('appointment_slot_removed',actor_id=g.user.id);db().commit();return jsonify(message='Availability removed')

route(bp,'/doctors/appointment-slots',slots,roles=('DOCTOR',))
route(bp,'/doctors/appointment-slots',add_slot,'POST',roles=('DOCTOR',))
route(bp,'/doctors/appointment-slots/<uuid:slot_id>',remove_slot,'DELETE',roles=('DOCTOR',))
def patient_slots(doctor_id):return slots(doctor_id)
route(bp,'/patients/doctor-directory/<uuid:doctor_id>/slots',patient_slots,roles=('PATIENT',))
