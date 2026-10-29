from flask import jsonify, g, request
from core.schemas import parse
from core.http import profile, pagination
from admin import service, schema


def login():
    return service.login(parse(schema.Credentials))


def me():
    return profile()


def register():
    return service.register(parse(schema.Register))


def verify_email():
    return service.verify_email(parse(schema.VerifyOTP))


def resend_otp():
    return jsonify(service.resend(parse(schema.Challenge).challenge_token))


def verify_login_otp():
    return service.verify_login(parse(schema.VerifyOTP))


def dashboard():
    return service.approvals.dashboard()


def requests_pending():
    return service.approvals.listing('DOCTOR', *pagination(), pending=True)


def users():
    return service.approvals.listing('DOCTOR', *pagination(), status=request.args.get('status'))


def approve(user_id):
    return service.approvals.review(g.user, user_id, 'DOCTOR', True)


def check_doctor(user_id):
    from services.doctor_verification import check_doctor as check
    return check(g.user, user_id)


def reject(user_id):
    return service.approvals.review(g.user, user_id, 'DOCTOR', False, parse(schema.Rejection).reason)


def suspend(user_id):
    return service.approvals.account_status(g.user, user_id, 'DOCTOR', False)


def reactivate(user_id):
    return service.approvals.account_status(g.user, user_id, 'DOCTOR', True)


def patients():
    return service.approvals.listing('PATIENT', *pagination(), status=request.args.get('status'))
