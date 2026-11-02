from flask import jsonify, request, g
from sqlalchemy import select
from core.database import db
from core.models import CareProfile, CareReport, User, FamilyInvitation, uid, now
from core.errors import APIError
from services.referrals import resolve_referral, doctor_details, care_doctor_details
from services.repository import audit
from services.approvals import paginate


def member_profile(user):
    return db().scalar(select(CareProfile).join(FamilyInvitation,FamilyInvitation.profile_id==CareProfile.id).where(FamilyInvitation.member_id==user.id,FamilyInvitation.accepted_at.is_not(None),FamilyInvitation.revoked_at.is_(None),CareProfile.deleted_at.is_(None)))


def patient_profile_access(user):
    member=member_profile(user)
    if member:return CareProfile.id==member.id
    linked=select(FamilyInvitation.profile_id).where(FamilyInvitation.member_id==user.id,
        FamilyInvitation.accepted_at.is_not(None),FamilyInvitation.revoked_at.is_(None))
    return (CareProfile.owner_id==user.id) | CareProfile.id.in_(linked)


def accessible_profile(user, profile_id, lock=False):
    # Delegates use the scoped Women workspace. Legacy APIs cannot bypass tab expiry.
    women_profile = db().get(CareProfile, profile_id)
    if women_profile and women_profile.module == 'women':
        from services.women_workspace import is_primary, recipients
        if getattr(g, 'women_authorized', None) == profile_id:
            return women_profile
        if not is_primary(user, women_profile):
            if user.id not in {recipient.id for recipient in recipients(women_profile)}:
                raise APIError(404, 'profile_not_found', 'Care profile not found')
            raise APIError(403, 'women_scoped_workspace_required', 'Open the shared Women workspace to use your tab permissions')
    if women_profile and women_profile.module=='adult':
        from core.models import AdultTabGrant
        from services.women_workspace import is_primary
        if getattr(g,'adult_authorized',None)==profile_id:return women_profile
        if not is_primary(user,women_profile) and db().scalar(select(AdultTabGrant.id).where(AdultTabGrant.profile_id==profile_id).limit(1)):
            raise APIError(403,'adult_scoped_workspace_required','Open the shared Adult workspace to use tab permissions')
    query = select(CareProfile).where(CareProfile.id == profile_id, CareProfile.deleted_at.is_(None))
    if user.role == 'PATIENT':
        query = query.where(patient_profile_access(user))
    elif user.role == 'DOCTOR':
        from services.profile_doctor_access import doctor_profile_filter
        query = query.where(doctor_profile_filter(user))
    else:
        raise APIError(403, 'forbidden', 'Profile access denied')
    if lock:
        query = query.with_for_update()
    profile = db().scalar(query)
    if not profile:
        raise APIError(404, 'profile_not_found', 'Care profile not found')
    if user.role == 'PATIENT' and profile.owner_id == user.id and profile.module in ('adult','women') and profile.profile_type != 'self':
        invitation = db().scalar(select(FamilyInvitation).where(FamilyInvitation.profile_id == profile.id, FamilyInvitation.accepted_at.is_not(None)))
        if invitation and (not (invitation.pending or {}).get('family_access') or request.method != 'GET'):
            raise APIError(403, 'member_permission_required', 'This member must allow family access before you can view their medical details')
    return profile


def profile_data(profile):
    doctor = db().get(User, profile.referred_doctor_id) if profile.referred_doctor_id else None
    membership=db().scalar(select(FamilyInvitation).where(FamilyInvitation.profile_id==profile.id,FamilyInvitation.accepted_at.is_not(None)))
    from services.profile_doctor_access import current_grant,serialize
    return dict(access_permissions=serialize(current_grant(profile)),id=profile.id, profile_type=profile.profile_type, module=profile.module,
                member_email=membership.email if membership else '',relationship=membership.relationship if membership else None,
                linked_member=bool(membership),
                full_name=profile.name, date_of_birth=profile.dob.isoformat(), gender=profile.gender,
                parent_profile_id=profile.parent_profile_id, guardian_contact=profile.guardian_contact, guardian_name=profile.guardian_name,
                emergency_contacts=profile.emergency_contacts,
                doctor=care_doctor_details(doctor) if doctor else None,
                created_at=profile.created_at.isoformat()+'Z')


