"""Short-lived signup cache. No signup records are written to PostgreSQL before verification."""
import json
import hmac
import time
import threading
from contextlib import contextmanager
from types import SimpleNamespace
from flask import current_app, jsonify, render_template
from sqlalchemy import select, or_
from core.database import db
from core.models import DoctorProfile, uid
from core.errors import APIError
from core.security import password_hasher, verify_password, encode_token
from services.repository import find_user
from services.otp import otp_code, code_hash
from services.email import send_mail


class PendingStore:
    def __init__(self, uri):
        self.items = {}
        self.mutex = threading.RLock()
        self.redis = None
        if uri.startswith(('redis://', 'rediss://')):
            from redis import Redis
            self.redis = Redis.from_url(uri, decode_responses=True)

    @contextmanager
    def locked(self):
        # A shared cache/lock is required when running multiple API processes.
        lock = self.redis.lock('familycare:signup:lock', timeout=120, blocking_timeout=20) if self.redis else self.mutex
        with lock:
            yield self

    def all(self):
        if self.redis:
            return [json.loads(value) for key in self.redis.scan_iter('familycare:signup:item:*')
                    if (value := self.redis.get(key))]
        self.items = {k: v for k, v in self.items.items() if v['retain_until'] > time.time()}
        return list(self.items.values())

    def put(self, item):
        if self.redis:
            self.redis.set('familycare:signup:item:' + item['id'], json.dumps(item), ex=600)
        else:
            self.items[item['id']] = item

    def delete(self, item):
        if self.redis:
            self.redis.delete('familycare:signup:item:' + item['id'])
        else:
            self.items.pop(item['id'], None)


def store():
    return current_app.extensions['pending_signups']


def response(item):
    token = encode_token(SimpleNamespace(id=item['id']), 'challenge', 10,
                         cid=item['cid'], purpose='verify_email', pending_signup=True)
    return dict(challenge_token=token, expires_in=300, resend_after=60, email_status='sent',
                message='OTP sent to your email. Verify OTP to complete registration.')


def deliver(item):
    body = render_template('emails/verify_email_otp.txt',
                           full_name=item['values']['full_name'], otp=otp_code(item['cid']))
    try:
        send_mail(item['values']['email'], 'Family Care - verify email OTP', body, item['cid'])
    except Exception as error:
        # Log the category/code only; credentials, recipient and OTP stay private.
        current_app.logger.warning('Signup SMTP delivery failed: %s code=%s',
                                   type(error).__name__, getattr(error, 'smtp_code', ''))
        raise APIError(503, 'email_delivery_failed', 'OTP email could not be sent. Please try again later.') from None


def issue(item):
    timestamp = time.time()
    if item.get('sent_at', 0) > timestamp - 60:
        raise APIError(429, 'otp_cooldown', 'Wait 60 seconds before requesting another OTP')
    updated = dict(item, cid=uid(), attempts=0, sent_at=timestamp,
                   expires_at=timestamp + 300, retain_until=timestamp + 600)
    updated['code_hash'] = code_hash(updated['cid'], otp_code(updated['cid']))
    deliver(updated)
    store().put(updated)
    return response(updated)


def register_pending(data, role):
    values = data.model_dump(exclude={'password', 'confirm_password'})
    values['email'] = str(data.email).lower()
    if find_user(values['email']):
        raise APIError(409, 'account_exists', 'Account already exists; use login or reset password')
    if role == 'PATIENT' and values.get('referral_id'):
        from services.referrals import resolve_referral
        resolve_referral(values['referral_id'])
    if role == 'DOCTOR':
        duplicate = db().scalar(select(DoctorProfile).where(or_(
            (DoctorProfile.registering_council == data.registering_council) &
            (DoctorProfile.medical_registration_number == data.medical_registration_number),
            DoctorProfile.nmr_id == data.nmr_id if data.nmr_id else False)))
        if duplicate:
            raise APIError(409, 'conflict', 'Doctor registration already exists')
    # Close the read-only transaction before SMTP; no pending data is persisted.
    db().rollback()
    values['password_hash'] = password_hasher.hash(data.password)
    with store().locked():
        items = store().all()
        existing = next((x for x in items if x['values']['email'] == values['email']), None)
        if len(items) >= 10000 and not existing:
            raise APIError(503, 'signup_busy', 'Please try again later')
        item = dict(id=existing['id'] if existing else uid(), role=role, values=values,
                    sent_at=existing['sent_at'] if existing else 0)
        result = issue(item)
    return jsonify(public_id=None, user_id=None, approval_status='PENDING_EMAIL_VERIFICATION', **result), 202


def lookup(claims, role):
    item = next((x for x in store().all() if x['id'] == claims['sub']), None)
    if not item or item['cid'] != claims.get('cid'):
        raise APIError(400, 'otp_unavailable', 'OTP expired or already used; register again')
    if claims.get('purpose') != 'verify_email' or (role and item['role'] != role):
        raise APIError(401, 'invalid_challenge', 'Invalid challenge')
    return item


def verify_pending(data, role, claims):
    with store().locked():
        item = lookup(claims, role)
        if item['expires_at'] <= time.time() or item['attempts'] >= 5:
            raise APIError(400, 'otp_unavailable', 'OTP expired or attempts exhausted')
        if not hmac.compare_digest(item['code_hash'], code_hash(item['cid'], data.otp)):
            item['attempts'] += 1
            store().put(item)
            raise APIError(400, 'invalid_otp', 'Invalid OTP')
        from services.authentication import create_verified_user
        result = create_verified_user(item['values'], role)
        store().delete(item)
        return result


def resend_pending(claims, role):
    with store().locked():
        return issue(lookup(claims, role))


def restart_pending(data):
    with store().locked():
        item = next((x for x in store().all() if x['values']['email'] == str(data.email).lower()), None)
        if not item:
            return None
        if not verify_password(item['values']['password_hash'], data.password):
            raise APIError(401, 'invalid_credentials', 'Invalid credentials')
        return jsonify(**issue(item)), 202
