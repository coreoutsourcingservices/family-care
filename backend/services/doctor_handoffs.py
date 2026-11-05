"""Selected reports and doctor-authored bullets, released only after patient consent."""
import io
import zipfile
from datetime import timedelta
from uuid import UUID
from typing import Literal
from flask import Blueprint, g, jsonify, send_file
from pydantic import Field, EmailStr, field_validator, model_validator
from sqlalchemy import select, or_, func
from werkzeug.utils import secure_filename
from core.database import db
from core.errors import APIError
from core.models import DoctorHandoff, CareProfile, CareReport, User, DoctorProfile, WomenAccessGrant, now
from core.routing import route
from core.schemas import Schema, parse
from services.repository import audit
from services.women_workspace import get_profile, primary_id

bp = Blueprint('doctor_handoffs', __name__, url_prefix='/api/v1')


class HandoffInput(Schema):
    doctor_identifier: str = Field(default='', max_length=160)
    external_name: str = Field(default='', max_length=120)
    external_email: EmailStr | None = None
    external_phone: str = Field(default='', max_length=16, pattern=r'^\+?[0-9]{8,15}$|^$')
    summary: list[str] = Field(min_length=1, max_length=20)
    report_ids: list[UUID] = Field(min_length=1, max_length=20)
    expires_in_days: int = Field(default=7, ge=1, le=30)

    @field_validator('summary')
    @classmethod
    def bullets(cls, values):
        result = [v.strip() for v in values]
        if any(not v or len(v) > 500 for v in result):
            raise ValueError('Each summary bullet must contain 1–500 characters')
        return result

    @model_validator(mode='after')
    def recipient(self):
        if self.doctor_identifier.strip():
            if self.external_name or self.external_email or self.external_phone:
                raise ValueError('Choose an app doctor or an external doctor')
        elif not self.external_name.strip() or not (self.external_email or self.external_phone):
            raise ValueError('Enter the external doctor name and email or phone')
        return self


class HandoffDecision(Schema):
    decision: Literal['APPROVED', 'DECLINED', 'REVOKED']


def active_doctor(user_id):
    user = db().get(User, user_id)
    if not user or user.role != 'DOCTOR' or not user.email_verified or user.account_status != 'ACTIVE' or user.approval_status != 'APPROVED':
        raise APIError(403, 'doctor_unavailable', 'Doctor is no longer active and approved')
    return user


def source_profile(profile_id, source_id):
    profile = db().scalar(select(CareProfile).where(CareProfile.id == str(profile_id), CareProfile.module == 'women', CareProfile.deleted_at.is_(None)).with_for_update())
    if not profile or profile.referred_doctor_id != source_id:
        raise APIError(403, 'handoff_access_denied', 'The referring doctor is no longer connected')
    active_doctor(source_id)
    grant = db().scalar(select(WomenAccessGrant).where(WomenAccessGrant.profile_id == profile.id, WomenAccessGrant.recipient_id == source_id,
        WomenAccessGrant.revoked_at.is_(None), or_(WomenAccessGrant.starts_at.is_(None), WomenAccessGrant.starts_at <= now()),
        or_(WomenAccessGrant.expires_at.is_(None), WomenAccessGrant.expires_at > now())).with_for_update())
    if not grant or 'records' not in grant.permissions:
        raise APIError(403, 'handoff_access_denied', 'The referring doctor needs current Medical records permission')
    return profile


def reports(row):
    result = list(db().scalars(select(CareReport).where(CareReport.profile_id == row.profile_id, CareReport.deleted_at.is_(None), CareReport.id.in_(row.report_ids)).order_by(CareReport.id)))
    if {r.id for r in result} != set(row.report_ids):
        raise APIError(409, 'reports_changed', 'A selected report is unavailable; create a new referral')
    return result