def create_profile(user, data):
    if member_profile(user):raise APIError(403,'member_profile_only','This member account is limited to its invited profile')
    if data.profile_type == 'self' and db().scalar(select(CareProfile.id).where(
            CareProfile.owner_id == user.id, CareProfile.profile_type == 'self')):
        raise APIError(409, 'self_profile_exists', 'A self profile already exists')
    parent = accessible_profile(user, str(data.parent_profile_id)) if data.parent_profile_id else None
    if parent and (parent.module == 'child' or parent.dob >= data.date_of_birth):
        raise APIError(422, 'invalid_parent', 'Parent must be an older adult/women profile in your account')
    doctor, _ = resolve_referral(data.referral_id, lock=True) if data.referral_id else (None, None)
    profile = CareProfile(id=uid(), owner_id=user.id, profile_type=data.profile_type,
                          module=data.module, name=data.full_name, dob=data.date_of_birth,gender=data.gender,
                          parent_profile_id=parent.id if parent else None,
                          guardian_contact=data.guardian_contact or ((user.phone_number or '') if data.module=='child' else ''),
                          guardian_name=data.guardian_name or (user.full_name if data.module=='child' else ''),
                          emergency_contacts=[item.model_dump() for item in data.emergency_contacts],
                          referred_doctor_id=doctor.id if doctor else None)
    db().add(profile)
    from doctor.notifications import queue_notification
    queue_notification(profile.referred_doctor_id, 'patient_connected', 'profile:' + profile.id)
    audit('care_profile_created', user.id, user.id)
    db().commit()
    return jsonify(profile=profile_data(profile)), 201


def list_profiles(user, page, per_page, module=None):
    from services.profile_doctor_access import doctor_profile_filter
    query = select(CareProfile).where(patient_profile_access(user)) if user.role == 'PATIENT' else select(CareProfile).where(doctor_profile_filter(user))
    query=query.where(CareProfile.deleted_at.is_(None))
    if module:
        if module not in ('child', 'adult', 'women'):
            raise APIError(422, 'invalid_module', 'module must be child, adult or women')
        query = query.where(CareProfile.module == module)
    rows, total = paginate(query.order_by(CareProfile.created_at, CareProfile.id), page, per_page)
    items=[]
    for item in rows:
        if item.module == 'women':
            from services.women_workspace import is_primary
            if not is_primary(user, item):
                items.append(dict(id=item.id,full_name=item.name,module=item.module,profile_type=item.profile_type,
                    created_at=item.created_at.isoformat()+'Z',family_access=False,linked_member=True))
                continue
        invitation=db().scalar(select(FamilyInvitation).where(FamilyInvitation.profile_id==item.id,FamilyInvitation.accepted_at.is_not(None))) if item.module in ('adult','women') else None
        if user.role=='PATIENT' and item.owner_id==user.id and invitation and not (invitation.pending or {}).get('family_access'):
            items.append(dict(id=item.id,full_name=item.name,module=item.module,profile_type=item.profile_type,created_at=item.created_at.isoformat()+'Z',family_access=False,linked_member=True))
        else:
            items.append(dict(**profile_data(item),family_access=True))
    return jsonify(items=items, total=total, page=page, per_page=per_page)


def connect_profile(user, profile_id, referral_id):
    doctor, _ = resolve_referral(referral_id, lock=True)
    profile = accessible_profile(user, profile_id, lock=True)
    if profile.referred_doctor_id and profile.referred_doctor_id != doctor.id:
        raise APIError(409, 'doctor_already_connected', 'Profile is already connected to another doctor')
    profile.referred_doctor_id = doctor.id
    from doctor.notifications import queue_notification
    queue_notification(doctor.id, 'patient_connected', 'profile:' + profile.id)
    audit('care_profile_doctor_connected', doctor.id, user.id)
    db().commit()
    return jsonify(profile=profile_data(profile))


