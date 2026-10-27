from flask import Blueprint
from core.routing import route
from admin import controller as c

bp = Blueprint('admin', __name__, url_prefix='/api/v1/admin')
route(bp, '/login', c.login, 'POST', schema='Login', limited=True)
route(bp, '/me', c.me, roles=('ADMIN',))
route(bp, '/register', c.register, 'POST', schema='Registration', limited=True)
route(bp, '/verify-email', c.verify_email, 'POST', schema='VerifyOTP', limited=True)
route(bp, '/resend-otp', c.resend_otp, 'POST', schema='Challenge', limited=True)
route(bp, '/verify-login-otp', c.verify_login_otp, 'POST', schema='VerifyOTP', limited=True)
route(bp, '/dashboard', c.dashboard, roles=('ADMIN',))
route(bp, '/doctor-requests', c.requests_pending, roles=('ADMIN',))
route(bp, '/doctors', c.users, roles=('ADMIN',))
route(bp, '/doctors/<user_id>/approve', c.approve, 'POST', roles=('ADMIN',))
route(bp, '/doctors/<user_id>/reject', c.reject, 'POST', roles=('ADMIN',), schema='Rejection')
route(bp, '/doctors/<user_id>/suspend', c.suspend, 'POST', roles=('ADMIN',))
route(bp, '/doctors/<user_id>/reactivate', c.reactivate, 'POST', roles=('ADMIN',))

route(bp, '/patients', c.patients, roles=('ADMIN',))
