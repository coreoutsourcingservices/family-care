"""Server-owned women's diary and explicit, expiring view/edit sharing."""
from datetime import date, datetime, timezone
from typing import Literal
from uuid import UUID
from flask import Blueprint, g, jsonify, request
from pydantic import Field, field_validator, model_validator
from sqlalchemy import select, or_
from core.database import db
from core.errors import APIError
from core.models import CareProfile, FamilyInvitation, User, WomenAccessGrant, WomenDiaryRecord, now
from core.routing import route
from core.schemas import Schema, parse
from services.repository import audit
from services.health_access import GrantInput, event, history

bp = Blueprint('women_workspace', __name__, url_prefix='/api/v1/women')
TABS = dict(health='My health', cycle='Period & cycle', pcos='PCOS & hormonal',
    pregnancy='Pregnancy care', fertility='Fertility & reproductive', symptoms='Symptoms & wellness',
    nutrition='Nutrition & lifestyle', screening='Screening & preventive', records='Medical records',
    consultation='Doctor consultation')
DIARY = set(TABS) - {'records'} | {'reminder', 'checkin'}


def membership(profile):
    return db().scalar(select(FamilyInvitation).where(FamilyInvitation.profile_id == profile.id,
        FamilyInvitation.accepted_at.is_not(None), FamilyInvitation.revoked_at.is_(None)))


def primary_id(profile):
    member = membership(profile)
    return member.member_id if member else profile.owner_id


def is_primary(user, profile):
    return user.role == 'PATIENT' and user.id == primary_id(profile)


def permissions(profile):
    if is_primary(g.user, profile):
        return {tab: 'edit' for tab in TABS}
    grant = db().scalar(select(WomenAccessGrant).where(WomenAccessGrant.profile_id == profile.id,
        WomenAccessGrant.recipient_id == g.user.id, WomenAccessGrant.revoked_at.is_(None),
        or_(WomenAccessGrant.starts_at.is_(None),WomenAccessGrant.starts_at<=now()),
        or_(WomenAccessGrant.expires_at.is_(None), WomenAccessGrant.expires_at > now())))
    if not grant:
        raise APIError(403, 'women_access_denied', 'Permission is missing, expired or revoked')
    # Membership/doctor disconnection also terminates effective access immediately.
    if not any(user.id == g.user.id for user in recipients(profile)):
        raise APIError(403, 'women_access_denied', 'This family member or doctor is no longer connected')
    return grant.permissions


def get_profile(profile_id, tab=None, edit=False, manage=False):
    profile = db().scalar(select(CareProfile).where(CareProfile.id == str(profile_id),
        CareProfile.module == 'women', CareProfile.deleted_at.is_(None)).with_for_update())
    if not profile:
        raise APIError(404, 'profile_not_found', 'Women profile not found')
    if manage and not is_primary(g.user, profile):
        raise APIError(403, 'owner_required', 'Only this profile owner can manage sharing')
    allowed = permissions(profile)
    effective = 'symptoms' if tab == 'checkin' else tab
    if tab == 'reminder' and not is_primary(g.user, profile):
        raise APIError(403, 'women_tab_denied', 'Personal reminders are private')
    if effective and effective != 'reminder' and (effective not in allowed or edit and allowed[effective] != 'edit'):
        raise APIError(403, 'women_tab_denied', 'You do not have this tab permission')
    return profile, allowed


def recipients(profile):
    # Only existing accepted members of the same family and this profile's connected doctor.
    member_ids = list(db().scalars(select(FamilyInvitation.member_id).where(
        FamilyInvitation.owner_id == profile.owner_id, FamilyInvitation.accepted_at.is_not(None),
        FamilyInvitation.revoked_at.is_(None), FamilyInvitation.member_id.is_not(None))))
    ids = [profile.owner_id, *member_ids]
    if profile.referred_doctor_id:
        ids.append(profile.referred_doctor_id)
    return list(db().scalars(select(User).where(User.id.in_(ids), User.id != primary_id(profile),
        User.account_status == 'ACTIVE', User.email_verified.is_(True), User.approval_status == 'APPROVED')))


def grant_data(row):
    user = db().get(User, row.recipient_id)
    return dict(revoked_at=row.revoked_at.isoformat()+'Z' if row.revoked_at else None,id=row.id, recipient_id=row.recipient_id, name=user.full_name, role=user.role,
        permissions=row.permissions, starts_at=row.starts_at.isoformat()+'Z' if row.starts_at else None, expires_at=row.expires_at.isoformat()+'Z' if row.expires_at else None,
        active=not row.revoked_at and (row.starts_at is None or row.starts_at<=now()) and (row.expires_at is None or row.expires_at > now()))


