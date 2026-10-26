import uuid
from datetime import datetime, timezone
from sqlalchemy import Uuid
from sqlalchemy import Column as C, String as S, Text, Boolean as B, Integer as I, DateTime as DT
from sqlalchemy import ForeignKey as FK, CheckConstraint as CK, UniqueConstraint as UQ
from core.database import Base


def now():
    """All stored timestamps are UTC (timestamp without time zone)."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def uid():
    return str(uuid.uuid4())


def primary_id():
    return C(Uuid(as_uuid=False), primary_key=True, default=uid)


def user_fk(**kw):
    return C(Uuid(as_uuid=False), FK('familycare.users.id', ondelete='CASCADE'), **kw)


class User(Base):
    __tablename__ = 'users'
    __table_args__ = (
        CK("role IN ('SUPERADMIN','ADMIN','DOCTOR','PATIENT')", name='role'),
        CK("approval_status IN ('PENDING_EMAIL_VERIFICATION','PENDING_APPROVAL','APPROVED','REJECTED')", name='approval'),
        CK("account_status IN ('ACTIVE','SUSPENDED')", name='status'))
    id = primary_id()
    public_id = C(S(40), unique=True, nullable=False)
    username = C(S(80), unique=True)
    full_name = C(S(120), nullable=False)
    email = C(S(254), unique=True, nullable=False)
    phone_number = C(S(20))
    password_hash = C(Text, nullable=False)
    role = C(S(20), nullable=False, index=True)
    email_verified = C(B, default=False, nullable=False)
    approval_status = C(S(32), default='PENDING_EMAIL_VERIFICATION', nullable=False, index=True)
    account_status = C(S(16), default='ACTIVE', nullable=False)
    must_change_password = C(B, default=False, nullable=False)
    created_at = C(DT, default=now, nullable=False)
    updated_at = C(DT, default=now, onupdate=now, nullable=False)
    last_login_at = C(DT)


class AdminProfile(Base):
    __tablename__ = 'admin_profiles'
    user_id = user_fk(primary_key=True)


class PatientProfile(Base):
    __tablename__ = 'patient_profiles'
    user_id = user_fk(primary_key=True)


class DoctorProfile(Base):
    __tablename__ = 'doctor_profiles'
    __table_args__ = (UQ('registering_council', 'medical_registration_number'),)
    user_id = user_fk(primary_key=True)
    qualification = C(S(200), nullable=False)
    specialization = C(S(200))
    medical_registration_number = C(S(100), nullable=False)
    registering_council = C(S(200), nullable=False)
    nmr_id = C(S(100), unique=True)
    verification_status = C(S(32), default='PENDING', nullable=False)
    approved_by = C(Uuid(as_uuid=False), FK('familycare.users.id'))
    approved_at = C(DT)


class OTPChallenge(Base):
    __tablename__ = 'otp_challenges'
    __table_args__ = (CK("purpose IN ('verify_email','login','reset_password','change_password')", name='purpose'),)
    id = primary_id()
    user_id = user_fk(nullable=False, index=True)
    purpose = C(S(32), nullable=False)
    code_hash = C(S(64))
    attempts = C(I, default=0, nullable=False)
    consumed_at = C(DT)
    expires_at = C(DT, nullable=False)
    created_at = C(DT, default=now, nullable=False)


class ApprovalRequest(Base):
    __tablename__ = 'approval_requests'
    id = primary_id()
    applicant_id = C(Uuid(as_uuid=False), FK('familycare.users.id', ondelete='CASCADE'), unique=True, nullable=False)
    applicant_role = C(S(20), nullable=False)
    requested_at = C(DT, default=now, nullable=False)
    status = C(S(20), default='PENDING', nullable=False, index=True)
    reviewed_by = C(Uuid(as_uuid=False), FK('familycare.users.id'))
    reviewed_at = C(DT)
    rejection_reason = C(S(500))


class UserSession(Base):
    __tablename__ = 'user_sessions'
    id = primary_id()
    user_id = user_fk(nullable=False, index=True)
    transport = C(S(10), default='bearer', nullable=False)
    csrf_hash = C(S(64))
    created_at = C(DT, default=now, nullable=False)
    expires_at = C(DT, nullable=False)
    revoked_at = C(DT)


class RefreshToken(Base):
    __tablename__ = 'refresh_tokens'
    id = primary_id()
    session_id = C(Uuid(as_uuid=False), FK('familycare.user_sessions.id', ondelete='CASCADE'), nullable=False, index=True)
    token_hash = C(S(64), unique=True, nullable=False)
    expires_at = C(DT, nullable=False)
    created_at = C(DT, default=now, nullable=False)
    consumed_at = C(DT)


class PasswordResetEvent(Base):
    __tablename__ = 'password_reset_events'
    id = primary_id()
    user_id = user_fk(nullable=False, index=True)
    challenge_id = C(Uuid(as_uuid=False), FK('familycare.otp_challenges.id'), nullable=False)
    created_at = C(DT, default=now, nullable=False)


class EmailNotification(Base):
    __tablename__ = 'email_notifications'
    id = primary_id()
    user_id = user_fk(nullable=False, index=True)
    challenge_id = C(Uuid(as_uuid=False), FK('familycare.otp_challenges.id'))
    template = C(S(40), nullable=False)
    # OTP plaintext is never persisted; worker derives code from keyed challenge ID.
    context_json = C(Text, default='{}', nullable=False)
    status = C(S(16), default='PENDING', nullable=False, index=True)
    attempts = C(I, default=0, nullable=False)
    available_at = C(DT, default=now, nullable=False, index=True)
    sent_at = C(DT)
    created_at = C(DT, default=now, nullable=False)


class AuditLog(Base):
    __tablename__ = 'audit_logs'
    id = primary_id()
    actor_id = C(Uuid(as_uuid=False), FK('familycare.users.id'))
    target_id = C(Uuid(as_uuid=False), FK('familycare.users.id'))
    action = C(S(80), nullable=False, index=True)
    created_at = C(DT, default=now, nullable=False, index=True)
