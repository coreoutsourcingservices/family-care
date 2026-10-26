from flask import jsonify, g, request
from core.schemas import parse
from core.http import profile, pagination
from doctor import service, schema


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


def approval_status():
    return service.approvals.doctor_status(parse(schema.Credentials))


def resubmit():
    return service.approvals.resubmit_doctor(parse(schema.Resubmission))
