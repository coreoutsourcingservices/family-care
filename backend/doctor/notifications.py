"""Durable doctor inbox; browser push messages never contain patient details."""
import base64
import hmac
import json
from datetime import timedelta
from urllib.parse import urlsplit
from flask import current_app, jsonify, request
from sqlalchemy import select, func, delete
from core.database import db
from core.errors import APIError
from core.http import pagination
from core.models import User, UserSession, now, uid
from core.security import decode_token, encode_token, digest
from doctor.notification_models import DoctorNotification, DoctorPushSubscription, DoctorPushDelivery

MESSAGES = {
    'vaccination_due': ('Child vaccination reminder','A connected child has a vaccination date to review.','/doctor/child-care'),
    'child_record_added': ('Child care updated','A connected child care record was updated.','/doctor/child-care'),
    'patient_connected': ('New family connection', 'A family profile has connected to your practice.', '/doctor/patients'),
    'consultation_requested': ('New consultation request', 'A connected family has requested a consultation.', '/doctor/consultations'),
    'report_shared': ('New shared report', 'A connected family has shared a health document.', '/doctor/reports'),
    'profile_submitted': ('Profile submitted', 'Your doctor profile has been sent for admin review.', '/doctor/dashboard'),
    'profile_approved': ('Doctor profile approved', 'Your clinical workspace is ready. Sign in to continue.', '/doctor/dashboard'),
    'profile_rejected': ('Profile changes requested', 'Sign in to review the requested profile changes.', '/doctor/dashboard'),
}


def notification_token(user, session_id=None):
    return encode_token(user, 'doctor_notifications', 60, password_version=digest(user.password_hash), sid=session_id)


def current_doctor():
    raw = request.headers.get('Authorization', '')
    claims = decode_token(raw[7:] if raw.startswith('Bearer ') else '', 'doctor_notifications')
    user = db().get(User, claims['sub'])
    if (not user or user.role != 'DOCTOR' or not user.email_verified or user.account_status != 'ACTIVE'
            or not hmac.compare_digest(claims.get('password_version', ''), digest(user.password_hash))):
        raise APIError(401, 'invalid_token', 'Sign in again to open notifications')
    if claims.get('sid'):
        session = db().get(UserSession, claims['sid'])
        if not session or session.user_id != user.id or session.revoked_at or session.expires_at <= now():
            raise APIError(401, 'invalid_token', 'Sign in again to open notifications')
    return user


def queue_notification(user_id, kind, event_key):
    if not user_id:
        return
    user = db().get(User, user_id)
    if not user or user.role != 'DOCTOR' or not user.email_verified or user.account_status != 'ACTIVE':
        return
    if db().scalar(select(DoctorNotification.id).where(DoctorNotification.user_id == user_id, DoctorNotification.event_key == event_key)):
        return
    title, body, path = MESSAGES[kind]
    item = DoctorNotification(id=uid(), user_id=user_id, kind=kind, event_key=event_key, title=title, body=body, path=path)
    db().add(item)
    db().flush()
    from services.notifications import enqueue
    general_kind={'profile_approved':'account_approved','profile_rejected':'account_rejected'}.get(kind,'profile_connected' if kind=='patient_connected' and event_key.startswith('profile:') else kind)
    enqueue(user_id,general_kind,title,body,{'path':path},event_key=event_key,mirror=False)
    for subscription in db().scalars(select(DoctorPushSubscription).where(DoctorPushSubscription.user_id == user_id)):
        db().add(DoctorPushDelivery(notification_id=item.id, subscription_id=subscription.id))


def inbox():
    user = current_doctor()
    page, per_page = pagination()
    from services.approvals import paginate
    rows, total = paginate(select(DoctorNotification).where(DoctorNotification.user_id == user.id).order_by(DoctorNotification.created_at.desc(), DoctorNotification.id), page, per_page)
    unread = db().scalar(select(func.count()).select_from(DoctorNotification).where(DoctorNotification.user_id == user.id, DoctorNotification.read_at.is_(None)))
    return jsonify(items=[dict(id=row.id, kind=row.kind, title=row.title, body=row.body, path=row.path,
                               created_at=row.created_at.isoformat()+'Z', read_at=row.read_at.isoformat()+'Z' if row.read_at else None) for row in rows],
                   total=total, unread=unread, page=page, per_page=per_page)


def mark_read(notification_id):
    user = current_doctor()
    item = db().scalar(select(DoctorNotification).where(DoctorNotification.id == str(notification_id), DoctorNotification.user_id == user.id))
    if not item:
        raise APIError(404, 'not_found', 'Notification not found')
    item.read_at = item.read_at or now()
    from core.models import AppNotification
    other=db().scalar(select(AppNotification).where(AppNotification.user_id==user.id,AppNotification.event_key==item.event_key))
    if other:other.read_at=item.read_at
    db().commit()
    return jsonify(message='Notification marked as read')


def push_config():
    current_doctor()
    return jsonify(public_key=current_app.config.get('PUSH_VAPID_PUBLIC_KEY', ''), enabled=push_enabled())


def push_enabled():
    return all(current_app.config.get(key) for key in ('PUSH_VAPID_PUBLIC_KEY', 'PUSH_VAPID_PRIVATE_KEY', 'PUSH_VAPID_SUBJECT'))


