from services import authentication, otp, approvals
from patient.model import ROLE


def register(data):
    return authentication.register(data, ROLE)


def login(data):
    return authentication.login(data, ROLE)


def verify_email(data):
    return authentication.verify_email(data, ROLE)


def verify_login(data):
    return authentication.verify_login(data, ROLE)


def resend(token):
    return otp.resend(token, ROLE)