class WomenGrantInput(GrantInput):
    @model_validator(mode='after')
    def validate_tabs(self):
        if set(self.permissions)-set(TABS):raise ValueError('Choose valid Women tabs')
        return self


def sharing(profile_id):
    profile, _ = get_profile(profile_id, manage=True)
    return jsonify(tabs=TABS, recipients=[dict(id=u.id, name=u.full_name, role=u.role) for u in recipients(profile)],
        grants=[grant_data(row) for row in db().scalars(select(WomenAccessGrant).where(WomenAccessGrant.profile_id == profile.id))])


def save_sharing(profile_id):
    profile, _ = get_profile(profile_id, manage=True)
    value = parse(WomenGrantInput)
    recipient_id = str(value.recipient_id)
    if recipient_id not in {u.id for u in recipients(profile)}:
        raise APIError(422, 'invalid_recipient', 'Choose a current family member or connected approved doctor')
    grant = db().scalar(select(WomenAccessGrant).where(WomenAccessGrant.profile_id == profile.id,
        WomenAccessGrant.recipient_id == recipient_id).with_for_update())
    if not grant:
        grant = WomenAccessGrant(profile_id=profile.id, recipient_id=recipient_id)
        db().add(grant)
    grant.granted_by = g.user.id
    grant.permissions = value.permissions
    grant.starts_at = value.starts_at
    grant.expires_at = value.expires_at
    grant.revoked_at = None
    event(profile,grant,'granted')
    audit('women_tab_access_granted', recipient_id, g.user.id)
    db().commit()
    return jsonify(grant=grant_data(grant))


def revoke_sharing(profile_id, grant_id):
    profile, _ = get_profile(profile_id, manage=True)
    grant = db().scalar(select(WomenAccessGrant).where(WomenAccessGrant.id == str(grant_id),
        WomenAccessGrant.profile_id == profile.id))
    if not grant:
        raise APIError(404, 'grant_not_found', 'Permission not found')
    grant.revoked_at = now()
    event(profile,grant,'revoked')
    audit('women_tab_access_revoked', grant.recipient_id, g.user.id)
    db().commit()
    return jsonify(message='Access revoked')


def record_data(row):
    from services.personal_reminders import delivery
    extra={'delivery_status':delivery('women',row,g.user.id)} if row.section=='reminder' else {}
    return dict(row.data, id=row.id, section=row.section, version=str(row.version),**extra)


def workspace(profile_id):
    profile, allowed = get_profile(profile_id)
    visible = set(allowed) | ({'reminder', 'checkin'} if is_primary(g.user, profile) else {'checkin'} if 'symptoms' in allowed else set())
    records = db().scalars(select(WomenDiaryRecord).where(WomenDiaryRecord.profile_id == profile.id,
        WomenDiaryRecord.deleted_at.is_(None), WomenDiaryRecord.section.in_(visible)).order_by(WomenDiaryRecord.updated_at))
    # The shared dashboard receives only the records authorised for this recipient.
    grant = None if is_primary(g.user, profile) else db().scalar(select(WomenAccessGrant).where(
        WomenAccessGrant.profile_id == profile.id, WomenAccessGrant.recipient_id == g.user.id))
    return jsonify(profile=dict(id=profile.id, name=profile.name, dob=profile.dob.isoformat()),
        owner=is_primary(g.user, profile), permissions=allowed, records=[record_data(row) for row in records],
        access_expires_at=grant.expires_at.isoformat()+'Z' if grant and grant.expires_at else None)


