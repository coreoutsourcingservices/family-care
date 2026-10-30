from flask import jsonify
from sqlalchemy import select, func
from core.database import db
from core.models import User, DoctorProfile, PatientProfile, now
from core.errors import APIError
from services.repository import audit, serialize_user


def doctor_details(user, profile=None):
    profile = profile or db().get(DoctorProfile, user.id)
    return dict(referral_id=profile.referral_id, public_id=user.public_id,
                full_name=user.full_name, email=user.email, mobile_number=user.phone_number,
                account_status=user.account_status, approval_status=user.approval_status)


def care_doctor_details(user):
    """Professional card for an already connected profile; never expose degree images."""
    from flask import current_app
    profile=db().get(DoctorProfile,user.id)
    result=doctor_details(user,profile)
    result.update(id=user.id,qualification=profile.qualification,specialization=profile.specialization,
                  registering_council=profile.registering_council,years_of_experience=profile.years_of_experience,
                  clinic_address=profile.clinic_address,profile_photo_url=None)
    photo=(profile.onboarding_images or {}).get('profile_photo')
    if photo and all(current_app.config.get('CLOUDINARY_'+key) for key in ('CLOUD_NAME','API_KEY','API_SECRET')):
        import time
        import cloudinary.utils
        from services.care_uploads import credentials
        result['profile_photo_url']=cloudinary.utils.private_download_url(photo['public_id'],photo['format'],
            resource_type='image',type='authenticated',expires_at=int(time.time())+300,secure=True,**credentials())
    return result


def resolve_referral(referral_id, lock=False):
    query = select(User, DoctorProfile).join(DoctorProfile, DoctorProfile.user_id == User.id).where(
        func.lower(DoctorProfile.referral_id) == referral_id.lower(), User.role == 'DOCTOR')
    if lock:
        query = query.with_for_update()
    result = db().execute(query).first()
    if (not result or not result.User.email_verified or result.User.approval_status != 'APPROVED'
            or result.User.account_status != 'ACTIVE'):
        raise APIError(422, 'invalid_referral', 'Referral ID must belong to an approved, active doctor')
    return result.User, result.DoctorProfile


def own_referral(user):
    return jsonify(doctor=doctor_details(user))


def connect_patient(user, referral_id):
    doctor, _ = resolve_referral(referral_id, lock=True)
    profile = db().scalar(select(PatientProfile).where(PatientProfile.user_id == user.id).with_for_update())
    if not profile:
        raise APIError(409, 'profile_unavailable', 'Patient profile is unavailable')
    if profile.referred_by_doctor_id and profile.referred_by_doctor_id != doctor.id:
        raise APIError(409, 'doctor_already_connected', 'Patient is already connected to another doctor')
    if not profile.referred_by_doctor_id:
        profile.referred_by_doctor_id, profile.referred_at = doctor.id, now()
        audit('doctor_referral_connected', doctor.id, user.id)
        from doctor.notifications import queue_notification
        queue_notification(doctor.id,'patient_connected','account:'+user.id)
        db().commit()
    return jsonify(doctor=doctor_details(doctor), message='Patient connected to doctor')


def connected_doctor(user):
    profile = db().get(PatientProfile, user.id)
    doctor = db().get(User, profile.referred_by_doctor_id) if profile and profile.referred_by_doctor_id else None
    return jsonify(doctor=doctor_details(doctor) if doctor else None)


def doctor_patients(user, page, per_page):
    from services.approvals import paginate
    query = select(User).join(PatientProfile, PatientProfile.user_id == User.id).where(
        PatientProfile.referred_by_doctor_id == user.id, User.role == 'PATIENT').order_by(User.created_at, User.id)
    rows, total = paginate(query, page, per_page)
    return jsonify(items=[serialize_user(item) for item in rows], total=total, page=page, per_page=per_page)
