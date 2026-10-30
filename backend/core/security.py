import hashlib
import hmac
import secrets
from datetime import timedelta
from functools import wraps
import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, VerificationError, InvalidHashError
from flask import current_app, request, g
from sqlalchemy import select
from core.database import db
from core.models import User, UserSession, now
from core.errors import APIError

password_hasher = PasswordHasher(time_cost=3, memory_cost=65536, parallelism=2)
_dummy = password_hasher.hash(secrets.token_urlsafe(24))


def digest(value):
    return hashlib.sha256(value.encode()).hexdigest()


def verify_password(encoded, candidate):
    try:
        valid = password_hasher.verify(encoded or _dummy, candidate)
        return valid and encoded is not None
    except (VerifyMismatchError, VerificationError, InvalidHashError):
        return False


def encode_token(user, token_type, minutes, **extra):
    issued = now()
    return jwt.encode(dict(sub=user.id, iss=current_app.config['JWT_ISSUER'],
                           aud=current_app.config['JWT_AUDIENCE'], iat=issued,
                           exp=issued + timedelta(minutes=minutes), jti=secrets.token_hex(16),
                           type=token_type, **extra), current_app.config['JWT_SECRET_KEY'], algorithm='HS256')


def decode_token(token, token_type):
    try:
        claims = jwt.decode(token, current_app.config['JWT_SECRET_KEY'], algorithms=['HS256'],
                            issuer=current_app.config['JWT_ISSUER'], audience=current_app.config['JWT_AUDIENCE'],
                            options={'require': ['sub', 'exp', 'iat', 'jti', 'type', 'iss', 'aud']})
        if claims['type'] != token_type:
            raise ValueError('wrong token purpose')
        return claims
    except (jwt.PyJWTError, ValueError, TypeError):
        raise APIError(401, 'invalid_token', 'Invalid or expired token') from None


def eligible(user):
    if (not user or not user.email_verified or user.approval_status != 'APPROVED'
            or user.account_status != 'ACTIVE' or user.must_change_password):
        raise APIError(403, 'account_restricted', 'Account must be verified, approved, active and password updated')


def transport():
    mode = request.headers.get('X-Auth-Transport', 'bearer').lower()
    if mode not in ('bearer', 'cookie'):
        raise APIError(400, 'invalid_transport', 'X-Auth-Transport must be bearer or cookie')
    return mode


def cookie_request_guard():
    origin = request.headers.get('Origin')
    if origin and origin not in current_app.config['CORS_ORIGINS']:
        raise APIError(403, 'origin_denied', 'Origin is not allowed')
    if request.headers.get('X-Requested-With') != 'FamilyCare':
        raise APIError(403, 'csrf_required', 'Cookie requests require X-Requested-With: FamilyCare')


def check_csrf(session):
    cookie_request_guard()
    token = request.headers.get('X-CSRF-Token', '')
    if not token or not hmac.compare_digest(session.csrf_hash or '', digest(token)):
        raise APIError(403, 'csrf_failed', 'Invalid CSRF token')


def protected(*roles):
    def decorate(fn):
        @wraps(fn)
        def wrapped(*args, **kwargs):
            header = request.headers.get('Authorization', '')
            is_bearer = header.startswith('Bearer ')
            raw = header[7:] if is_bearer else request.cookies.get(cookie_name('access'), request.cookies.get('fc_access', ''))
            claims = decode_token(raw, 'access')
            session = db().get(UserSession, claims.get('sid')) if claims.get('sid') else None
            user = db().get(User, claims['sub'])
            if not session or session.user_id != claims['sub'] or session.revoked_at or session.expires_at <= now():
                raise APIError(401, 'session_revoked', 'Session expired or revoked')
            expected = 'bearer' if is_bearer else 'cookie'
            if session.transport != expected:
                raise APIError(401, 'invalid_transport', 'Session transport mismatch')
            eligible(user)
            portal=request.headers.get('X-FamilyCare-Portal','')
            if not is_bearer and portal in ('patient','doctor') and user.role!=portal.upper():
                raise APIError(401,'portal_session_changed','Please sign in to this portal again')
            if roles and user.role not in roles:
                raise APIError(403, 'forbidden', 'Insufficient permissions')
            if not is_bearer and request.method not in ('GET', 'HEAD', 'OPTIONS'):
                check_csrf(session)
            g.user, g.auth_session = user, session
            return fn(*args, **kwargs)
        return wrapped
    return decorate


def cookie_name(kind):
    # Public patient/doctor portals coexist on the same host and API path.
    portal=request.headers.get('X-FamilyCare-Portal','')
    return 'fc_'+portal+'_'+kind if portal in ('patient','doctor') else 'fc_'+kind