class WomenRecordInput(Schema):
    section: str = Field(max_length=24)
    data: dict[str, str] = Field(max_length=20)
    version: int = Field(default=0, ge=0)

    @model_validator(mode='after')
    def topic_fields(self):
        statuses={'screening':{'Planned','Scheduled','Completed','Result received','Follow-up required'},'reminder':{'Planned','Completed','Dismissed'}}.get(self.section,{'Planned','Completed'})
        if self.data.get('status') and self.data['status'] not in statuses:raise ValueError('Choose a valid status for this section')
        allowed={'flow':{'Light','Medium','Heavy'},'severity':{'Mild','Moderate','Severe'},'diagnosis_source':{'Self-reported symptoms','Clinician-confirmed diagnosis'},'due_source':{'Not confirmed','Clinician confirmed','Ultrasound estimate','Last period estimate'},'pregnancy_status':{'Ongoing','Ended','Postpartum'}}
        for field,choices in allowed.items():
            if self.data.get(field) and self.data[field] not in choices:raise ValueError('Choose a valid '+field.replace('_',' '))
        if self.section=='pregnancy' and self.data.get('pregnancy_status') in ('Ended','Postpartum') and not self.data.get('ended_on'):raise ValueError('Enter the pregnancy end date')
        if self.data.get('ended_on'):
            from patient.child_routes import today
            if date.fromisoformat(self.data['ended_on'])>today():raise ValueError('Pregnancy end date cannot be in the future')
        return self

    @field_validator('section')
    @classmethod
    def valid_section(cls, value):
        if value not in DIARY:
            raise ValueError('Choose a valid diary section')
        return value

    @field_validator('data')
    @classmethod
    def valid_data(cls, value):
        if not value.get('title', '').strip() or len(value['title']) > 120:
            raise ValueError('A title up to 120 characters is required')
        first=date.fromisoformat(value.get('date', ''))
        if first.isoformat()!=value['date']:raise ValueError('Use YYYY-MM-DD dates')
        for key in ('end','due','next','ended_on'):
            if value.get(key):date.fromisoformat(value[key])
        if value.get('pain_score') and not 0<=float(value['pain_score'])<=10:raise ValueError('Pain score must be between 0 and 10')
        if any(len(v) > 2000 for v in value.values()):
            raise ValueError('Diary fields must be 2000 characters or shorter')
        if value.get('end') and value['end'] < value['date']:
            raise ValueError('End date must be on or after start date')
        if value.get('week') and not 1 <= int(value['week']) <= 45:
            raise ValueError('Pregnancy week must be between 1 and 45')
        if value.get('status') and value['status'] not in ('Planned','Scheduled','Completed','Result received','Follow-up required','Dismissed'):
            raise ValueError('Choose a valid status')
        return {k: v for k, v in value.items() if k not in ('id', 'section', 'version')}


def put_record(profile_id, record_id):
    value = parse(WomenRecordInput)
    profile, _ = get_profile(profile_id, value.section, edit=True)
    row = db().get(WomenDiaryRecord, str(record_id))
    if row and row.profile_id != profile.id:
        raise APIError(404, 'record_not_found', 'Diary entry not found')
    if row and (row.deleted_at or row.section != value.section):
        raise APIError(409, 'record_conflict', 'This diary entry was removed or has another section')
    if row and row.version != value.version or not row and value.version != 0:
        raise APIError(409, 'record_conflict', 'Entry changed. Refresh before saving again')
    first=date.fromisoformat(value.data['date'])
    if first<profile.dob:raise APIError(422,'invalid_date','Diary date cannot precede birth')
    if value.section=='cycle':
        from patient.child_routes import today
        if first>today():raise APIError(422,'invalid_date','A recorded period cannot start in the future')
        last=date.fromisoformat(value.data.get('end') or value.data['date'])
        others=db().scalars(select(WomenDiaryRecord).where(WomenDiaryRecord.profile_id==profile.id,WomenDiaryRecord.section=='cycle',WomenDiaryRecord.id!=str(record_id),WomenDiaryRecord.deleted_at.is_(None)))
        if any(first<=date.fromisoformat(r.data.get('end') or r.data['date']) and last>=date.fromisoformat(r.data['date']) for r in others):raise APIError(409,'overlapping_period','This period overlaps an existing entry. Edit that entry instead')
    if not row:
        row = WomenDiaryRecord(id=str(record_id), profile_id=profile.id, section=value.section, version=0, data={})
        db().add(row)
    row.data = value.data
    row.version += 1
    row.updated_by = g.user.id
    audit('women_diary_saved', profile.owner_id, g.user.id)
    db().commit()
    return jsonify(record=record_data(row))


