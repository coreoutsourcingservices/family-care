"""Explicit adult per-tab access. Old diary APIs cannot bypass issued tab grants."""
from flask import Blueprint,g,jsonify,request
from sqlalchemy import select,or_
from core.database import db
from core.errors import APIError
from core.models import AdultTabGrant,AdultRecord,CareProfile,now
from core.schemas import parse
from core.routing import route
from services.women_workspace import is_primary,recipients
from services.health_access import GrantInput,event,history

bp=Blueprint('adult_workspace',__name__,url_prefix='/api/v1/adult-access')
TABS=dict(bp='Blood pressure',glucose='Blood sugar',lipids='Cholesterol',medicine='Prescriptions',lifestyle='Growth & nutrition',screening='Preventive care',history='Medical history',reports='Medical reports',consultation_request='Doctor consultation')


def permissions(profile):
    if is_primary(g.user,profile):return {key:'edit' for key in TABS}
    grant=db().scalar(select(AdultTabGrant).where(AdultTabGrant.profile_id==profile.id,AdultTabGrant.recipient_id==g.user.id,AdultTabGrant.revoked_at.is_(None),or_(AdultTabGrant.starts_at.is_(None),AdultTabGrant.starts_at<=now()),or_(AdultTabGrant.expires_at.is_(None),AdultTabGrant.expires_at>now())))
    if not grant or g.user.id not in {u.id for u in recipients(profile)}:raise APIError(403,'adult_access_denied','Permission is missing, not started, expired or revoked')
    return grant.permissions


def profile(profile_id,tab=None,edit=False,manage=False):
    row=db().scalar(select(CareProfile).where(CareProfile.id==str(profile_id),CareProfile.module=='adult',CareProfile.deleted_at.is_(None)).with_for_update())
    if not row:raise APIError(404,'profile_not_found','Adult profile not found')
    if manage and not is_primary(g.user,row):raise APIError(403,'owner_required','Only this profile owner can manage sharing')
    allowed=permissions(row)
    if tab and (tab not in allowed or edit and allowed[tab]!='edit'):raise APIError(403,'adult_tab_denied','You do not have this tab permission')
    return row,allowed


def grant_data(row):
    from core.models import User
    user=db().get(User,row.recipient_id)
    return dict(revoked_at=row.revoked_at.isoformat()+'Z' if row.revoked_at else None,id=row.id,recipient_id=row.recipient_id,name=user.full_name,role=user.role,permissions=row.permissions,
        starts_at=row.starts_at.isoformat()+'Z' if row.starts_at else None,expires_at=row.expires_at.isoformat()+'Z' if row.expires_at else None,
        active=not row.revoked_at and (not row.starts_at or row.starts_at<=now()) and (not row.expires_at or row.expires_at>now()))


def sharing(profile_id):
    row,_=profile(profile_id,manage=True)
    return jsonify(tabs=TABS,recipients=[dict(id=u.id,name=u.full_name,role=u.role) for u in recipients(row)],grants=[grant_data(r) for r in db().scalars(select(AdultTabGrant).where(AdultTabGrant.profile_id==row.id))])


def save_sharing(profile_id):
    row,_=profile(profile_id,manage=True);value=parse(GrantInput)
    if set(value.permissions)-set(TABS):raise APIError(422,'invalid_tabs','Choose valid Adult tabs')
    if str(value.recipient_id) not in {u.id for u in recipients(row)}:raise APIError(422,'invalid_recipient','Choose a current family member or connected approved doctor')
    grant=db().scalar(select(AdultTabGrant).where(AdultTabGrant.profile_id==row.id,AdultTabGrant.recipient_id==str(value.recipient_id)).with_for_update())
    if not grant:grant=AdultTabGrant(profile_id=row.id,recipient_id=str(value.recipient_id));db().add(grant)
    grant.granted_by=g.user.id;grant.permissions=value.permissions;grant.starts_at=value.starts_at;grant.expires_at=value.expires_at;grant.revoked_at=None
    event(row,grant,'granted');db().commit();return jsonify(grant=grant_data(grant))


def revoke(profile_id,grant_id):
    row,_=profile(profile_id,manage=True);grant=db().scalar(select(AdultTabGrant).where(AdultTabGrant.id==str(grant_id),AdultTabGrant.profile_id==row.id))
    if not grant:raise APIError(404,'grant_not_found','Permission not found')
    grant.revoked_at=now();event(row,grant,'revoked');db().commit();return jsonify(message='Access revoked')


def access_history(profile_id):return history(profile(profile_id,manage=True)[0])


