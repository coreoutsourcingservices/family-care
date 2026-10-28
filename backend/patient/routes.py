from flask import Blueprint
from core.routing import route
from patient import controller as c

bp = Blueprint('patient', __name__, url_prefix='/api/v1/patients')
route(bp, '/login', c.login, 'POST', schema='Login', limited=True)
route(bp, '/me', c.me, roles=('PATIENT',))
route(bp, '/register', c.register, 'POST', schema='PatientRegistration', limited=True)
route(bp, '/verify-email', c.verify_email, 'POST', schema='VerifyOTP', limited=True)
route(bp, '/resend-otp', c.resend_otp, 'POST', schema='Challenge', limited=True)
route(bp, '/verify-login-otp', c.verify_login_otp, 'POST', schema='VerifyOTP', limited=True)

route(bp, '/connect-doctor', c.connect_doctor, 'POST', roles=('PATIENT',), schema='ConnectDoctor')
route(bp, '/doctor', c.connected_doctor, roles=('PATIENT',))

from patient import care_controller as care
route(bp, '/profiles', care.create_profile, 'POST', roles=('PATIENT',), schema='CareProfileCreate')
route(bp, '/profiles', care.profiles, roles=('PATIENT',))
route(bp, '/profiles/<uuid:profile_id>', care.profile, roles=('PATIENT',))
route(bp, '/profiles/<uuid:profile_id>/connect-doctor', care.connect_profile_doctor, 'POST', roles=('PATIENT',), schema='CareProfileReferral')
route(bp, '/profiles/<uuid:profile_id>/reports', care.upload_report, 'POST', roles=('PATIENT',), schema='ReportUpload', limited=True)
route(bp, '/profiles/<uuid:profile_id>/reports', care.reports, roles=('PATIENT',))
route(bp, '/profiles/<uuid:profile_id>/reports/<uuid:report_id>/download', care.download_report, roles=('PATIENT',))