def data(row, full=True):
    profile = db().get(CareProfile, row.profile_id)
    source = db().get(User, row.source_id)
    recipient = db().get(User, row.recipient_id) if row.recipient_id else None
    result = dict(id=row.id, profile_id=row.profile_id, source_name=source.full_name, source_public_id=source.public_id,
        recipient_name=row.recipient_name, recipient_public_id=recipient.public_id if recipient else None,
        external=not row.recipient_id, status='EXPIRED' if row.expires_at <= now() else row.status,
        expires_at=row.expires_at.isoformat()+'Z', created_at=row.created_at.isoformat()+'Z')
    if full:
        available = {r.id:r.name for r in db().scalars(select(CareReport).where(CareReport.profile_id == row.profile_id, CareReport.deleted_at.is_(None), CareReport.id.in_(row.report_ids)))}
        result.update(patient_name=profile.name, summary=row.summary, recipient_email=row.recipient_email,
            recipient_phone=row.recipient_phone, reports=[dict(id=report_id, name=available.get(report_id, 'Report no longer available')) for report_id in row.report_ids])
    return result


def options(profile_id):
    profile = source_profile(profile_id, g.user.id)
    rows = db().scalars(select(CareReport).where(CareReport.profile_id == profile.id, CareReport.deleted_at.is_(None)).order_by(CareReport.created_at.desc()))
    return jsonify(patient_name=profile.name, reports=[dict(id=r.id, name=r.name, category=r.category) for r in rows])


def create(profile_id):
    profile = source_profile(profile_id, g.user.id)
    value = parse(HandoffInput)
    recipient = None
    if value.doctor_identifier.strip():
        identifier = value.doctor_identifier.strip().lower()
        recipient = db().scalar(select(User).join(DoctorProfile, DoctorProfile.user_id == User.id).where(
            or_(func.lower(User.public_id) == identifier, func.lower(DoctorProfile.referral_id) == identifier)))
        if not recipient:
            raise APIError(422, 'doctor_not_found', 'No approved app doctor matches this referral ID or public ID')
        active_doctor(recipient.id)
        if recipient.id == g.user.id:
            raise APIError(422, 'same_doctor', 'Choose another doctor')
    row = DoctorHandoff(profile_id=profile.id, source_id=g.user.id, recipient_id=recipient.id if recipient else None,
        recipient_name=recipient.full_name if recipient else value.external_name.strip(),
        recipient_email=recipient.email if recipient else str(value.external_email or ''), recipient_phone=value.external_phone,
        summary=value.summary, report_ids=list(dict.fromkeys(str(v) for v in value.report_ids)),
        expires_at=now()+timedelta(days=value.expires_in_days))
    reports(row)
    db().add(row); db().flush()
    from services.notifications import enqueue
    enqueue(primary_id(profile), 'doctor_referral_consent', 'Doctor referral needs your approval',
        f'{g.user.full_name} requests permission to share selected reports with {row.recipient_name}.',
        {'profile_id': profile.id, 'handoff_id': row.id, 'path':'/customer/women/sharing'}, 'handoff-request:'+row.id)
    audit('doctor_handoff_requested', primary_id(profile), g.user.id)
    db().commit()
    return jsonify(handoff=data(row)), 201


def patient_list(profile_id):
    profile, _ = get_profile(profile_id, manage=True)
    rows = db().scalars(select(DoctorHandoff).where(DoctorHandoff.profile_id == profile.id).order_by(DoctorHandoff.created_at.desc()).limit(100))
    return jsonify(items=[data(row) for row in rows])


def decide(profile_id, handoff_id):
    profile, _ = get_profile(profile_id, manage=True)
    value = parse(HandoffDecision)
    row = db().scalar(select(DoctorHandoff).where(DoctorHandoff.id == str(handoff_id), DoctorHandoff.profile_id == profile.id).with_for_update())
    if not row:
        raise APIError(404, 'handoff_not_found', 'Referral not found')
    if row.expires_at <= now() or value.decision == 'REVOKED' and row.status != 'APPROVED' or value.decision != 'REVOKED' and row.status != 'PENDING':
        raise APIError(409, 'handoff_state', 'This referral can no longer receive that decision')
    if value.decision == 'APPROVED':
        source_profile(profile.id, row.source_id); reports(row)
        if row.recipient_id:
            active_doctor(row.recipient_id)
    row.status=value.decision; row.decided_by=g.user.id; row.decided_at=now()
    from services.notifications import enqueue
    for user_id in {row.source_id, row.recipient_id} - {None}:
        if user_id == row.recipient_id and row.status == 'DECLINED':
            continue
        enqueue(user_id, 'doctor_referral_updated', 'Doctor referral '+row.status.lower(),
            'Open Doctor referrals to review the update.', {'handoff_id':row.id, 'path':'/doctor/referrals'}, 'handoff-'+row.status+':'+row.id)
    audit('doctor_handoff_'+row.status.lower(), primary_id(profile), g.user.id)
    db().commit()
    return jsonify(handoff=data(row))


