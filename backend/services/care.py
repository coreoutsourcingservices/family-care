from flask import jsonify
from sqlalchemy import select
from core.database import db
from core.models import CareProfile, CareReport, User, uid
from core.errors import APIError
from services.referrals import resolve_referral, doctor_details
from services.repository import audit
from services.approvals import paginate


def accessible_profile(user, profile_id, lock=False):
    query = select(CareProfile).where(CareProfile.id == profile_id)
    if user.role == 'PATIENT':
        query = query.where(CareProfile.owner_id == user.id)
    elif user.role == 'DOCTOR':
        query = query.where(CareProfile.referred_doctor_id == user.id)
    else:
        raise APIError(403, 'forbidden', 'Profile access denied')
    if lock:
        query = query.with_for_update()
    profile = db().scalar(query)
    if not profile:
        raise APIError(404, 'profile_not_found', 'Care profile not found')
    return profile


def profile_data(profile):
    doctor = db().get(User, profile.referred_doctor_id) if profile.referred_doctor_id else None
    return dict(id=profile.id, profile_type=profile.profile_type, module=profile.module,
                full_name=profile.name, date_of_birth=profile.dob.isoformat(),
                parent_profile_id=profile.parent_profile_id, guardian_contact=profile.guardian_contact,
                emergency_contacts=profile.emergency_contacts,
                doctor=doctor_details(doctor) if doctor else None,
                created_at=profile.created_at.isoformat()+'Z')


def create_profile(user, data):
    if data.profile_type == 'self' and db().scalar(select(CareProfile.id).where(
            CareProfile.owner_id == user.id, CareProfile.profile_type == 'self')):
        raise APIError(409, 'self_profile_exists', 'A self profile already exists')
    parent = accessible_profile(user, str(data.parent_profile_id)) if data.parent_profile_id else None
    if parent and (parent.module == 'child' or parent.dob >= data.date_of_birth):
        raise APIError(422, 'invalid_parent', 'Parent must be an older adult/women profile in your account')
    doctor, _ = resolve_referral(data.referral_id, lock=True) if data.referral_id else (None, None)
    profile = CareProfile(id=uid(), owner_id=user.id, profile_type=data.profile_type,
                          module=data.module, name=data.full_name, dob=data.date_of_birth,
                          parent_profile_id=parent.id if parent else None,
                          guardian_contact=data.guardian_contact,
                          emergency_contacts=[item.model_dump() for item in data.emergency_contacts],
                          referred_doctor_id=doctor.id if doctor else None)
    db().add(profile)
    from doctor.notifications import queue_notification
    queue_notification(profile.referred_doctor_id, 'patient_connected', 'profile:' + profile.id)
    audit('care_profile_created', user.id, user.id)
    db().commit()
    return jsonify(profile=profile_data(profile)), 201


def list_profiles(user, page, per_page, module=None):
    query = select(CareProfile).where(CareProfile.owner_id == user.id) if user.role == 'PATIENT' else select(
        CareProfile).where(CareProfile.referred_doctor_id == user.id)
    if module:
        if module not in ('child', 'adult', 'women'):
            raise APIError(422, 'invalid_module', 'module must be child, adult or women')
        query = query.where(CareProfile.module == module)
    rows, total = paginate(query.order_by(CareProfile.created_at, CareProfile.id), page, per_page)
    return jsonify(items=[profile_data(item) for item in rows], total=total, page=page, per_page=per_page)


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
    accessible_profile(user, profile_id)
    rows, total = paginate(select(CareReport).where(CareReport.profile_id == profile_id).order_by(
        CareReport.created_at.desc(), CareReport.id), page, per_page)
    from services.care_uploads import report_data
    return jsonify(items=[report_data(item) for item in rows], total=total, page=page, per_page=per_page)


def accessible_report(user, profile_id, report_id):
    accessible_profile(user, profile_id)
    report = db().scalar(select(CareReport).where(CareReport.id == report_id, CareReport.profile_id == profile_id))
    if not report:
        raise APIError(404, 'report_not_found', 'Medical report not found')
    return report
