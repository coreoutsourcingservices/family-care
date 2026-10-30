import uuid
from datetime import datetime, timezone
from sqlalchemy import Uuid, Date, JSON, LargeBinary, Index, text
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
        CK("approval_status IN ('PENDING_EMAIL_VERIFICATION','PROFILE_REQUIRED','PENDING_APPROVAL','APPROVED','REJECTED')", name='approval'),
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
    referred_by_doctor_id = C(Uuid(as_uuid=False), FK('familycare.doctor_profiles.user_id', ondelete='SET NULL'), index=True)
    referred_at = C(DT)


class DoctorProfile(Base):
    __tablename__ = 'doctor_profiles'
    __table_args__ = (UQ('registering_council', 'medical_registration_number'),)
    user_id = user_fk(primary_key=True)
    referral_id = C(S(160), unique=True, nullable=False)
    qualification = C(S(200))
    specialization = C(S(200))
    medical_registration_number = C(S(100))
    registering_council = C(S(200))
    address = C(S(1000))
    clinic_address = C(S(1000))
    years_of_experience = C(I)
    nmr_id = C(S(100), unique=True)
    verification_status = C(S(32), default='PENDING', nullable=False)
    verification_check = C(JSON)
    onboarding_images = C(JSON)
    approved_by = C(Uuid(as_uuid=False), FK('familycare.users.id'))
    approved_at = C(DT)


# Covers ORM callers such as bootstrap/import tools as well as normal registration.
from sqlalchemy import event, select


@event.listens_for(DoctorProfile, 'before_insert')
def assign_doctor_referral(mapper, connection, profile):
    if not profile.referral_id:
        from core.referrals import make_referral_id
        user = connection.execute(select(User.full_name, User.public_id).where(User.id == profile.user_id)).one()
        profile.referral_id = make_referral_id(user.full_name, user.public_id)


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


class CareProfile(Base):
    __tablename__ = 'care_profiles'
    __table_args__ = (
        CK("module IN ('child','women','adult')", name='module'),
        CK("profile_type IN ('self','member')", name='profile_type'),
        Index('uq_care_profiles_self_owner', 'owner_id', unique=True,
              postgresql_where=text("profile_type = 'self'"), sqlite_where=text("profile_type = 'self'"))
    )
    id = primary_id()
    owner_id = user_fk(nullable=False, index=True)
    module = C(S(10), nullable=False)
    name = C(S(120), nullable=False)
    dob = C(Date, nullable=False)
    guardian_contact = C(S(20), nullable=False, default='')
    emergency_contacts = C(JSON, nullable=False, default=list)
    referred_doctor_id = C(Uuid(as_uuid=False), FK('familycare.users.id'), index=True)
    profile_type = C(S(10), nullable=False, default='member', server_default='member')
    parent_profile_id = C(Uuid(as_uuid=False), FK('familycare.care_profiles.id', ondelete='SET NULL'))
    created_at = C(DT, default=now, nullable=False)
    updated_at = C(DT, default=now, onupdate=now, nullable=False)


class AdultRecord(Base):
    __tablename__ = 'adult_records'
    id = primary_id()
    profile_id = C(Uuid(as_uuid=False), FK('familycare.care_profiles.id', ondelete='CASCADE'), nullable=False, index=True)
    kind = C(S(32), nullable=False)
    data = C(JSON, nullable=False)
    created_at = C(DT, default=now, nullable=False)
    updated_at = C(DT, default=now, onupdate=now, nullable=False)
    deleted_at = C(DT)


class AdultRecordRevision(Base):
    __tablename__ = 'adult_record_revisions'
    id = primary_id()
    record_id = C(Uuid(as_uuid=False), FK('familycare.adult_records.id', ondelete='CASCADE'), nullable=False, index=True)
    actor_id = user_fk(nullable=False)
    action = C(S(12), nullable=False)
    data = C(JSON, nullable=False)
    created_at = C(DT, default=now, nullable=False)


class ChildRecord(Base):
    __tablename__ = 'child_records'
    __table_args__ = (CK("kind IN ('vaccination','history','growth','nutrition','consultation','consultation_request','care')", name='kind'),)
    id = primary_id()
    profile_id = C(Uuid(as_uuid=False), FK('familycare.care_profiles.id', ondelete='CASCADE'), nullable=False, index=True)
    kind = C(S(32), nullable=False)
    data = C(JSON, nullable=False)
    created_at = C(DT, default=now, nullable=False)
    updated_at = C(DT, default=now, onupdate=now, nullable=False)
    deleted_at = C(DT)


class ChildRecordRevision(Base):
    __tablename__ = 'child_record_revisions'
    id = primary_id()
    record_id = C(Uuid(as_uuid=False), FK('familycare.child_records.id', ondelete='CASCADE'), nullable=False, index=True)
    actor_id = user_fk(nullable=False)
    action = C(S(12), nullable=False)
    data = C(JSON, nullable=False)
    created_at = C(DT, default=now, nullable=False)