def doctor_list():
    rows = db().scalars(select(DoctorHandoff).where(or_(DoctorHandoff.source_id == g.user.id,
        (DoctorHandoff.recipient_id == g.user.id) & (DoctorHandoff.status == 'APPROVED') & (DoctorHandoff.expires_at > now()))).order_by(DoctorHandoff.created_at.desc()).limit(100))
    items=[]
    for row in rows:
        try:
            source_profile(row.profile_id, row.source_id)
            items.append(dict(data(row, full=row.source_id == g.user.id or row.status == 'APPROVED'), direction='sent' if row.source_id == g.user.id else 'received'))
        except APIError:
            if row.source_id == g.user.id:
                items.append(dict(data(row, full=False), direction='sent', unavailable=True))
    return jsonify(items=items)


def authorized(handoff_id):
    row=db().scalar(select(DoctorHandoff).where(DoctorHandoff.id == str(handoff_id)).with_for_update())
    if not row or g.user.id not in (row.source_id, row.recipient_id):
        raise APIError(404, 'handoff_not_found', 'Referral not found')
    if row.status != 'APPROVED' or row.expires_at <= now():
        raise APIError(403, 'consent_required', 'Patient approval is missing, expired or revoked')
    source_profile(row.profile_id, row.source_id)
    if row.recipient_id:
        active_doctor(row.recipient_id)
    return row


def download(handoff_id):
    row=authorized(handoff_id)
    from services.report_text import report_bytes
    buffer=io.BytesIO()
    profile=db().get(CareProfile,row.profile_id)
    summary='FamilyCare doctor referral\nPatient: '+profile.name+'\nFrom: '+db().get(User,row.source_id).full_name+'\nTo: '+row.recipient_name+'\nDoctor-authored summary:\n'+'\n'.join('- '+v for v in row.summary)
    total=0
    with zipfile.ZipFile(buffer,'w',zipfile.ZIP_DEFLATED) as archive:
        archive.writestr('referral-summary.txt',summary)
        for report in reports(row):
            try:
                content=report_bytes(report)
            except ValueError:
                raise APIError(502,'report_download_failed','A selected report could not be retrieved. Please retry.') from None
            total+=len(content)
            if total > 50*1024*1024:
                raise APIError(413,'handoff_too_large','Select reports totalling 50 MB or less')
            archive.writestr(report.id+'_'+(secure_filename(report.name) or 'report'),content)
    audit('doctor_handoff_downloaded',primary_id(profile),g.user.id);db().commit()
    buffer.seek(0)
    return send_file(buffer,mimetype='application/zip',as_attachment=True,download_name='doctor-referral-'+row.id+'.zip')


route(bp, '/doctors/women/<uuid:profile_id>/handoff-options', options, roles=('DOCTOR',))
route(bp, '/doctors/women/<uuid:profile_id>/handoffs', create, 'POST', roles=('DOCTOR',), schema=HandoffInput, limited=True)
route(bp, '/doctors/handoffs', doctor_list, roles=('DOCTOR',))
route(bp, '/doctors/handoffs/<uuid:handoff_id>/download', download, roles=('DOCTOR',))
route(bp, '/women/profiles/<uuid:profile_id>/handoffs', patient_list, roles=('PATIENT',))
route(bp, '/women/profiles/<uuid:profile_id>/handoffs/<uuid:handoff_id>', decide, 'PUT', roles=('PATIENT',), schema=HandoffDecision)
