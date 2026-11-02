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
def family_access(profile_id):
    from flask import g, jsonify, request
    from sqlalchemy import select
    from core.database import db
    from core.models import FamilyInvitation
    from core.errors import APIError
    from services.repository import audit
    row=db().scalar(select(FamilyInvitation).where(FamilyInvitation.profile_id==str(profile_id),FamilyInvitation.member_id==g.user.id,FamilyInvitation.accepted_at.is_not(None),FamilyInvitation.revoked_at.is_(None)).with_for_update())
    if not row: raise APIError(403,'member_only','Only the invited member can manage family access')
    enabled=bool((row.pending or {}).get('family_access'))
    if request.method=='PUT':
        data=request.get_json(silent=True)
        if not isinstance(data,dict) or set(data)!={'enabled'} or not isinstance(data['enabled'],bool):raise APIError(422,'invalid_permission','Send enabled as a boolean')
        enabled=data['enabled'];row.pending={**(row.pending or {}),'family_access':enabled}
        audit('member_family_access_updated',row.owner_id,g.user.id);db().commit()
    return jsonify(enabled=enabled)
route(bp,'/profiles/<uuid:profile_id>/family-access',family_access,roles=('PATIENT',))
def update_family_access(profile_id):return family_access(profile_id)
route(bp,'/profiles/<uuid:profile_id>/family-access',update_family_access,'PUT',roles=('PATIENT',))
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
    if profile.module=='women' and previous:
        from core.models import WomenAccessGrant,now
        from sqlalchemy import select
        for grant in db().scalars(select(WomenAccessGrant).where(WomenAccessGrant.profile_id==profile.id,WomenAccessGrant.recipient_id==previous)):
            grant.revoked_at=now()
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
route(bp, '/profiles/<uuid:profile_id>/reports/<uuid:report_id>/text', report_text.request_text, 'POST', roles=('PATIENT',), schema=report_text.Options, limited=True)

route(bp, '/profiles/<uuid:profile_id>', care.update_profile, 'PATCH', roles=('PATIENT',), schema='CareProfileUpdate')
route(bp, '/profiles/<uuid:profile_id>', care.delete_profile, 'DELETE', roles=('PATIENT',))

from services import report_records
route(bp,'/profiles/<uuid:profile_id>/imported-records',report_records.imported,roles=('PATIENT',))
route(bp,'/profiles/<uuid:profile_id>/reports/<uuid:report_id>/import',report_records.import_record,'POST',roles=('PATIENT',),schema=report_records.ImportInput)

route(bp,'/profiles/<uuid:profile_id>/reports/<uuid:report_id>/category',report_records.set_category,'PATCH',roles=('PATIENT',))
route(bp,'/profiles/<uuid:profile_id>/reports/<uuid:report_id>',report_records.delete_report,'DELETE',roles=('PATIENT',))
route(bp,'/profiles/<uuid:profile_id>/doctor-overview',care.doctor_overview,roles=('PATIENT',))

from services import profile_doctor_access
route(bp,'/profiles/<uuid:profile_id>/doctor-access',profile_doctor_access.get_grant,roles=('PATIENT',))
route(bp,'/profiles/<uuid:profile_id>/doctor-access',profile_doctor_access.put_grant,'PUT',roles=('PATIENT',),schema=profile_doctor_access.GrantInput)
route(bp,'/profiles/<uuid:profile_id>/doctor-access',profile_doctor_access.revoke_grant,'DELETE',roles=('PATIENT',))
