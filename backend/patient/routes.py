from flask import Blueprint
from core.routing import route
from patient import controller as c

bp = Blueprint('patient', __name__, url_prefix='/api/v1/patients')
route(bp, '/login', c.login, 'POST', schema='Login', limited=True)
route(bp, '/me', c.me, roles=('PATIENT',))
route(bp, '/register', c.register, 'POST', schema='Registration', limited=True)
route(bp, '/verify-email', c.verify_email, 'POST', schema='VerifyOTP', limited=True)
route(bp, '/resend-otp', c.resend_otp, 'POST', schema='Challenge', limited=True)
route(bp, '/verify-login-otp', c.verify_login_otp, 'POST', schema='VerifyOTP', limited=True)
