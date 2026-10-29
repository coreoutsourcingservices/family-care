"""Limited-purpose onboarding; setup tokens cannot access clinical routes."""
from flask import jsonify
from sqlalchemy import select, or_
from core.database import db
from core.errors import APIError
from core.models import User, DoctorProfile, ApprovalRequest, now
from core.security import encode_token, decode_token
from services.repository import serialize_user, audit

FIELDS = ('qualification', 'medical_registration_number', 'registering_council',
          'specialization', 'nmr_id', 'address', 'clinic_address', 'years_of_experience')


def setup_response(user):
    profile = db().get(DoctorProfile, user.id)
    application = db().scalar(select(ApprovalRequest).where(ApprovalRequest.applicant_id == user.id))
    return jsonify(user=serialize_user(user), requires_profile_setup=True,
                   setup_token=encode_token(user, 'doctor_profile_setup', 30),
                   doctor={key: getattr(profile, key) for key in FIELDS},
                   rejection_reason=application.rejection_reason if application else None,
                   message='Complete your doctor profile and submit it for approval.'), 202


def submit_profile(data):
    claims = decode_token(data.setup_token, 'doctor_profile_setup')
    user = db().scalar(select(User).where(User.id == claims['sub']).with_for_update())
    if (not user or user.role != 'DOCTOR' or not user.email_verified or
            user.account_status != 'ACTIVE' or user.approval_status not in ('PROFILE_REQUIRED', 'REJECTED')):
        raise APIError(409, 'invalid_state', 'Profile setup is not available for this account')
    values = data.model_dump(exclude={'setup_token'})
    for key in ('qualification', 'medical_registration_number', 'registering_council'):
        values[key] = values[key].strip().upper()
    for key in ('specialization', 'nmr_id'):
        values[key] = (values[key] or '').strip() or None
    duplicate = db().scalar(select(DoctorProfile).where(DoctorProfile.user_id != user.id, or_(
        (DoctorProfile.registering_council == values['registering_council']) &
        (DoctorProfile.medical_registration_number == values['medical_registration_number']),
        DoctorProfile.nmr_id == values['nmr_id'] if values['nmr_id'] else False)))
    if duplicate:
        raise APIError(409, 'conflict', 'Doctor registration already exists')
    profile = db().get(DoctorProfile, user.id)
    for key, value in values.items():
        setattr(profile, key, value)
    profile.verification_status = 'PENDING'
    profile.verification_check = None
    profile.approved_by = profile.approved_at = None
    application = db().scalar(select(ApprovalRequest).where(ApprovalRequest.applicant_id == user.id).with_for_update())
    if application is None:
        application = ApprovalRequest(applicant_id=user.id, applicant_role='DOCTOR')
        db().add(application)
    application.status, application.requested_at = 'PENDING', now()
    application.reviewed_by = application.reviewed_at = application.rejection_reason = None
    user.approval_status = 'PENDING_APPROVAL'
    audit('doctor_profile_submitted', user.id, user.id)
    db().commit()
    return jsonify(user=serialize_user(user), message='Your profile is under review.'), 202
