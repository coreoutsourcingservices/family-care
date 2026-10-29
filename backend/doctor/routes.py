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

route(bp, '/referral', c.referral, roles=('DOCTOR',))
route(bp, '/patients', c.patients, roles=('DOCTOR',))

from patient import care_controller as care
route(bp, '/care-profiles', care.profiles, roles=('DOCTOR',))
route(bp, '/care-profiles/<uuid:profile_id>', care.profile, roles=('DOCTOR',))
route(bp, '/care-profiles/<uuid:profile_id>/reports', care.reports, roles=('DOCTOR',))
route(bp, '/care-profiles/<uuid:profile_id>/reports/<uuid:report_id>/download', care.download_report, roles=('DOCTOR',))

from doctor.practice import get_practice_profile, save_practice_profile
from services.connections import doctor_records
route(bp, '/practice-profile', get_practice_profile, roles=('DOCTOR',))
route(bp, '/practice-profile', save_practice_profile, 'PUT', roles=('DOCTOR',))
route(bp, '/care-profiles/<uuid:profile_id>/records', doctor_records, roles=('DOCTOR',))
