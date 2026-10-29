import secrets
from datetime import timedelta
from flask import jsonify
from sqlalchemy import select, text
from core.database import db
from core.errors import APIError
from core.models import User, AdminProfile, DoctorProfile, PatientProfile, ApprovalRequest, OTPChallenge, PasswordResetEvent, now, uid
from core.security import password_hasher, verify_password, eligible
from services.repository import find_user, serialize_user, revoke_sessions, audit
from services import otp
from services.sessions import issue_session


def register(data, role):
    from services.signup import register_pending
    return register_pending(data, role)


def create_verified_user(values, role):
    if find_user(values['email']):
        raise APIError(409, 'account_exists', 'Account already exists; use login or reset password')
    referred_doctor = None
    if role == 'PATIENT' and values.get('referral_id'):
        from services.referrals import resolve_referral
        referred_doctor, _ = resolve_referral(values['referral_id'], lock=True)
    user = User(id=uid(), public_id=None, full_name=values['full_name'], email=values['email'],
                phone_number=values['mobile_number'], password_hash=values['password_hash'], role=role,
                email_verified=True,
                approval_status='APPROVED' if role == 'PATIENT' else 'PROFILE_REQUIRED' if role == 'DOCTOR' else 'PENDING_APPROVAL')
    if db().bind.dialect.name == 'sqlite':
        user.public_id = {'ADMIN': 'A', 'DOCTOR': 'D', 'PATIENT': 'C'}[role] + secrets.token_hex(6)
    db().add(user)
    db().flush()
    db().refresh(user)
    if role == 'DOCTOR':
        fields = ('qualification', 'specialization', 'medical_registration_number', 'registering_council', 'nmr_id')
        db().add(DoctorProfile(user_id=user.id, **{k: values.get(k) for k in fields}))
    elif role == 'PATIENT':
        db().add(PatientProfile(user_id=user.id, referred_by_doctor_id=referred_doctor.id if referred_doctor else None,
                                referred_at=now() if referred_doctor else None))
        if referred_doctor:
            audit('doctor_referral_connected', referred_doctor.id, user.id)
    else:
        db().add(AdminProfile(user_id=user.id))
    audit('registered', user.id, user.id)
    audit('email_verified', user.id, user.id)
    if role == 'PATIENT':
        return issue_session(user)
    if role == 'DOCTOR':
        db().commit()
        from services.doctor_onboarding import setup_response
        return setup_response(user)
    db().add(ApprovalRequest(applicant_id=user.id, applicant_role=role))
    audit('approval_requested', user.id, user.id)
    db().commit()
    return jsonify(user=serialize_user(user), message='Email verified. Waiting for approval.'), 202


def request_verification(data):
    from services.signup import restart_pending
    pending = restart_pending(data)
    if pending is not None:
        return pending
    user = find_user(str(data.email), lock=True)
    if not verify_password(user.password_hash if user else None, data.password):
        raise APIError(401, 'invalid_credentials', 'Invalid credentials')
    if user.email_verified or user.account_status != 'ACTIVE':
        raise APIError(409, 'invalid_state', 'Account is verified or unavailable')
    result = otp.issue(user, 'verify_email')
    db().commit()
    return jsonify(**result), 202


def verify_email(data, role):
    from services.signup import verify_pending
    claims = otp.decode_token(data.challenge_token, 'challenge')
    if claims.get('pending_signup'):
        return verify_pending(data, role, claims)
    user, challenge = otp.resolve(data.challenge_token, 'verify_email', role)
    otp.consume(challenge, data.otp)
    if user.email_verified:
        raise APIError(409, 'already_verified', 'Email already verified')
    user.email_verified = True
    audit('email_verified', user.id, user.id)
    if role == 'PATIENT':
        user.approval_status = 'APPROVED'
        return issue_session(user)
    if role == 'DOCTOR':
        user.approval_status = 'PROFILE_REQUIRED'
        db().commit()
        from services.doctor_onboarding import setup_response
        return setup_response(user)
    user.approval_status = 'PENDING_APPROVAL'
    db().add(ApprovalRequest(applicant_id=user.id, applicant_role=role))
    audit('approval_requested', user.id, user.id)
    db().commit()
    return jsonify(user=serialize_user(user), message='Email verified. Waiting for approval.'), 202


