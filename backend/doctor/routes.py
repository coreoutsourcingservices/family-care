from flask import Blueprint
from core.routing import route
from doctor import controller as c

from doctor.onboarding_images import upload as upload_setup_image
from doctor.clinical_records import records as shared_clinical_records

bp = Blueprint('doctor', __name__, url_prefix='/api/v1/doctors')
route(bp, '/login', c.login, 'POST', schema='Login', limited=True)
route(bp, '/me', c.me, roles=('DOCTOR',))
route(bp, '/register', c.register, 'POST', schema='DoctorRegistration', limited=True)
route(bp, '/setup-images', upload_setup_image, 'POST', limited=True)
route(bp, '/setup-profile', c.setup_profile, 'POST', schema='DoctorProfileSetup', limited=True)
route(bp, '/verify-email', c.verify_email, 'POST', schema='VerifyOTP', limited=True)
route(bp, '/resend-otp', c.resend_otp, 'POST', schema='Challenge', limited=True)
route(bp, '/approval-status', c.approval_status, 'POST', schema='Login', limited=True)
route(bp, '/resubmit', c.resubmit, 'POST', schema='Resubmission', limited=True)

route(bp, '/referral', c.referral, roles=('DOCTOR',))
route(bp, '/patients', c.patients, roles=('DOCTOR',))

from patient import care_controller as care
route(bp, '/care-profiles', care.profiles, roles=('DOCTOR',))
route(bp, '/care-profiles/<uuid:profile_id>', care.profile, roles=('DOCTOR',))
route(bp, '/care-profiles/<uuid:profile_id>/records', shared_clinical_records, roles=('DOCTOR',))
route(bp, '/care-profiles/<uuid:profile_id>/reports', care.reports, roles=('DOCTOR',))
route(bp, '/care-profiles/<uuid:profile_id>/reports/<uuid:report_id>/download', care.download_report, roles=('DOCTOR',))

from doctor import notifications as notices
route(bp, '/notifications', notices.inbox)
route(bp, '/notifications/<uuid:notification_id>/read', notices.mark_read, 'POST')
route(bp, '/notifications/push-config', notices.push_config)
route(bp, '/notifications/subscriptions', notices.subscriptions, 'POST', limited=True)
def remove_push_subscription():
    return notices.subscriptions()
route(bp, '/notifications/subscriptions', remove_push_subscription, 'DELETE', limited=True)
