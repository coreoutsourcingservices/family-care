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
def edit_profile(profile_id):
    from flask import g,jsonify
    from core.database import db
    from core.schemas import parse
    from core.care_schemas import CareProfileEdit
    from services.care import accessible_profile,profile_data
    from services.repository import audit
    row=accessible_profile(g.user,str(profile_id),lock=True)
    value=parse(CareProfileEdit)
    row.name=value.full_name;row.guardian_contact=value.guardian_contact
    audit('care_profile_basics_updated',row.owner_id,g.user.id);db().commit()
    return jsonify(profile=profile_data(row))
from core.care_schemas import CareProfileEdit
route(bp,'/profiles/<uuid:profile_id>',edit_profile,'PUT',roles=('PATIENT',),schema=CareProfileEdit)
route(bp, '/profiles/<uuid:profile_id>/connect-doctor', care.connect_profile_doctor, 'POST', roles=('PATIENT',), schema='CareProfileReferral')
def disconnect_profile_doctor(profile_id):
    from flask import g,jsonify
    from core.database import db
    from services.care import accessible_profile,profile_data
    from services.repository import audit
    profile=accessible_profile(g.user,str(profile_id),lock=True)
    previous=profile.referred_doctor_id
    profile.referred_doctor_id=None
    audit('care_profile_doctor_disconnected',previous,g.user.id)
    db().commit()
    return jsonify(profile=profile_data(profile),message='Doctor disconnected from this profile')
route(bp,'/profiles/<uuid:profile_id>/doctor',disconnect_profile_doctor,'DELETE',roles=('PATIENT',))
route(bp, '/profiles/<uuid:profile_id>/reports', care.upload_report, 'POST', roles=('PATIENT',), schema='ReportUpload', limited=True)
route(bp, '/profiles/<uuid:profile_id>/reports', care.reports, roles=('PATIENT',))
route(bp, '/profiles/<uuid:profile_id>/reports/<uuid:report_id>/download', care.download_report, roles=('PATIENT',))

from services import report_text
route(bp, '/report-text/options', report_text.options_endpoint, roles=('PATIENT',))
route(bp, '/profiles/<uuid:profile_id>/reports/<uuid:report_id>/text', report_text.get_text, roles=('PATIENT',))
route(bp, '/profiles/<uuid:profile_id>/reports/<uuid:report_id>/text', report_text.request_text, 'POST', roles=('PATIENT',), limited=True)
