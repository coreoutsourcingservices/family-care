from flask import Blueprint, jsonify
from core.routing import route
from core.errors import APIError
from services import vaccination as service

bp=Blueprint('vaccination',__name__,url_prefix='/api/v1')


def public_version(schedule_id):
    row=service.schedule_row(schedule_id)
    if row.status not in ('PUBLISHED','RETIRED'):raise APIError(404,'schedule_not_found','Published schedule not found')
    return jsonify(schedule=service.schedule_data(row))


route(bp,'/vaccination-schedules/<uuid:schedule_id>',public_version)
route(bp,'/children/<uuid:child_id>/vaccination-context',service.context_endpoint,roles=('PATIENT',))
def save_context(child_id):return service.context_endpoint(child_id)
route(bp,'/children/<uuid:child_id>/vaccination-context',save_context,'PUT',roles=('PATIENT',))
route(bp,'/doctors/vaccination-reviews',service.review_queue,roles=('DOCTOR',))
route(bp,'/doctors/vaccination-reviews/<uuid:schedule_id>',service.medical_review,'POST',roles=('DOCTOR',))
from services import vaccination_starters as starters
route(bp,'/admin/vaccination/import-uip',starters.import_uip,'POST',roles=('ADMIN',))
def superadmin_import_uip():return starters.import_uip()
route(bp,'/superadmin/vaccination/import-uip',superadmin_import_uip,'POST',roles=('SUPERADMIN',))
route(bp,'/doctors/vaccination/import-iap',starters.import_iap,'POST',roles=('DOCTOR',))
route(bp,'/doctors/vaccination/schedules',starters.doctor_schedules,roles=('DOCTOR',))
route(bp,'/doctors/vaccination/schedules/<uuid:schedule_id>',starters.doctor_edit,'PUT',roles=('DOCTOR',))
route(bp,'/doctors/vaccination/schedules/<uuid:schedule_id>/submit-review',starters.doctor_submit,'POST',roles=('DOCTOR',))
def doctor_reviewers():return service.reviewers()
route(bp,'/doctors/vaccination/reviewers',doctor_reviewers,roles=('DOCTOR',))


# Each administrative portal retains its own role boundary and cookie namespace.
for prefix,role in (('admin','ADMIN'),('superadmin','SUPERADMIN')):
    def register(path,handler,method='GET'):
        def view(**kwargs):return handler(**kwargs)
        view.__name__=prefix+'_'+path.replace('/','_').replace('<uuid:','').replace('>','').replace('-','_')+'_'+method
        route(bp,'/'+prefix+'/vaccination/'+path,view,method,roles=(role,))
    register('vaccines',service.vaccines_admin)
    register('vaccines',service.vaccines_admin,'POST')
    register('vaccines/<uuid:vaccine_id>',service.edit_vaccine,'PUT')
    register('schedules',service.schedules_admin)
    register('schedules',service.schedules_admin,'POST')
    register('schedules/<uuid:schedule_id>',service.edit_schedule,'PUT')
    def eligibility(schedule_id):return service.edit_section(schedule_id,'eligibility')
    def reminders(schedule_id):return service.edit_section(schedule_id,'reminders')
    register('schedules/<uuid:schedule_id>/eligibility',eligibility,'PUT')
    register('schedules/<uuid:schedule_id>/reminders',reminders,'PUT')
    register('reviewers',service.reviewers)
    register('schedules/<uuid:schedule_id>/submit-review',service.submit_review,'POST')
    register('schedules/<uuid:schedule_id>/withdraw',service.withdraw,'POST')
    register('schedules/<uuid:schedule_id>/publish',service.publish,'POST')
    register('schedules/<uuid:schedule_id>/retire',service.retire,'POST')
    register('audit',service.audits)

from services.child_vaccination_plan import plan as child_plan
route(bp,'/doctors/care-profiles/<uuid:profile_id>/vaccination-plan',child_plan,roles=('DOCTOR',))
def save_child_plan(profile_id):return child_plan(profile_id)
route(bp,'/doctors/care-profiles/<uuid:profile_id>/vaccination-plan',save_child_plan,'POST',roles=('DOCTOR',))
