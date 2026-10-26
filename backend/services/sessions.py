import secrets
import hmac
from datetime import timedelta
from flask import current_app, request, jsonify
from sqlalchemy import select
from core.database import db
from core.models import UserSession, RefreshToken, User, now, uid
from core.security import digest, encode_token, eligible, transport, check_csrf, cookie_request_guard
from core.errors import APIError
from services.repository import serialize_user, audit


def issue_session(user):
    eligible(user)
    mode = transport()
    if mode == 'cookie':
        cookie_request_guard()
    session = UserSession(id=uid(), user_id=user.id, transport=mode,
                           expires_at=now() + timedelta(days=current_app.config['REFRESH_TOKEN_DAYS']))
    db().add(session)
    db().flush()
    user.last_login_at = now()
    audit('login_success', user.id, user.id)
    result = rotate(user, session)
    db().commit()
    return respond(result, session)


def rotate(user, session):
    refresh = secrets.token_urlsafe(48)
    db().add(RefreshToken(session_id=session.id, token_hash=digest(refresh), expires_at=session.expires_at))
    csrf = secrets.token_urlsafe(32) if session.transport == 'cookie' else None
    session.csrf_hash = digest(csrf) if csrf else None
    ttl = current_app.config['ACCESS_TOKEN_MINUTES'] * 60
    return dict(access_token=encode_token(user, 'access', ttl / 60, sid=session.id, role=user.role),
                refresh_token=refresh, token_type='Bearer', expires_in=ttl,
                csrf_token=csrf, user=serialize_user(user))


def respond(result, session):
    if session.transport == 'bearer':
        result.pop('csrf_token', None)
        return jsonify(result)
    access, refresh = result.pop('access_token'), result.pop('refresh_token')
    response = jsonify(result)
    options = dict(secure=current_app.config['COOKIE_SECURE'], httponly=True, samesite='Lax')
    response.set_cookie('fc_access', access, max_age=result['expires_in'], path='/api/v1', **options)
    response.set_cookie('fc_refresh', refresh, max_age=max(0, int((session.expires_at-now()).total_seconds())),
                        path='/api/v1/auth', **options)
    return response


def refresh_session(raw, cookie_mode):
    if not raw or not isinstance(raw, str) or len(raw) > 512:
        raise APIError(401, 'invalid_refresh', 'Refresh token required')
    # Initial lookup is read-only; acquire user -> session -> token locks consistently.
    item = db().scalar(select(RefreshToken).where(RefreshToken.token_hash == digest(raw)))
    if not item:
        raise APIError(401, 'invalid_refresh', 'Invalid refresh token')
    preliminary = db().get(UserSession, item.session_id)
    user = db().scalar(select(User).where(User.id == preliminary.user_id).with_for_update())
    session = db().scalar(select(UserSession).where(UserSession.id == item.session_id)
                          .with_for_update().execution_options(populate_existing=True))
    item = db().scalar(select(RefreshToken).where(RefreshToken.id == item.id)
                       .with_for_update().execution_options(populate_existing=True))
    if session.transport != ('cookie' if cookie_mode else 'bearer'):
        raise APIError(401, 'invalid_transport', 'Refresh transport mismatch')
    if cookie_mode:
        check_csrf(session)
    if item.consumed_at:
        session.revoked_at = now()
        audit('refresh_reuse_detected', user.id, user.id)
        db().commit()
        raise APIError(401, 'refresh_reused', 'Refresh token reused; session revoked')
    if session.revoked_at or session.expires_at <= now() or item.expires_at <= now():
        raise APIError(401, 'session_expired', 'Session expired or revoked')
    eligible(user)
    item.consumed_at = now()
    result = rotate(user, session)
    db().commit()
    return respond(result, session)


def clear_cookies(response):
    response.delete_cookie('fc_access', path='/api/v1')
    response.delete_cookie('fc_refresh', path='/api/v1/auth')
    return response
