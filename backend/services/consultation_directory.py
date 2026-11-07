"""Approved-doctor discovery, explicit consultation requests and completed-visit reviews."""
from datetime import datetime,timezone
from uuid import UUID
from typing import Literal
from flask import Blueprint,g,jsonify,request
from pydantic import Field,field_validator
from sqlalchemy import select,func,or_
from core.database import db
from core.models import User,DoctorProfile,DoctorConsultation,DoctorReview,CareProfile,now
from core.routing import route
from core.schemas import Schema,parse
from core.errors import APIError
from services.repository import audit

bp=Blueprint('consultation_directory',__name__,url_prefix='/api/v1')


def approved(doctor_id):
    row=db().scalar(select(User).where(User.id==str(doctor_id),User.role=='DOCTOR',User.email_verified.is_(True),User.account_status=='ACTIVE',User.approval_status=='APPROVED'))
    if not row or not db().get(DoctorProfile,row.id):raise APIError(404,'doctor_not_found','Approved doctor not found')
    return row


def primary(profile_id):
    from services.care import accessible_profile
    from services.women_workspace import is_primary
    row=accessible_profile(g.user,str(profile_id))
    if row.module not in ('child','adult','women') or not is_primary(g.user,row):raise APIError(403,'owner_required','Only the profile owner can request consultations')
    return row


def directory():
    search=request.args.get('search','').strip()[:120]
    try:page=int(request.args.get('page',1));size=int(request.args.get('per_page',12))
    except ValueError:raise APIError(422,'invalid_pagination','Invalid pagination')
    if page<1 or not 1<=size<=50:raise APIError(422,'invalid_pagination','Invalid pagination')
    ratings=select(DoctorReview.doctor_id,func.avg(DoctorReview.rating).label('rating'),func.count().label('reviews')).group_by(DoctorReview.doctor_id).subquery()
    query=select(User,DoctorProfile,ratings.c.rating,ratings.c.reviews).join(DoctorProfile,DoctorProfile.user_id==User.id).outerjoin(ratings,ratings.c.doctor_id==User.id).where(User.role=='DOCTOR',User.approval_status=='APPROVED',User.account_status=='ACTIVE',User.email_verified.is_(True))
    if search:
        query=query.where((User.full_name.ilike('%'+search+'%'))|(DoctorProfile.specialization.ilike('%'+search+'%')))
    elif request.args.get('module') == 'women':
        concern = request.args.get('concern', '')
        terms = ['gynec', 'gynaec', 'obstet', "women", 'reproductive']
        if concern == 'PCOS & hormonal':
            terms += ['endocrin']
        elif concern == 'Fertility & conception':
            terms += ['fertility', 'ivf', 'androlog']
        elif concern in ("Women's wellness", 'Other concern'):
            terms += ['general medicine', 'family medicine', 'internal medicine', 'general physician']
        query = query.where(or_(*(DoctorProfile.specialization.ilike('%'+term+'%') for term in terms)))
    total=db().scalar(select(func.count()).select_from(query.subquery()))
    rows=db().execute(query.order_by(func.coalesce(ratings.c.rating,0).desc(),func.coalesce(ratings.c.reviews,0).desc(),func.coalesce(DoctorProfile.years_of_experience,0).desc(),User.full_name,User.id).offset((page-1)*size).limit(size))
    from doctor.onboarding_images import photo_details
    return jsonify(items=[dict(id=u.id,name=u.full_name,public_id=u.public_id,referral_id=d.referral_id,consultation_options=d.consultation_options,specialization=d.specialization,qualification=d.qualification,experience=d.years_of_experience or 0,photo=photo_details(d),rating=round(float(rating),2) if rating is not None else None,review_count=count or 0) for u,d,rating,count in rows],total=total,page=page,per_page=size)