def delete_record(profile_id, record_id):
    # Lock before loading the entry so a concurrent edit cannot leave a stale version in this session.
    get_profile(profile_id)
    row = db().get(WomenDiaryRecord, str(record_id))
    if not row or row.profile_id != str(profile_id) or row.deleted_at:
        raise APIError(404, 'record_not_found', 'Diary entry not found')
    profile, _ = get_profile(profile_id, row.section, edit=True)
    if request.args.get('version') != str(row.version):
        raise APIError(409, 'record_conflict', 'Entry changed. Refresh before deleting again')
    row.deleted_at = now()
    from services.recycle_bin import retain
    retain('women_diary',row,profile_id=profile.id)
    audit('women_diary_removed', profile.owner_id, g.user.id)
    db().commit()
    return jsonify(message='Diary entry deleted')


def shared_profiles():
    rows = db().scalars(select(CareProfile).join(WomenAccessGrant, WomenAccessGrant.profile_id == CareProfile.id).where(
        CareProfile.deleted_at.is_(None), WomenAccessGrant.recipient_id == g.user.id,
        WomenAccessGrant.revoked_at.is_(None), or_(WomenAccessGrant.expires_at.is_(None), WomenAccessGrant.expires_at > now())))
    items = []
    for profile in rows:
        try:
            allowed = permissions(profile)
        except APIError:
            continue
        items.append(dict(id=profile.id, name=profile.name, permissions=allowed))
    return jsonify(items=items)


def reports(profile_id):
    profile, _ = get_profile(profile_id, 'records', edit=request.method == 'POST')
    g.women_authorized = profile.id
    if request.method == 'POST':
        from patient.care_controller import upload_report
        response, status = upload_report(profile.id)
        report = response.get_json()['report']
        report.update(url=None, secure_url=None)
        return jsonify(report=report), status
    from core.models import CareReport
    from services.care_uploads import report_data
    items = db().scalars(select(CareReport).where(CareReport.profile_id == profile.id, CareReport.deleted_at.is_(None)).order_by(CareReport.created_at.desc()))
    return jsonify(items=[dict(report_data(r), url=None, secure_url=None) for r in items])


def download(profile_id, report_id):
    profile, _ = get_profile(profile_id, 'records')
    from core.models import CareReport
    from services.report_text import report_bytes
    from flask import send_file
    import io
    report = db().scalar(select(CareReport).where(CareReport.id == str(report_id), CareReport.profile_id == profile.id, CareReport.deleted_at.is_(None)))
    if not report:
        raise APIError(404, 'report_not_found', 'Report not found')
    try:
        content = report_bytes(report)
    except ValueError:
        raise APIError(502, 'report_download_failed', 'The stored report could not be downloaded. Please retry.') from None
    response = send_file(io.BytesIO(content), mimetype=report.content_type,
        as_attachment=True, download_name=report.name)
    response.headers['Cache-Control'] = 'no-store'
    return response


def upload(profile_id):
    return reports(profile_id)


def remove_report(profile_id, report_id):
    profile, _ = get_profile(profile_id, 'records', edit=True)
    g.women_authorized = profile.id
    from services.report_records import delete_report
    return delete_report(profile_id, report_id)


ROLES = ('PATIENT', 'DOCTOR')
route(bp, '/shared', shared_profiles, roles=ROLES)
route(bp, '/profiles/<uuid:profile_id>/workspace', workspace, roles=ROLES)
route(bp, '/profiles/<uuid:profile_id>/sharing', sharing, roles=('PATIENT',))
route(bp, '/profiles/<uuid:profile_id>/sharing', save_sharing, 'PUT', roles=('PATIENT',), schema=WomenGrantInput)
route(bp, '/profiles/<uuid:profile_id>/sharing/<uuid:grant_id>', revoke_sharing, 'DELETE', roles=('PATIENT',))
route(bp, '/profiles/<uuid:profile_id>/diary/<uuid:record_id>', put_record, 'PUT', roles=ROLES, schema=WomenRecordInput)
route(bp, '/profiles/<uuid:profile_id>/diary/<uuid:record_id>', delete_record, 'DELETE', roles=ROLES)
route(bp, '/profiles/<uuid:profile_id>/reports', reports, roles=ROLES)
route(bp, '/profiles/<uuid:profile_id>/reports', upload, 'POST', roles=ROLES)
route(bp, '/profiles/<uuid:profile_id>/reports/<uuid:report_id>/download', download, roles=ROLES)
route(bp, '/profiles/<uuid:profile_id>/reports/<uuid:report_id>', remove_report, 'DELETE', roles=ROLES)


def access_history(profile_id):return history(get_profile(profile_id,manage=True)[0])
route(bp,'/profiles/<uuid:profile_id>/history',access_history,roles=('PATIENT',))