class ChildPreferences(Base):
    __tablename__ = 'child_preferences'
    profile_id = C(Uuid(as_uuid=False), FK('familycare.care_profiles.id', ondelete='CASCADE'), primary_key=True)
    in_app = C(B, nullable=False, default=True)
    updated_at = C(DT, default=now, onupdate=now, nullable=False)


class Vaccine(Base):
    __tablename__ = 'vaccines'
    id = primary_id()
    code = C(S(40), unique=True, nullable=False)
    data = C(JSON, nullable=False)
    active = C(B, nullable=False, default=True)
    created_at = C(DT, default=now, nullable=False)
    updated_at = C(DT, default=now, onupdate=now, nullable=False)


class VaccineSchedule(Base):
    __tablename__ = 'vaccine_schedules'
    __table_args__ = (UQ('vaccine_id','schedule_type','dose_code','version'),
                      CK("status IN ('DRAFT','IN_REVIEW','APPROVED','PUBLISHED','RETIRED')", name='status'))
    id = primary_id()
    vaccine_id = C(Uuid(as_uuid=False), FK('familycare.vaccines.id'), nullable=False, index=True)
    schedule_type = C(S(8), nullable=False)
    dose_code = C(S(40), nullable=False)
    version = C(S(80), nullable=False)
    status = C(S(16), nullable=False, default='DRAFT', index=True)
    data = C(JSON, nullable=False)
    created_by = user_fk(nullable=False)
    reviewer_id = user_fk()
    reviewed_hash = C(S(64))
    reviewed_at = C(DT)
    published_at = C(DT)
    created_at = C(DT, default=now, nullable=False)
    updated_at = C(DT, default=now, onupdate=now, nullable=False)


class VaccineAudit(Base):
    __tablename__ = 'vaccine_audit'
    id = primary_id()
    vaccine_id = C(Uuid(as_uuid=False), FK('familycare.vaccines.id'), index=True)
    schedule_id = C(Uuid(as_uuid=False), FK('familycare.vaccine_schedules.id'), index=True)
    actor_id = user_fk(nullable=False)
    action = C(S(40), nullable=False)
    data = C(JSON, nullable=False)
    created_at = C(DT, default=now, nullable=False)


class ChildVaccinationContext(Base):
    __tablename__ = 'child_vaccination_context'
    profile_id = C(Uuid(as_uuid=False), FK('familycare.care_profiles.id', ondelete='CASCADE'), primary_key=True)
    data = C(JSON, nullable=False)
    updated_at = C(DT, default=now, onupdate=now, nullable=False)


class VaccineReminderDelivery(Base):
    __tablename__ = 'vaccine_reminder_deliveries'
    __table_args__ = (UQ('profile_id','schedule_id','event_date','channel'),)
    id = primary_id()
    profile_id = C(Uuid(as_uuid=False), FK('familycare.care_profiles.id', ondelete='CASCADE'), nullable=False)
    schedule_id = C(Uuid(as_uuid=False), FK('familycare.vaccine_schedules.id'), nullable=False)
    event_date = C(Date, nullable=False)
    channel = C(S(12), nullable=False)
    notification_id = C(Uuid(as_uuid=False), FK('familycare.email_notifications.id'))


class CareReport(Base):
    __tablename__ = 'care_reports'
    id = primary_id()
    profile_id = C(Uuid(as_uuid=False), FK('familycare.care_profiles.id', ondelete='CASCADE'), nullable=False, index=True)
    name = C(S(255), nullable=False)
    content_type = C(S(80), nullable=False)
    content = C(LargeBinary)
    storage_provider = C(S(16), nullable=False, default='database', server_default='database')
    cloudinary_public_id = C(S(512), unique=True)
    cloudinary_asset_id = C(S(100))
    secure_url = C(Text)
    folder = C(S(512))
    resource_type = C(S(16))
    delivery_type = C(S(20))
    file_format = C(S(20))
    size_bytes = C(I)
    created_at = C(DT, default=now, nullable=False)


class ReportText(Base):
    __tablename__ = 'report_texts'
    report_id = C(Uuid(as_uuid=False), FK('familycare.care_reports.id', ondelete='CASCADE'), primary_key=True)
    requested_by = user_fk(nullable=False)
    status = C(S(16), nullable=False, default='QUEUED')
    options = C(JSON, nullable=False)
    result = C(JSON, nullable=False, default=dict)
    error_code = C(S(60))
    lease_id = C(S(36))
    started_at = C(DT)
    created_at = C(DT, default=now, nullable=False)
    updated_at = C(DT, default=now, onupdate=now, nullable=False)

# Registered here so migrations and isolated test metadata include the doctor inbox.
from doctor.notification_models import DoctorNotification, DoctorPushSubscription, DoctorPushDelivery