class ConsultationInput(Schema):
    doctor_id: UUID
    concern: str = Field(min_length=1,max_length=160)
    notes: str = Field(default='',max_length=2000)
    requested_at: datetime

    @field_validator('concern')
    @classmethod
    def nonblank(cls,value):
        if not value.strip():raise ValueError('Choose a concern')
        return value.strip()

    @field_validator('requested_at')
    @classmethod
    def future(cls,value):
        if value.tzinfo is None:raise ValueError('Date must include a timezone')
        value=value.astimezone(timezone.utc).replace(tzinfo=None)
        if value<=now():raise ValueError('Choose a future requested time')
        return value


def consultation_data(row):
    doctor=db().get(User,row.doctor_id);profile=db().get(CareProfile,row.profile_id)
    review=db().scalar(select(DoctorReview).where(DoctorReview.doctor_id==row.doctor_id,DoctorReview.patient_id==row.patient_id))
    return dict(id=row.id,profile_id=row.profile_id,patient_name=profile.name,doctor_id=row.doctor_id,doctor_name=doctor.full_name,
        concern=row.concern,notes=row.notes,status=row.status,requested_at=row.requested_at.isoformat()+'Z',review_rating=review.rating if review else None,confirmed_at=row.confirmed_at.isoformat()+'Z' if row.confirmed_at else None,duration_minutes=row.duration_minutes,version=row.version)


def consultations(profile_id):
    row=primary(profile_id)
    visits=db().scalars(select(DoctorConsultation).where(DoctorConsultation.profile_id==row.id,DoctorConsultation.patient_id==g.user.id).order_by(DoctorConsultation.requested_at.desc()).limit(100))
    return jsonify(items=[consultation_data(v) for v in visits])


def request_consultation(profile_id):
    row=primary(profile_id);value=parse(ConsultationInput);doctor=approved(value.doctor_id)
    duplicate=db().scalar(select(DoctorConsultation.id).where(DoctorConsultation.profile_id==row.id,DoctorConsultation.doctor_id==doctor.id,DoctorConsultation.requested_at==value.requested_at,DoctorConsultation.status.in_(['REQUESTED','CONFIRMED'])))
    if duplicate:raise APIError(409,'request_exists','This consultation request already exists')
    visit=DoctorConsultation(profile_id=row.id,patient_id=g.user.id,doctor_id=doctor.id,concern=value.concern,notes=value.notes,requested_at=value.requested_at,status='REQUESTED')
    db().add(visit);db().flush()
    from doctor.notifications import queue_notification
    queue_notification(doctor.id,'consultation_requested','consultation:'+visit.id)
    audit('consultation_requested',doctor.id,g.user.id);db().commit()
    return jsonify(consultation=consultation_data(visit)),201


def doctor_requests():
    rows=db().scalars(select(DoctorConsultation).where(DoctorConsultation.doctor_id==g.user.id).order_by(DoctorConsultation.requested_at.desc()).limit(100))
    return jsonify(items=[consultation_data(row) for row in rows])


class StatusInput(Schema):
    status: Literal['CONFIRMED','DECLINED','COMPLETED','CANCELLED']
    confirmed_at: datetime|None=None
    duration_minutes:int=Field(default=30,ge=5,le=240)
    version:int|None=Field(default=None,ge=1)