def workspace(profile_id):
    row,allowed=profile(profile_id)
    rows=db().scalars(select(AdultRecord).where(AdultRecord.profile_id==row.id,AdultRecord.deleted_at.is_(None),AdultRecord.kind.in_(allowed)))
    return jsonify(profile=dict(id=row.id,name=row.name,dob=row.dob.isoformat()),owner=is_primary(g.user,row),permissions=allowed,records=[dict(r.data,id=r.id,kind=r.kind) for r in rows])


def shared():
    rows=db().scalars(select(CareProfile).join(AdultTabGrant,AdultTabGrant.profile_id==CareProfile.id).where(CareProfile.deleted_at.is_(None),AdultTabGrant.recipient_id==g.user.id))
    items=[]
    for row in rows:
        try:allowed=permissions(row)
        except APIError:continue
        items.append(dict(id=row.id,name=row.name,permissions=allowed))
    return jsonify(items=items)


def report_list(profile_id):
    row,_=profile(profile_id,'reports',request.method=='POST');g.adult_authorized=row.id
    from services.care_uploads import upload_report,report_data
    from core.models import CareReport
    if request.method=='POST':
        response,status=upload_report(g.user,row.id,request.files.get('file'));payload=response.get_json();payload['report'].update(url=None,secure_url=None);return jsonify(payload),status
    return jsonify(items=[dict(report_data(r),url=None,secure_url=None) for r in db().scalars(select(CareReport).where(CareReport.profile_id==row.id))])


def upload(profile_id):return report_list(profile_id)


def download(profile_id,report_id):
    row,_=profile(profile_id,'reports');g.adult_authorized=row.id
    from core.models import CareReport
    from services.report_text import report_bytes
    from flask import send_file
    import io
    report=db().scalar(select(CareReport).where(CareReport.id==str(report_id),CareReport.profile_id==row.id))
    if not report:raise APIError(404,'report_not_found','Report not found')
    response=send_file(io.BytesIO(report_bytes(report)),mimetype=report.content_type,as_attachment=True,download_name=report.name);response.headers['Cache-Control']='no-store';return response


def delete_report(profile_id,report_id):
    row,_=profile(profile_id,'reports',True);g.adult_authorized=row.id
    from services.report_records import delete_report as remove
    return remove(profile_id,report_id)


ROLES=('PATIENT','DOCTOR')
route(bp,'/shared',shared,roles=ROLES)
route(bp,'/profiles/<uuid:profile_id>/workspace',workspace,roles=ROLES)
route(bp,'/profiles/<uuid:profile_id>/sharing',sharing,roles=('PATIENT',))
route(bp,'/profiles/<uuid:profile_id>/sharing',save_sharing,'PUT',roles=('PATIENT',),schema=GrantInput)
route(bp,'/profiles/<uuid:profile_id>/sharing/<uuid:grant_id>',revoke,'DELETE',roles=('PATIENT',))
route(bp,'/profiles/<uuid:profile_id>/history',access_history,roles=('PATIENT',))
route(bp,'/profiles/<uuid:profile_id>/reports',report_list,roles=ROLES)
route(bp,'/profiles/<uuid:profile_id>/reports',upload,'POST',roles=ROLES)
route(bp,'/profiles/<uuid:profile_id>/reports/<uuid:report_id>/download',download,roles=ROLES)
route(bp,'/profiles/<uuid:profile_id>/reports/<uuid:report_id>',delete_report,'DELETE',roles=ROLES)


def save_record(profile_id,record_id=None):
    from patient.adult_routes import AdultInput,save
    value=parse(AdultInput);row,_=profile(profile_id,value.kind,True);g.adult_authorized=row.id
    return save(profile_id,record_id)


def update_record(profile_id,record_id):return save_record(profile_id,record_id)


def remove_record(profile_id,record_id):
    from patient.adult_routes import remove
    row=db().scalar(select(AdultRecord).where(AdultRecord.id==str(record_id),AdultRecord.profile_id==str(profile_id),AdultRecord.deleted_at.is_(None)))
    if not row:raise APIError(404,'record_not_found','Record not found')
    owner,_=profile(profile_id,row.kind,True);g.adult_authorized=owner.id
    return remove(profile_id,record_id)

route(bp,'/profiles/<uuid:profile_id>/records',save_record,'POST',roles=ROLES)
route(bp,'/profiles/<uuid:profile_id>/records/<uuid:record_id>',update_record,'PATCH',roles=ROLES)
route(bp,'/profiles/<uuid:profile_id>/records/<uuid:record_id>',remove_record,'DELETE',roles=ROLES)
