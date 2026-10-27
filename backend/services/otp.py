import hashlib
import hmac
from datetime import timedelta
from flask import current_app
from sqlalchemy import select, update
from core.database import db
from core.errors import APIError
from core.models import OTPChallenge, EmailNotification, now, uid
from core.security import encode_token, decode_token
from services.repository import audit


def otp_code(challenge_id):
    key = current_app.config['OTP_HMAC_SECRET'].encode()
    raw = hmac.new(key, ('code:' + challenge_id).encode(), hashlib.sha256).digest()
    # Rejection sampling avoids modulo bias; challenge UUID is cryptographically random.
    index = 0
    while True:
        number = int.from_bytes(raw[:4], 'big')
        if number < (2**32 // 1000000) * 1000000:
            return f'{number % 1000000:06d}'
        index += 1
        raw = hmac.new(key, raw + str(index).encode(), hashlib.sha256).digest()


def code_hash(challenge_id, value):
    return hmac.new(current_app.config['OTP_HMAC_SECRET'].encode(),
                    f'verify:{challenge_id}:{value}'.encode(), hashlib.sha256).hexdigest()


def issue(user, purpose):
    if purpose == 'login':
        raise APIError(410, 'login_otp_disabled', 'Sign in with email and password')
    # Caller locks User first; all OTP creation for an account is serialized.
    latest = db().scalar(select(OTPChallenge).where(OTPChallenge.user_id == user.id,
                        OTPChallenge.purpose == purpose).order_by(OTPChallenge.created_at.desc()).limit(1))
    if latest and latest.created_at > now() - timedelta(seconds=60):
        raise APIError(429, 'otp_cooldown', 'Wait 60 seconds before requesting another OTP')
    db().execute(update(OTPChallenge).where(OTPChallenge.user_id == user.id,
                 OTPChallenge.purpose == purpose, OTPChallenge.consumed_at.is_(None)).values(consumed_at=now()))
    challenge = OTPChallenge(id=uid(), user_id=user.id, purpose=purpose,
                              expires_at=now() + timedelta(minutes=5))
    challenge.code_hash = code_hash(challenge.id, otp_code(challenge.id))
    db().add(challenge)
    db().flush()
    db().add(EmailNotification(user_id=user.id, challenge_id=challenge.id, template=purpose + '_otp'))
    audit('otp_queued:' + purpose, user.id)
    return payload(user, challenge)


def payload(user, challenge):
    return {'challenge_token': encode_token(user, 'challenge', 10, cid=challenge.id,
                                           purpose=challenge.purpose),
            'expires_in': 300, 'resend_after': 60, 'email_status': 'queued'}


def resolve(token, purpose=None, role=None):
    claims = decode_token(token, 'challenge')
    from core.models import User
    user = db().scalar(select(User).where(User.id == claims['sub']).with_for_update())
    challenge = db().scalar(select(OTPChallenge).where(OTPChallenge.id == claims.get('cid')).with_for_update())
    if (not user or not challenge or challenge.user_id != user.id or challenge.purpose != claims.get('purpose')
            or (purpose and challenge.purpose != purpose) or (role and user.role != role)):
        raise APIError(401, 'invalid_challenge', 'Invalid challenge')
    if user.account_status != 'ACTIVE':
        raise APIError(403, 'account_restricted', 'Account is suspended')
    return user, challenge


def consume(challenge, code):
    if challenge.consumed_at or challenge.expires_at <= now() or challenge.attempts >= 5:
        raise APIError(400, 'otp_unavailable', 'OTP expired, already used or attempts exhausted')
    challenge.attempts += 1
    if not hmac.compare_digest(challenge.code_hash or '', code_hash(challenge.id, code)):
        if challenge.attempts >= 5:
            challenge.consumed_at = now()
        audit('otp_invalid', challenge.user_id)
        db().commit()  # Preserve failed attempt even though the request returns an error.
        raise APIError(400, 'invalid_otp', 'Invalid OTP')
    challenge.consumed_at = now()


def resend(token, role):
    claims = decode_token(token, 'challenge')
    if claims.get('pending_signup'):
        from services.signup import resend_pending
        return resend_pending(claims, role)
    user, challenge = resolve(token, role=role)
    if challenge.purpose not in ('verify_email', 'reset_password'):
        raise APIError(400, 'invalid_purpose', 'This challenge cannot be resent')
    if challenge.consumed_at:
        raise APIError(400, 'otp_unavailable', 'Challenge already used; start a new flow')
    result = issue(user, challenge.purpose)
    db().commit()
    return result
