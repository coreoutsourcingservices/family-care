from flask import jsonify, g, request
from core.schemas import parse
from core.http import profile, pagination
from superadmin import service, schema


def login():
    return service.login(parse(schema.Credentials))


def me():
    return profile()


def dashboard():
    return service.approvals.dashboard()


def requests_pending():
    return service.approvals.listing('ADMIN', *pagination(), pending=True)


def users():
    return service.approvals.listing('ADMIN', *pagination(), status=request.args.get('status'))


def approve(user_id):
    return service.approvals.review(g.user, user_id, 'ADMIN', True)


def reject(user_id):
    return service.approvals.review(g.user, user_id, 'ADMIN', False, parse(schema.Rejection).reason)


def suspend(user_id):
    return service.approvals.account_status(g.user, user_id, 'ADMIN', False)


def reactivate(user_id):
    return service.approvals.account_status(g.user, user_id, 'ADMIN', True)


def doctors():
    return service.approvals.listing('DOCTOR', *pagination())


def patients():
    return service.approvals.listing('PATIENT', *pagination())


def audit_logs():
    return service.approvals.audit_logs(*pagination())