def list_reports(user, profile_id, page, per_page):
    profile=accessible_profile(user, profile_id)
    from services.profile_doctor_access import require_scope
    grant=require_scope(user,profile,'reports')
    query=select(CareReport).where(CareReport.profile_id == profile_id)
    if grant and grant.report_ids is not None:query=query.where(CareReport.id.in_(grant.report_ids))
    if user.role=='DOCTOR' and profile.module=='child':query=query.where(CareReport.id.in_(shared_report_ids(profile_id)))
    rows, total = paginate(query.order_by(
        CareReport.created_at.desc(), CareReport.id), page, per_page)
    from services.care_uploads import report_data
    return jsonify(items=[report_data(item) for item in rows], total=total, page=page, per_page=per_page)


def accessible_report(user, profile_id, report_id):
    profile=accessible_profile(user, profile_id)
    from services.profile_doctor_access import require_scope
    grant=require_scope(user,profile,'reports')
    if grant and grant.report_ids is not None and report_id not in grant.report_ids:raise APIError(404,'report_not_found','Report is outside the shared permission')
    if user.role=='DOCTOR' and profile.module=='child' and report_id not in shared_report_ids(profile_id):
        raise APIError(404,'report_not_found','Report is not shared in an authorised child care area')
    report = db().scalar(select(CareReport).where(CareReport.id == report_id, CareReport.profile_id == profile_id))
    if not report:
        raise APIError(404, 'report_not_found', 'Medical report not found')
    return report


def update_profile(user,profile_id,data):
    profile=accessible_profile(user,profile_id,lock=True)
    if profile.profile_type=='self':
        raise APIError(409,'self_identity_locked','Account identity is managed separately')
    from datetime import date
    if profile.module=='child':
        age=date.today().year-data.date_of_birth.year-((date.today().month,date.today().day)<(data.date_of_birth.month,data.date_of_birth.day))
        if age>12:raise APIError(422,'child_age','Child Care supports ages 0?12')
        from core.models import ChildRecord
        for row in db().scalars(select(ChildRecord).where(ChildRecord.profile_id==profile.id,ChildRecord.deleted_at.is_(None))):
            if row.data.get('date','9999')<data.date_of_birth.isoformat():
                raise APIError(422,'records_before_birth','Existing records precede this birth date; review their dates first')
    if profile.parent_profile_id:
        parent=db().get(CareProfile,profile.parent_profile_id)
        if parent and parent.dob>=data.date_of_birth:raise APIError(422,'parent_age','The parent must be older than the child')
    for key,value in [('name',data.full_name),('dob',data.date_of_birth),('guardian_name',data.guardian_name.strip()),('guardian_contact',data.guardian_contact),('emergency_contacts',[item.model_dump() for item in data.emergency_contacts])]:
        setattr(profile,key,value)
    audit('care_profile_updated',user.id,user.id)
    db().commit()
    return jsonify(profile=profile_data(profile))


def delete_profile(user,profile_id):
    profile=accessible_profile(user,profile_id,lock=True)
    if profile.profile_type=='self':raise APIError(409,'self_profile_required','Your account self profile cannot be removed here')
    profile.deleted_at=now()
    audit('care_profile_removed',user.id,user.id)
    db().commit()
    return jsonify(message='Profile removed. Its private records are retained and no longer accessible through the care workspace.')


def shared_report_ids(profile_id):
    from core.models import ChildRecord
    ids=set()
    for row in db().scalars(select(ChildRecord).where(ChildRecord.profile_id==profile_id,ChildRecord.deleted_at.is_(None),ChildRecord.kind.in_(['vaccination','growth','nutrition','care']))):
        for key in ('source_report_id','certificate_id'):
            if row.data.get(key):ids.add(row.data[key])
    return list(ids)