def login(data, role):
    legacy_username = role == 'SUPERADMIN' and not data.email
    identifier = data.username if legacy_username else str(data.email)
    user = find_user(identifier, role, username=legacy_username, lock=True)
    if not verify_password(user.password_hash if user else None, data.password):
        audit('login_failed', user.id if user else None)
        db().commit()
        raise APIError(401, 'invalid_credentials', 'Invalid credentials')
    if user.account_status != 'ACTIVE':
        raise APIError(403, 'account_restricted', 'Account is suspended')
    if role == 'DOCTOR' and user.email_verified:
        if user.approval_status in ('PROFILE_REQUIRED', 'REJECTED'):
            from services.doctor_onboarding import setup_response
            return setup_response(user)
        if user.approval_status == 'PENDING_APPROVAL':
            return jsonify(user=serialize_user(user), message='Your profile is under review.'), 202
    if user.must_change_password:
        # Persisted single-use challenge prevents bootstrap password-change replay.
        challenge = OTPChallenge(id=uid(), user_id=user.id, purpose='change_password',
                                  expires_at=now() + timedelta(minutes=10))
        db().add(challenge)
        db().flush()
        payload = otp.payload(user, challenge)
        db().commit()
        return jsonify(requires_password_change=True, challenge_token=payload['challenge_token'], expires_in=600), 202
    eligible(user)
    if password_hasher.check_needs_rehash(user.password_hash):
        user.password_hash = password_hasher.hash(data.password)
    return issue_session(user)


def verify_login(data, role):
    raise APIError(410, 'login_otp_disabled', 'Sign in with email and password; login OTP is no longer required')


def forgot_password(email):
    user = find_user(str(email), lock=True)
    result = None
    if user and user.email_verified and user.account_status == 'ACTIVE':
        try:
            result = otp.issue(user, 'reset_password')
        except APIError as error:
            if error.status != 429:
                raise
    if not result:
        # Indistinguishable shape for unknown, unverified or cooldown accounts.
        dummy = User(id=uid())
        fake = OTPChallenge(id=uid(), purpose='reset_password')
        result = otp.payload(dummy, fake)
    db().commit()
    return jsonify(message='If an eligible account exists, reset instructions are queued.', **result), 202


def reset_password(data):
    user, challenge = otp.resolve(data.challenge_token, 'reset_password')
    otp.consume(challenge, data.otp)
    user.password_hash = password_hasher.hash(data.new_password)
    user.must_change_password = False
    revoke_sessions(user.id)
    db().add(PasswordResetEvent(user_id=user.id, challenge_id=challenge.id))
    audit('password_reset', user.id, user.id)
    db().commit()
    return jsonify(message='Password reset. Sign in again.')


def change_password(user, data, initial=False):
    from flask import current_app
    if user.role == 'SUPERADMIN' and current_app.config['APP_ENV'] == 'production' and data.new_password == 'superadmin@2026':
        raise APIError(422, 'unsafe_password', 'Default development password is prohibited in production')
    if not verify_password(user.password_hash, data.current_password):
        raise APIError(401, 'invalid_credentials', 'Current password is incorrect')
    if verify_password(user.password_hash, data.new_password):
        raise APIError(422, 'password_unchanged', 'Choose a different password')
    user.password_hash = password_hasher.hash(data.new_password)
    user.must_change_password = False
    revoke_sessions(user.id)
    audit('password_changed', user.id, user.id)
    if initial:
        return issue_session(user)
    db().commit()
    return jsonify(message='Password changed. All sessions revoked; sign in again.')


def initial_password(data):
    user, challenge = otp.resolve(data.challenge_token, 'change_password', 'SUPERADMIN')
    if challenge.consumed_at or challenge.expires_at <= now() or not user.must_change_password:
        raise APIError(400, 'challenge_unavailable', 'Password change challenge expired or used')
    challenge.consumed_at = now()
    return change_password(user, data, initial=True)
