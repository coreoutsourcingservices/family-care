"""Account-owned adult health logs. Values are reported, not diagnoses."""
from datetime import date
from typing import Literal
from flask import Blueprint, g, jsonify
from pydantic import Field, model_validator
from sqlalchemy import select
from core.models import AdultRecord, AdultRecordRevision, now
from core.database import db
from core.routing import route
from core.schemas import Schema, parse
from core.errors import APIError
from services.care import accessible_profile

bp = Blueprint('adults', __name__, url_prefix='/api/v1/patients/adults')

class AdultInput(Schema):
    kind: Literal['bp','glucose','lipids','medicine','lifestyle','screening','history','consultation_request','reminder']
    title: str = Field(min_length=1, max_length=160)
    date: date
    notes: str = Field(default='', max_length=2000)
    status: Literal['Recorded','Planned','Completed'] = 'Recorded'
    systolic: float | None = Field(default=None, gt=0, le=400)
    diastolic: float | None = Field(default=None, gt=0, le=300)
    pulse: float | None = Field(default=None, gt=0, le=350)
    glucose: float | None = Field(default=None, gt=0, le=2000)
    total: float | None = Field(default=None, gt=0, le=3000)
    ldl: float | None = Field(default=None, gt=0, le=3000)
    hdl: float | None = Field(default=None, gt=0, le=1000)
    triglycerides: float | None = Field(default=None, gt=0, le=5000)
    minutes: float | None = Field(default=None, ge=0, le=1440)
    context: str = Field(default='', max_length=160)

    version: str|None = Field(default=None,max_length=40)
    arm: Literal['','Left','Right'] = ''
    position: Literal['','Seated','Standing','Lying'] = ''
    measurement_time: str = Field(default='',pattern=r'^(?:[0-2][0-9]:[0-5][0-9])?$')
    reading_context: Literal['','Fasting','Pre-meal','Post-meal','Random'] = ''
    units: Literal['mg/dL','mmol/L']|None = None
    meal_minutes: int|None = Field(default=None,ge=0,le=1440)
    strength: str = Field(default='',max_length=100)
    dose: str = Field(default='',max_length=100)
    frequency: str = Field(default='',max_length=160)
    start_date: date|None = None
    end_date: date|None = None
    adherence: Literal['','Taken','Missed','Not recorded'] = ''
    follow_up: date|None = None
    result_status: Literal['','Scheduled','Completed','Result received','Follow-up required'] = ''
    history_type: Literal['','Condition','Allergy','Procedure','Hospitalization','Family history'] = ''
    sleep_hours: float|None = Field(default=None,ge=0,le=24)
    report_id: str|None = Field(default=None,max_length=36)

    @model_validator(mode='after')
    def validate_values(self):
        from patient.child_routes import today
        self.title = self.title.strip()
        if not self.title:
            raise ValueError('Enter a title')
        required = {'bp': ('systolic','diastolic'), 'glucose': ('glucose',), 'lipids': ('total',)}
        if any(getattr(self, key) is None for key in required.get(self.kind, ())):
            raise ValueError('Enter the required measurements')
        if self.kind in ('bp','glucose','lipids','lifestyle','history') and self.date > today():
            raise ValueError('Recorded measurements cannot be in the future')
        if self.kind=='bp' and self.systolic<=self.diastolic:raise ValueError('Systolic must be greater than diastolic')
        if self.start_date and self.end_date and self.end_date<self.start_date:raise ValueError('End date cannot precede start date')
        if self.measurement_time and int(self.measurement_time[:2])>23:raise ValueError('Choose a valid measurement time')
        if self.kind=='glucose':self.units=self.units or 'mg/dL'
        elif self.units is not None:raise ValueError('Units selection applies to glucose records only')
        return self

def profile(profile_id):
    row = accessible_profile(g.user, str(profile_id))
    # Existing child profiles age into this workspace without losing their reports.
    age = date.today().year-row.dob.year-((date.today().month,date.today().day)<(row.dob.month,row.dob.day))
    if row.module != 'adult' and not (row.module == 'child' and age > 12):
        raise APIError(404, 'adult_not_found', 'Adult profile not found')
    return row

def data(row):
    from services.personal_reminders import delivery
    extra={'delivery_status':delivery('adult',row,g.user.id)} if row.kind=='reminder' else {}
    return dict(row.data,**extra, id=row.id, kind=row.kind, version=row.updated_at.isoformat(), verification_status='SELF_REPORTED')

