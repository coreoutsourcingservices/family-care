from datetime import datetime,timezone
from typing import Literal
from flask import g,jsonify
from pydantic import Field,model_validator
from sqlalchemy import select,and_,or_,exists
from core.database import db
from core.models import ProfileDoctorGrant,CareProfile,CareReport,now
from core.errors import APIError
from core.schemas import Schema,parse


class GrantInput(Schema):
    referral_id:str=Field(min_length=1,max_length=160)
    scopes:list[Literal['reports','records']]=Field(min_length=1,max_length=2)
    report_ids:list[str]|None=Field(default=None,max_length=200)
    record_kinds:list[str]|None=Field(default=None,max_length=40)
    expires_at:datetime|None=None

    @model_validator(mode='after')
    def valid(self):
        if self.expires_at:
            if self.expires_at.tzinfo is None:raise ValueError('Expiry must include a timezone')
            self.expires_at=self.expires_at.astimezone(timezone.utc).replace(tzinfo=None)
            if self.expires_at<=now():raise ValueError('Expiry must be in the future')
        if self.report_ids is not None and not self.report_ids:raise ValueError('Select reports or allow all reports')
        if self.record_kinds is not None and not self.record_kinds:raise ValueError('Select record types or allow all types')
        return self


def doctor_profile_filter(user):
    grant=ProfileDoctorGrant
    configured=exists(select(grant.profile_id).where(grant.profile_id==CareProfile.id))
    active=exists(select(grant.profile_id).where(grant.profile_id==CareProfile.id,grant.doctor_id==user.id,
        grant.revoked_at.is_(None),or_(grant.expires_at.is_(None),grant.expires_at>now())))
    return and_(CareProfile.module!='women',CareProfile.referred_doctor_id==user.id,or_(CareProfile.module=='child',~configured,active))


def current_grant(profile):
    return db().get(ProfileDoctorGrant,profile.id) if profile.module in ('adult','women') else None


def require_scope(user,profile,scope):
    if getattr(g,'women_authorized',None)==profile.id:return None
    if user.role!='DOCTOR':return None
    grant=current_grant(profile)
    if grant and (grant.doctor_id!=user.id or grant.revoked_at or grant.expires_at and grant.expires_at<=now() or scope not in grant.scopes):
        raise APIError(403,'access_scope_denied','This area is outside the permission granted for this profile')
    return grant


def serialize(grant):
    if not grant:return None
    return dict(scopes=grant.scopes,report_ids=grant.report_ids,record_kinds=grant.record_kinds,
        expires_at=grant.expires_at.isoformat()+'Z' if grant.expires_at else None,
        active=not grant.revoked_at and (not grant.expires_at or grant.expires_at>now()),doctor_id=grant.doctor_id)


def manage(profile_id):
    from services.care import accessible_profile
    profile=accessible_profile(g.user,str(profile_id),lock=True)
    if profile.module=='women':raise APIError(422,'women_tab_sharing_required','Use Women tab sharing for family and doctor permissions')
    if profile.module not in ('adult','women'):raise APIError(422,'invalid_module','Timed permissions apply only to adult and women profiles')
    return profile


def get_grant(profile_id):
    return jsonify(access=serialize(current_grant(manage(profile_id))))


def put_grant(profile_id):
    from services.referrals import resolve_referral
    from services.repository import audit
    profile=manage(profile_id);value=parse(GrantInput)
    doctor,_=resolve_referral(value.referral_id,lock=True)
    if value.report_ids is not None:
        import uuid
        try:ids=[str(uuid.UUID(item)) for item in value.report_ids]
        except ValueError:raise APIError(422,'invalid_reports','Select reports belonging to this profile') from None
        found=set(db().scalars(select(CareReport.id).where(CareReport.profile_id==profile.id,CareReport.deleted_at.is_(None),CareReport.id.in_(ids))))
        if found!=set(ids):raise APIError(422,'invalid_reports','Select reports belonging to this profile')
        value.report_ids=ids
    grant=current_grant(profile)
    if not grant:grant=ProfileDoctorGrant(profile_id=profile.id);db().add(grant)
    grant.doctor_id=doctor.id;grant.granted_by=g.user.id;grant.scopes=list(set(value.scopes))
    grant.report_ids=value.report_ids;grant.record_kinds=value.record_kinds
    grant.expires_at=value.expires_at;grant.revoked_at=None
    profile.referred_doctor_id=doctor.id
    audit('profile_doctor_access_granted',profile.owner_id,g.user.id);db().commit()
    return jsonify(access=serialize(grant))


def revoke_grant(profile_id):
    from services.repository import audit
    profile=manage(profile_id);grant=current_grant(profile)
    if grant:grant.revoked_at=now()
    profile.referred_doctor_id=None
    audit('profile_doctor_access_revoked',profile.owner_id,g.user.id);db().commit()
    return jsonify(message='Doctor access revoked')
