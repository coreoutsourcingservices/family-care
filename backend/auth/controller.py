from flask import request, g, jsonify
from sqlalchemy import select
from core.database import db
from core.models import UserSession, now
from core.schemas import parse, ForgotPassword, ResetPassword, ChangePassword, InitialPassword
from core.security import transport, cookie_name
from core.http import locked_current_user
from core.errors import APIError
from services import authentication, sessions
from services.repository import audit, revoke_sessions
from services import otp
from core.schemas import Login, Challenge


def request_verification():
    return authentication.request_verification(parse(Login))


def resend_otp():
    return jsonify(otp.resend(parse(Challenge).challenge_token, None))


def refresh():
    cookie_mode = transport() == 'cookie'
    if cookie_mode:
        raw = request.cookies.get(cookie_name('refresh'), request.cookies.get('fc_refresh'))
    else:
        data = request.get_json()
        if not isinstance(data, dict) or set(data) != {'refresh_token'}:
            raise APIError(400, 'invalid_json', 'Only refresh_token is required')
        raw = data.get('refresh_token')
    return sessions.refresh_session(raw, cookie_mode)


def logout():
    g.auth_session.revoked_at = now()
    audit('logout', g.user.id, g.user.id)
    db().commit()
    return sessions.clear_cookies(jsonify(message='Logged out'))


def logout_all():
    locked_current_user()
    revoke_sessions(g.user.id)
    audit('logout_all', g.user.id, g.user.id)
    db().commit()
    return sessions.clear_cookies(jsonify(message='All sessions revoked'))


def forgot_password():
    return authentication.forgot_password(parse(ForgotPassword).email)


def reset_password():
    return authentication.reset_password(parse(ResetPassword))


def change_password():
    result = authentication.change_password(locked_current_user(), parse(ChangePassword))
    return sessions.clear_cookies(result)


def initial_password():
    return authentication.initial_password(parse(InitialPassword))


def list_sessions():
    rows = db().scalars(select(UserSession).where(UserSession.user_id == g.user.id,
              UserSession.revoked_at.is_(None), UserSession.expires_at > now()).order_by(UserSession.created_at.desc()).limit(100)).all()
    return jsonify(items=[{'id': r.id, 'created_at': r.created_at.isoformat()+'Z',
                           'expires_at': r.expires_at.isoformat()+'Z', 'current': r.id == g.auth_session.id} for r in rows])


def revoke_session(session_id):
    import uuid
    try:
        uuid.UUID(session_id)
    except ValueError:
        raise APIError(404, 'not_found', 'Session not found') from None
    locked_current_user()
    session = db().scalar(select(UserSession).where(UserSession.id == session_id).with_for_update())
    if not session or session.user_id != g.user.id:
        raise APIError(404, 'not_found', 'Session not found')
    session.revoked_at = now()
    audit('session_revoked', g.user.id, g.user.id)
    db().commit()
    return jsonify(message='Session revoked')