def validate_subscription(data):
    endpoint = data.get('endpoint', '')
    if not isinstance(endpoint, str) or len(endpoint) > 2048:
        raise APIError(422, 'invalid_subscription', 'Invalid browser push subscription')
    try:
        parsed = urlsplit(endpoint)
        host = parsed.hostname or ''
        allowed = host in ('fcm.googleapis.com', 'web.push.apple.com', 'updates.push.services.mozilla.com') or host.endswith('.push.services.mozilla.com') or host.endswith('.notify.windows.com')
        if parsed.scheme != 'https' or parsed.port not in (None, 443) or parsed.username or parsed.password or parsed.fragment or not allowed:
            raise ValueError()
        keys = data.get('keys', {})
        for key, length in (('auth', 16), ('p256dh', 65)):
            value = keys[key]
            if not isinstance(value, str) or len(value) > 100 or len(base64.b64decode(value + '=' * (-len(value) % 4), altchars=b'-_', validate=True)) != length:
                raise ValueError()
        from cryptography.hazmat.primitives.asymmetric import ec
        ec.EllipticCurvePublicKey.from_encoded_point(ec.SECP256R1(), base64.urlsafe_b64decode(keys['p256dh'] + '=' * (-len(keys['p256dh']) % 4)))
    except (ValueError, TypeError, KeyError):
        raise APIError(422, 'invalid_subscription', 'Use a valid browser push subscription') from None
    return endpoint, {key: keys[key] for key in ('auth', 'p256dh')}


def subscriptions():
    user = current_doctor()
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        raise APIError(422, 'invalid_subscription', 'Send a browser push subscription')
    if request.method == 'DELETE':
        endpoint = data.get('endpoint')
        if not isinstance(endpoint, str):
            raise APIError(422, 'invalid_subscription', 'Endpoint required')
        item = db().scalar(select(DoctorPushSubscription).where(DoctorPushSubscription.user_id == user.id, DoctorPushSubscription.endpoint_hash == digest(endpoint)))
        if item:
            db().execute(delete(DoctorPushDelivery).where(DoctorPushDelivery.subscription_id == item.id))
            db().delete(item)
            db().commit()
        return jsonify(message='Notifications disabled on this browser')
    if not push_enabled():
        raise APIError(503, 'push_unavailable', 'Browser push is not configured on this server')
    endpoint, keys = validate_subscription(data)
    item = db().scalar(select(DoctorPushSubscription).where(DoctorPushSubscription.endpoint_hash == digest(endpoint)))
    if item and item.user_id != user.id:
        raise APIError(409, 'subscription_in_use', 'Disable notifications for the previous account in this browser first')
    if not item:
        count = db().scalar(select(func.count()).select_from(DoctorPushSubscription).where(DoctorPushSubscription.user_id == user.id))
        if count >= 20:
            raise APIError(409, 'device_limit', 'Notification device limit reached')
        item = DoctorPushSubscription(user_id=user.id, endpoint=endpoint, endpoint_hash=digest(endpoint), keys=keys)
        db().add(item)
    else:
        item.keys = keys
    db().commit()
    return jsonify(message='Notifications enabled on this browser'), 201


def deliver_pending(limit=20):
    if not push_enabled():
        return 0
    from pywebpush import webpush, WebPushException
    delivered = 0
    for _ in range(limit):
        row = db().scalar(select(DoctorPushDelivery).where(DoctorPushDelivery.status == 'PENDING', DoctorPushDelivery.next_attempt_at <= now()).order_by(DoctorPushDelivery.next_attempt_at).with_for_update(skip_locked=True).limit(1))
        if not row:
            break
        item = db().get(DoctorNotification, row.notification_id)
        subscription = db().get(DoctorPushSubscription, row.subscription_id)
        if not item or not subscription:
            row.status = 'CANCELLED'; db().commit(); continue
        user = db().get(User, subscription.user_id)
        if not user or user.account_status != 'ACTIVE' or not user.email_verified:
            row.status = 'CANCELLED'; db().commit(); continue
        row.attempts += 1
        try:
            webpush(subscription_info=dict(endpoint=subscription.endpoint, keys=subscription.keys),
                    data=json.dumps(dict(id=item.id, title=item.title, body=item.body, path=item.path)),
                    vapid_private_key=current_app.config['PUSH_VAPID_PRIVATE_KEY'],
                    vapid_claims={'sub': current_app.config['PUSH_VAPID_SUBJECT']}, ttl=3600, timeout=10)
            row.status = 'SENT'; delivered += 1
        except WebPushException as error:
            status = getattr(error.response, 'status_code', None)
            if status in (404, 410):
                db().execute(delete(DoctorPushDelivery).where(DoctorPushDelivery.subscription_id == subscription.id))
                db().delete(subscription)
            else:
                row.status = 'FAILED' if row.attempts >= 5 else 'PENDING'
                row.next_attempt_at = now() + timedelta(seconds=min(3600, 60 * 2 ** row.attempts))
        except Exception:
            row.status = 'FAILED' if row.attempts >= 5 else 'PENDING'
            row.next_attempt_at = now() + timedelta(minutes=5)
            current_app.logger.warning('Web push delivery deferred; check push configuration')
        db().commit()
    return delivered
