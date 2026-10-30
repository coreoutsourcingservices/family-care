import json
from flask import jsonify
from sqlalchemy import select, func, or_
from core.database import db
from core.errors import APIError
from core.models import User, ApprovalRequest, DoctorProfile, EmailNotification, AuditLog, now
from services.repository import user_by_id, serialize_user, revoke_sessions, audit
from core.security import verify_password


def paginate(query, page=1, per_page=25):
    total = db().scalar(select(func.count()).select_from(query.order_by(None).subquery()))
    return db().scalars(query.offset((page-1)*per_page).limit(per_page)).all(), total


def listing(role, page, per_page, status=None, pending=False):
    query = select(User).where(User.role == role)
    if role == 'DOCTOR':
        query = query.where(User.id.in_(select(ApprovalRequest.applicant_id).where(ApprovalRequest.applicant_role == 'DOCTOR')))
        status = {'pending': 'PENDING_APPROVAL', 'verified': 'APPROVED', 'rejected': 'REJECTED'}.get(status, status)
    if pending:
        query = query.where(User.approval_status == 'PENDING_APPROVAL', User.email_verified.is_(True))
    elif status:
        query = query.where(User.approval_status == status)
    rows, total = paginate(query.order_by(User.created_at, User.id), page, per_page)
    if role == 'PATIENT':
        from services.patient_directory import counts_for_users
        profile_counts = counts_for_users([user.id for user in rows])
    items = []
    for user in rows:
        item = serialize_user(user)
        if role == 'PATIENT':
            item['profile_counts'] = profile_counts[user.id]
        if role == 'DOCTOR':
            profile = db().get(DoctorProfile, user.id)
            item['doctor'] = {k: getattr(profile, k) for k in ('qualification', 'specialization',
                              'medical_registration_number', 'registering_council', 'nmr_id', 'verification_status',
                              'address', 'clinic_address', 'years_of_experience', 'verification_check')}
            from doctor.onboarding_images import image_details
            item['doctor']['images'] = image_details(profile)
        items.append(item)
    return jsonify(items=items, total=total, page=page, per_page=per_page)


def review(actor, identifier, role, approve, reason=None):
    if (role == 'ADMIN' and actor.role != 'SUPERADMIN') or (role == 'DOCTOR' and actor.role != 'ADMIN'):
        raise APIError(403, 'forbidden', 'This role cannot review the requested account')
    user = user_by_id(identifier, lock=True)
    if not user or user.role != role:
        raise APIError(404, 'not_found', 'Applicant not found')
    application = db().scalar(select(ApprovalRequest).where(ApprovalRequest.applicant_id == user.id).with_for_update())
    if not application or application.status != 'PENDING' or user.approval_status != 'PENDING_APPROVAL':
        raise APIError(409, 'invalid_state', 'Applicant is not pending approval')
    if not user.email_verified:
        raise APIError(409, 'email_unverified', 'Email must be verified first')
    status = 'APPROVED' if approve else 'REJECTED'
    user.approval_status = status
    application.status, application.reviewed_by, application.reviewed_at = status, actor.id, now()
    application.rejection_reason = None if approve else reason
    if role == 'DOCTOR':
        profile = db().get(DoctorProfile, user.id)
        profile.verification_status = status
        profile.approved_by = actor.id if approve else None
        profile.approved_at = now() if approve else None
    revoke_sessions(user.id)
    db().add(EmailNotification(user_id=user.id, template=role.lower() + '_' + status.lower(),
                               context_json=json.dumps({'reason': reason or ''})))
    if role == 'DOCTOR':
        from doctor.notifications import queue_notification
        queue_notification(user.id, 'profile_approved' if approve else 'profile_rejected', 'review:' + application.id + ':' + str(application.reviewed_at))
    if role!='DOCTOR':
        from services.notifications import enqueue
        enqueue(user.id,'account_approved' if approve else 'account_rejected','Account review updated','Sign in to review your account status.',event_key='review:'+application.id+':'+str(application.reviewed_at))
    audit('approval_' + status.lower(), user.id, actor.id)
    db().commit()
    return jsonify(user=serialize_user(user), email_status='queued')


def account_status(actor, identifier, role, active):
    if (role == 'ADMIN' and actor.role != 'SUPERADMIN') or (role == 'DOCTOR' and actor.role != 'ADMIN'):
        raise APIError(403, 'forbidden', 'Cannot manage this account role')
    user = user_by_id(identifier, lock=True)
    if not user or user.role != role:
        raise APIError(404, 'not_found', 'Account not found')
    user.account_status = 'ACTIVE' if active else 'SUSPENDED'
    revoke_sessions(user.id)
    audit('account_' + user.account_status.lower(), user.id, actor.id)
    db().commit()
    return jsonify(user=serialize_user(user))


def dashboard():
    counts = db().execute(select(User.role, User.approval_status, func.count())
                           .where(or_(User.role != 'DOCTOR', User.id.in_(select(ApprovalRequest.applicant_id))))
                           .group_by(User.role, User.approval_status)).all()
    return jsonify(counts=[{'role': role, 'approval_status': status, 'count': count}
                           for role, status, count in counts])


def audit_logs(page, per_page):
    rows, total = paginate(select(AuditLog).order_by(AuditLog.created_at.desc(), AuditLog.id), page, per_page)
    return jsonify(items=[{'id': r.id, 'actor_id': r.actor_id, 'target_id': r.target_id,
                            'action': r.action, 'created_at': r.created_at.isoformat()+'Z'} for r in rows], total=total)


def doctor_status(data):
    from services.repository import find_user
    user = find_user(str(data.email), 'DOCTOR')
    if not verify_password(user.password_hash if user else None, data.password):
        raise APIError(401, 'invalid_credentials', 'Invalid credentials')
    application = db().scalar(select(ApprovalRequest).where(ApprovalRequest.applicant_id == user.id))
    return jsonify(public_id=user.public_id, email_verified=user.email_verified,
                   doctor_status=serialize_user(user)['doctor_status'],
                   approval_status=user.approval_status, account_status=user.account_status,
                   rejection_reason=application.rejection_reason if application else None)


def resubmit_doctor(data):
    from services.repository import find_user
    user = find_user(str(data.email), 'DOCTOR', lock=True)
    if not verify_password(user.password_hash if user else None, data.password):
        raise APIError(401, 'invalid_credentials', 'Invalid credentials')
    if user.approval_status != 'REJECTED' or not user.email_verified or user.account_status != 'ACTIVE':
        raise APIError(409, 'invalid_state', 'Only verified active rejected doctors may resubmit')
    profile = db().get(DoctorProfile, user.id)
    profile.qualification = data.qualification.strip().upper()
    profile.medical_registration_number = data.medical_registration_number.strip().upper()
    profile.registering_council = data.registering_council.strip().upper()
    profile.verification_status = 'PENDING'
    profile.verification_check = None
    application = db().scalar(select(ApprovalRequest).where(ApprovalRequest.applicant_id == user.id).with_for_update())
    application.status, application.requested_at = 'PENDING', now()
    application.reviewed_by = application.reviewed_at = application.rejection_reason = None
    user.approval_status = 'PENDING_APPROVAL'
    audit('doctor_resubmitted', user.id, user.id)
    db().commit()
    return jsonify(message='Resubmitted for review', user=serialize_user(user)), 202