def listing(profile_id):
    owner = profile(profile_id)
    rows = db().scalars(select(AdultRecord).where(AdultRecord.profile_id==owner.id, AdultRecord.deleted_at.is_(None)).order_by(AdultRecord.created_at.desc(), AdultRecord.id)).all()
    return jsonify(items=[data(row) for row in rows])

def save(profile_id, record_id=None):
    owner = profile(profile_id)
    payload = parse(AdultInput)
    if payload.date < owner.dob:
        raise APIError(422,'invalid_date','Record date cannot be before birth')
    row = None
    if record_id:
        row = db().scalar(select(AdultRecord).where(AdultRecord.id==str(record_id),AdultRecord.profile_id==owner.id,AdultRecord.deleted_at.is_(None)).with_for_update())
        if row is None:
            raise APIError(404,'record_not_found','Record not found')
        if payload.version and payload.version!=row.updated_at.isoformat():raise APIError(409,'record_conflict','This record changed. Refresh before editing')
        if row.kind != payload.kind:
            raise APIError(422,'invalid_kind','Record type cannot be changed')
    if payload.kind=='consultation_request' and not owner.referred_doctor_id:
        raise APIError(409,'doctor_required','Connect a doctor before requesting a consultation')
    created = row is None
    if created:
        row=AdultRecord(profile_id=owner.id,kind=payload.kind)
        db().add(row)
    if payload.report_id:
        from core.models import CareReport
        report=db().get(CareReport,payload.report_id)
        if not report or report.profile_id!=owner.id or report.deleted_at:raise APIError(422,'invalid_report','Choose a report from this profile')
    row.data=payload.model_dump(mode='json',exclude={'version'})
    db().flush()
    db().add(AdultRecordRevision(record_id=row.id,actor_id=g.user.id,action='created' if created else 'updated',data=row.data))
    if created and payload.kind=='consultation_request':
        from doctor.notifications import queue_notification
        queue_notification(owner.referred_doctor_id,'consultation_requested','adult-consultation:'+row.id)
    db().commit()
    return jsonify(record=data(row)), 201 if created else 200

def remove(profile_id, record_id):
    owner=profile(profile_id)
    row=db().scalar(select(AdultRecord).where(AdultRecord.id==str(record_id),AdultRecord.profile_id==owner.id,AdultRecord.deleted_at.is_(None)).with_for_update())
    if row is None:
        raise APIError(404,'record_not_found','Record not found')
    row.deleted_at=now()
    from services.recycle_bin import retain
    retain('adult_record',row,profile_id=row.profile_id)
    db().add(AdultRecordRevision(record_id=row.id,actor_id=g.user.id,action='deleted',data=row.data))
    db().commit()
    return jsonify(message='Record removed')

def update(profile_id,record_id):
    return save(profile_id,record_id)

route(bp,'/<uuid:profile_id>/records',listing,roles=('PATIENT',))
route(bp,'/<uuid:profile_id>/records',save,method='POST',roles=('PATIENT',),schema=AdultInput)
route(bp,'/<uuid:profile_id>/records/<uuid:record_id>',update,method='POST',roles=('PATIENT',),schema=AdultInput)
route(bp,'/<uuid:profile_id>/records/<uuid:record_id>/delete',remove,method='POST',roles=('PATIENT',))
def get_record(profile_id,record_id):
    owner=profile(profile_id)
    row=db().scalar(select(AdultRecord).where(AdultRecord.id==str(record_id),AdultRecord.profile_id==owner.id,AdultRecord.deleted_at.is_(None)))
    if row is None:raise APIError(404,'record_not_found','Record not found')
    return jsonify(record=data(row))
def patch_record(profile_id,record_id):return update(profile_id,record_id)
def delete_record(profile_id,record_id):return remove(profile_id,record_id)
route(bp,'/<uuid:profile_id>/records/<uuid:record_id>',get_record,roles=('PATIENT',))
route(bp,'/<uuid:profile_id>/records/<uuid:record_id>',patch_record,method='PATCH',roles=('PATIENT',),schema=AdultInput)
route(bp,'/<uuid:profile_id>/records/<uuid:record_id>',delete_record,method='DELETE',roles=('PATIENT',))
