from flask import Blueprint
from core.routing import route
from auth import controller as c

bp = Blueprint('auth', __name__, url_prefix='/api/v1/auth')
ROLES = ('SUPERADMIN', 'ADMIN', 'DOCTOR', 'PATIENT')
route(bp, '/refresh', c.refresh, 'POST', schema='RefreshRequest', limited=True)
route(bp, '/logout', c.logout, 'POST', roles=ROLES)
route(bp, '/logout-all', c.logout_all, 'POST', roles=ROLES)
route(bp, '/forgot-password', c.forgot_password, 'POST', schema='ForgotPassword', limited=True)
route(bp, '/reset-password', c.reset_password, 'POST', schema='ResetPassword', limited=True)
route(bp, '/change-password', c.change_password, 'POST', roles=ROLES, schema='ChangePassword')
route(bp, '/initial-password', c.initial_password, 'POST', schema='InitialPassword', limited=True)
route(bp, '/sessions', c.list_sessions, roles=ROLES)
route(bp, '/sessions/<session_id>', c.revoke_session, 'DELETE', roles=ROLES)
route(bp, '/request-email-verification', c.request_verification, 'POST', schema='Login', limited=True)
route(bp, '/resend-otp', c.resend_otp, 'POST', schema='Challenge', limited=True)
