from flask import Blueprint
from core.routing import route
from superadmin import controller as c

bp = Blueprint('superadmin', __name__, url_prefix='/api/v1/superadmin')
from services import doctor_directory
route(bp,'/doctors/<user_id>',doctor_directory.detail,roles=('SUPERADMIN',))
route(bp,'/doctors/<user_id>/profiles',doctor_directory.connected_profiles,roles=('SUPERADMIN',))
route(bp, '/login', c.login, 'POST', schema='SuperLogin', limited=True)
route(bp, '/me', c.me, roles=('SUPERADMIN',))
route(bp, '/dashboard', c.dashboard, roles=('SUPERADMIN',))
route(bp, '/admin-requests', c.requests_pending, roles=('SUPERADMIN',))
route(bp, '/admins', c.users, roles=('SUPERADMIN',))
route(bp, '/admins/<user_id>/approve', c.approve, 'POST', roles=('SUPERADMIN',))
route(bp, '/admins/<user_id>/reject', c.reject, 'POST', roles=('SUPERADMIN',), schema='Rejection')
route(bp, '/admins/<user_id>/suspend', c.suspend, 'POST', roles=('SUPERADMIN',))
route(bp, '/admins/<user_id>/reactivate', c.reactivate, 'POST', roles=('SUPERADMIN',))
route(bp, '/doctors', c.doctors, roles=('SUPERADMIN',))
route(bp, '/patients', c.patients, roles=('SUPERADMIN',))
from services import patient_directory
route(bp, '/patients/<user_id>', patient_directory.account_detail, roles=('SUPERADMIN',))
route(bp, '/patients/<user_id>/profiles', patient_directory.members, roles=('SUPERADMIN',))
route(bp, '/patients/<user_id>/profiles/<uuid:profile_id>', patient_directory.member_detail, roles=('SUPERADMIN',))
route(bp, '/audit-logs', c.audit_logs, roles=('SUPERADMIN',))
