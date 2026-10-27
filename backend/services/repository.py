from sqlalchemy import select
from core.database import db
from core.models import User, AuditLog, UserSession, now


def find_user(identifier, role=None, username=False, lock=False):
    query = select(User).where((User.username if username else User.email) == identifier.strip().lower())
    if role:
        query = query.where(User.role == role)
    if lock:
        query = query.with_for_update()
    return db().scalar(query)


def user_by_id(identifier, lock=False):
    query = select(User).where((User.id == identifier) | (User.public_id == identifier))
    # public IDs cannot be compared to PostgreSQL UUID columns.
    import uuid
    try:
        uuid.UUID(identifier)
    except ValueError:
        query = select(User).where(User.public_id == identifier)
    if lock:
        query = query.with_for_update()
    return db().scalar(query)


def serialize_user(user):
    result = {key: getattr(user, key) for key in ('id', 'public_id', 'full_name', 'email',
            'phone_number', 'role', 'email_verified', 'approval_status', 'account_status', 'must_change_password')}
    if user.role == 'DOCTOR':
        from core.models import DoctorProfile
        profile = db().get(DoctorProfile, user.id)
        result['referral_id'] = profile.referral_id if profile else None
    elif user.role == 'PATIENT':
        from core.models import PatientProfile
        from services.referrals import doctor_details
        profile = db().get(PatientProfile, user.id)
        doctor = db().get(User, profile.referred_by_doctor_id) if profile and profile.referred_by_doctor_id else None
        result['referred_doctor'] = doctor_details(doctor) if doctor else None
    return result


def audit(action, target_id=None, actor_id=None):
    db().add(AuditLog(action=action, target_id=target_id, actor_id=actor_id))


def revoke_sessions(user_id):
    from sqlalchemy import update
    db().execute(update(UserSession).where(UserSession.user_id == user_id,
                                          UserSession.revoked_at.is_(None)).values(revoked_at=now()))