def status(consultation_id):
    from services.appointment_slots import lock_doctor,check_conflicts
    lock_doctor(g.user.id)
    row=db().scalar(select(DoctorConsultation).where(DoctorConsultation.id==str(consultation_id),DoctorConsultation.doctor_id==g.user.id).with_for_update())
    if not row:raise APIError(404,'consultation_not_found','Consultation not found')
    value=parse(StatusInput)
    if value.status not in {'REQUESTED':{'CONFIRMED','DECLINED','CANCELLED'},'CONFIRMED':{'CONFIRMED','COMPLETED','DECLINED','CANCELLED'}}.get(row.status,set()):raise APIError(409,'invalid_transition','This status change is not permitted')
    if value.version is not None and value.version!=row.version:raise APIError(409,'consultation_conflict','Appointment changed. Refresh before updating')
    if value.status=='CONFIRMED':
        start=value.confirmed_at or row.requested_at.replace(tzinfo=timezone.utc)
        if start.tzinfo is None:raise APIError(422,'timezone_required','Confirmed time must include a timezone')
        start=start.astimezone(timezone.utc).replace(tzinfo=None)
        if start<=now():raise APIError(422,'future_time_required','Choose a future appointment time')
        check_conflicts(g.user.id,start,value.duration_minutes,row.id)
        row.confirmed_at=start;row.duration_minutes=value.duration_minutes
    if value.status=='COMPLETED' and row.confirmed_at and row.confirmed_at>now():raise APIError(409,'appointment_not_started','Appointment time has not arrived')
    row.version+=1
    from services.notifications import enqueue
    enqueue(row.patient_id,'consultation_status_changed','Consultation updated','Open your consultation to review the status and confirmed time.',{'profile_id':row.profile_id},event_key='consultation:'+row.id+':'+str(row.version))
    row.status=value.status;audit('consultation_status_changed',row.patient_id,g.user.id);db().commit()
    return jsonify(consultation=consultation_data(row))


def cancel(profile_id,consultation_id):
    primary(profile_id);row=db().scalar(select(DoctorConsultation).where(DoctorConsultation.id==str(consultation_id),DoctorConsultation.profile_id==str(profile_id),DoctorConsultation.patient_id==g.user.id).with_for_update())
    if not row:raise APIError(404,'consultation_not_found','Consultation not found')
    if row.status not in ('REQUESTED','CONFIRMED'):raise APIError(409,'invalid_transition','This request cannot be cancelled')
    row.status='CANCELLED';row.version+=1;audit('consultation_cancelled',row.doctor_id,g.user.id);db().commit();return jsonify(consultation=consultation_data(row))


class ReviewInput(Schema):
    consultation_id: UUID
    rating: int = Field(ge=1,le=5,strict=True)
    comment: str = Field(default='',max_length=1000)


def review(doctor_id):
    approved(doctor_id);value=parse(ReviewInput)
    visit=db().scalar(select(DoctorConsultation).where(DoctorConsultation.id==str(value.consultation_id),DoctorConsultation.patient_id==g.user.id,DoctorConsultation.doctor_id==str(doctor_id),DoctorConsultation.status=='COMPLETED'))
    if not visit:raise APIError(403,'completed_consultation_required','Only a completed consultation with this doctor can be reviewed')
    primary(visit.profile_id)
    row=db().scalar(select(DoctorReview).where(DoctorReview.doctor_id==str(doctor_id),DoctorReview.patient_id==g.user.id).with_for_update())
    if not row:row=DoctorReview(doctor_id=str(doctor_id),patient_id=g.user.id);db().add(row)
    row.consultation_id=visit.id;row.rating=value.rating;row.comment=value.comment.strip();audit('doctor_review_saved',str(doctor_id),g.user.id);db().commit()
    return jsonify(review=dict(id=row.id,rating=row.rating,comment=row.comment))


route(bp,'/patients/doctor-directory',directory,roles=('PATIENT',))
route(bp,'/patients/profiles/<uuid:profile_id>/consultations',consultations,roles=('PATIENT',))
route(bp,'/patients/profiles/<uuid:profile_id>/consultations',request_consultation,'POST',roles=('PATIENT',),schema=ConsultationInput)
route(bp,'/patients/profiles/<uuid:profile_id>/consultations/<uuid:consultation_id>/cancel',cancel,'POST',roles=('PATIENT',))
route(bp,'/patients/doctor-directory/<uuid:doctor_id>/review',review,'PUT',roles=('PATIENT',),schema=ReviewInput)
route(bp,'/doctors/consultation-visits',doctor_requests,roles=('DOCTOR',))
route(bp,'/doctors/consultation-visits/<uuid:consultation_id>/status',status,'PATCH',roles=('DOCTOR',),schema=StatusInput)
