from flask import Blueprint
from core.routing import route
from superadmin import controller as c

bp = Blueprint('superadmin', __name__, url_prefix='/api/v1/superadmin')
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
route(bp, '/audit-logs', c.audit_logs, roles=('SUPERADMIN',))
