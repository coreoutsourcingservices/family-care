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
    if find_user(str(data.email)):
        raise APIError(409, 'account_exists', 'Account already exists; use login or reset password')
    user = User(id=uid(), public_id=None, full_name=data.full_name, email=str(data.email).lower(),
                phone_number=data.mobile_number, password_hash=password_hasher.hash(data.password), role=role)
    if db().bind.dialect.name == 'sqlite':
        # Only a test adapter; real public IDs always come from the PostgreSQL trigger.
        counter = db().info.setdefault('test_ids', {})
        counter[role] = counter.get(role, 0) + 1
        user.public_id = {'ADMIN': 'A', 'DOCTOR': 'D', 'PATIENT': 'C'}[role] + secrets.token_hex(6)
    db().add(user)
    db().flush()
    db().refresh(user)
    if role == 'DOCTOR':
        db().add(DoctorProfile(user_id=user.id, qualification=data.qualification,
                              specialization=data.specialization, medical_registration_number=data.medical_registration_number,
                              registering_council=data.registering_council, nmr_id=data.nmr_id))
    else:
        db().add((AdminProfile if role == 'ADMIN' else PatientProfile)(user_id=user.id))
    # Newly inserted user row is owned by this transaction; issue() is serialized.
    challenge = otp.issue(user, 'verify_email')
    audit('registered', user.id, user.id)
    db().commit()
    return jsonify(public_id=user.public_id, user_id=user.id, approval_status=user.approval_status,
                   message='Verify email OTP before continuing', **challenge), 202


def request_verification(data):
    user = find_user(str(data.email), lock=True)
    if not verify_password(user.password_hash if user else None, data.password):
        raise APIError(401, 'invalid_credentials', 'Invalid credentials')
    if user.email_verified or user.account_status != 'ACTIVE':
        raise APIError(409, 'invalid_state', 'Account is verified or unavailable')
    result = otp.issue(user, 'verify_email')
    db().commit()
    return jsonify(**result), 202


def verify_email(data, role):
    user, challenge = otp.resolve(data.challenge_token, 'verify_email', role)
    otp.consume(challenge, data.otp)
    if user.email_verified:
        raise APIError(409, 'already_verified', 'Email already verified')
    user.email_verified = True
    audit('email_verified', user.id, user.id)
    if role == 'PATIENT':
        user.approval_status = 'APPROVED'
        return issue_session(user)
    user.approval_status = 'PENDING_APPROVAL'
    db().add(ApprovalRequest(applicant_id=user.id, applicant_role=role))
    audit('approval_requested', user.id, user.id)
    db().commit()
    return jsonify(user=serialize_user(user), message='Email verified. Waiting for approval.'), 202


def login(data, role):
    identifier = data.username if role == 'SUPERADMIN' else str(data.email)
    user = find_user(identifier, role, username=role == 'SUPERADMIN', lock=True)
    if not verify_password(user.password_hash if user else None, data.password):
        audit('login_failed', user.id if user else None)
        db().commit()
        raise APIError(401, 'invalid_credentials', 'Invalid credentials')
    if user.account_status != 'ACTIVE':
        raise APIError(403, 'account_restricted', 'Account is suspended')
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
    if role in ('ADMIN', 'PATIENT'):
        result = otp.issue(user, 'login')
        db().commit()
        return jsonify(requires_otp=True, **result), 202
    return issue_session(user)


def verify_login(data, role):
    user, challenge = otp.resolve(data.challenge_token, 'login', role)
    eligible(user)
    otp.consume(challenge, data.otp)
    return issue_session(user)


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
