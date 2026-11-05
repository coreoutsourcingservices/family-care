"""Versioned doctor-authored prescriptions; issued documents are immutable."""
from datetime import date
from typing import Literal
from flask import Blueprint,g,jsonify
from sqlalchemy import select
from pydantic import Field,model_validator
from core.database import db
from core.models import CareProfile,DoctorPrescription,DoctorProfile,User,now
from core.errors import APIError
from core.schemas import Schema,parse
from core.routing import route
from services.repository import audit

bp=Blueprint('prescriptions',__name__,url_prefix='/api/v1')

def access(profile_id,edit=False):
    profile=db().get(CareProfile,str(profile_id))
    if not profile or profile.deleted_at:raise APIError(404,'profile_not_found','Profile not found')
    if profile.module=='women':
        from services.women_workspace import get_profile
        profile,_=get_profile(profile.id,'records',edit=edit)
    elif profile.module=='adult':
        from services.adult_workspace import profile as adult_profile
        profile,_=adult_profile(profile.id,'reports',edit=edit)
    else:
        from services.care import accessible_profile
        profile=accessible_profile(g.user,profile.id,lock=True)
    return profile

class Medicine(Schema):
    name:str=Field(min_length=1,max_length=160)
    strength:str=Field(min_length=1,max_length=80)
    dose:str=Field(min_length=1,max_length=80)
    frequency:str=Field(min_length=1,max_length=120)
    duration:str=Field(min_length=1,max_length=120)
    instructions:str=Field(default='',max_length=500)

class Draft(Schema):
    medicines:list[Medicine]=Field(min_length=1,max_length=30)
    instructions:str=Field(default='',max_length=3000)
    follow_up:date|None=None
    version:int=Field(default=0,ge=0)
    @model_validator(mode='after')
    def valid(self):
        for medicine in self.medicines:
            if any(not getattr(medicine,k).strip() for k in ('name','strength','dose','frequency','duration')):
                raise ValueError('Complete every medicine field')
        if self.follow_up and self.follow_up<now().date():raise ValueError('Follow-up cannot be in the past')
        return self

def serialize(row):
    doctor=db().get(User,row.doctor_id)
    return dict(id=row.id,profile_id=row.profile_id,doctor_id=row.doctor_id,doctor_name=doctor.full_name,
                status=row.status,version=row.version,data=row.data,void_reason=row.void_reason,
                issued_at=row.issued_at.isoformat()+'Z' if row.issued_at else None,
                created_at=row.created_at.isoformat()+'Z')

def listing(profile_id):
    profile=access(profile_id)
    query=select(DoctorPrescription).where(DoctorPrescription.profile_id==profile.id)
    if g.user.role=='DOCTOR':query=query.where(DoctorPrescription.doctor_id==g.user.id)
    else:query=query.where(DoctorPrescription.status!='DRAFT')
    return jsonify(items=[serialize(row) for row in db().scalars(query.order_by(DoctorPrescription.created_at.desc()))])

def save(profile_id,prescription_id=None):
    profile=access(profile_id,edit=True);value=parse(Draft)
    row=None
    if prescription_id:
        row=db().scalar(select(DoctorPrescription).where(DoctorPrescription.id==str(prescription_id),DoctorPrescription.profile_id==profile.id,DoctorPrescription.doctor_id==g.user.id).with_for_update())
        if not row:raise APIError(404,'prescription_not_found','Prescription not found')
        if row.status!='DRAFT' or row.version!=value.version:raise APIError(409,'prescription_conflict','Only the latest draft can be edited')
    elif value.version:raise APIError(409,'prescription_conflict','New drafts start at version zero')
    if row is None:
        row=DoctorPrescription(profile_id=profile.id,doctor_id=g.user.id,version=0)
        db().add(row)
    row.data=value.model_dump(mode='json',exclude={'version'});row.version+=1
    audit('prescription_draft_saved',profile.owner_id,g.user.id);db().commit()
    return jsonify(prescription=serialize(row))

def update(profile_id,prescription_id):return save(profile_id,prescription_id)

class Decision(Schema):
    action:Literal['ISSUE','VOID']
    version:int=Field(ge=1)
    attestation:Literal[True]
    reason:str=Field(default='',max_length=1000)

def decide(profile_id,prescription_id):
    profile=access(profile_id,edit=True);value=parse(Decision)
    row=db().scalar(select(DoctorPrescription).where(DoctorPrescription.id==str(prescription_id),DoctorPrescription.profile_id==profile.id,DoctorPrescription.doctor_id==g.user.id).with_for_update())
    if not row:raise APIError(404,'prescription_not_found','Prescription not found')
    if row.version!=value.version:raise APIError(409,'prescription_conflict','Prescription changed. Refresh before continuing')
    if value.action=='ISSUE':
        if row.status!='DRAFT':raise APIError(409,'invalid_status','Only a draft can be issued')
        clinician=db().get(DoctorProfile,g.user.id)
        if not clinician or not clinician.medical_registration_number:raise APIError(409,'registration_required','Complete professional registration before issuing')
        row.data={**row.data,'issuer':dict(name=g.user.full_name,registration=clinician.medical_registration_number),'patient':dict(name=profile.name,dob=profile.dob.isoformat())}
        row.status='ISSUED';row.issued_at=now()
    else:
        if row.status!='ISSUED' or not value.reason.strip():raise APIError(409,'reason_required','Only issued prescriptions can be voided, with a reason')
        row.status='VOID';row.void_reason=value.reason.strip()
    row.version+=1;audit('prescription_'+row.status.lower(),profile.owner_id,g.user.id);db().commit()
    return jsonify(prescription=serialize(row))

def patient_listing(profile_id):return listing(profile_id)
route(bp,'/doctors/care-profiles/<uuid:profile_id>/prescriptions',listing,roles=('DOCTOR',))
route(bp,'/patients/profiles/<uuid:profile_id>/prescriptions',patient_listing,roles=('PATIENT',))
route(bp,'/doctors/care-profiles/<uuid:profile_id>/prescriptions',save,'POST',roles=('DOCTOR',))
route(bp,'/doctors/care-profiles/<uuid:profile_id>/prescriptions/<uuid:prescription_id>',update,'PUT',roles=('DOCTOR',))
route(bp,'/doctors/care-profiles/<uuid:profile_id>/prescriptions/<uuid:prescription_id>/decision',decide,'POST',roles=('DOCTOR',))
