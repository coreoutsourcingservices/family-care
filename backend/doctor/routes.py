from flask import Blueprint
from core.routing import route
from doctor import controller as c

bp = Blueprint('doctor', __name__, url_prefix='/api/v1/doctors')
route(bp, '/login', c.login, 'POST', schema='Login', limited=True)
route(bp, '/me', c.me, roles=('DOCTOR',))
route(bp, '/register', c.register, 'POST', schema='DoctorRegistration', limited=True)
route(bp, '/verify-email', c.verify_email, 'POST', schema='VerifyOTP', limited=True)
route(bp, '/resend-otp', c.resend_otp, 'POST', schema='Challenge', limited=True)
route(bp, '/approval-status', c.approval_status, 'POST', schema='Login', limited=True)
route(bp, '/resubmit', c.resubmit, 'POST', schema='Resubmission', limited=True)
