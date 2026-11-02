"""Separate, authenticated review queues; registration/OTP behavior stays unchanged."""
from flask import g
from core.errors import APIError
from core.http import pagination
from core.schemas import parse, Rejection
from services.approvals import listing, review


def applicant_role(kind):
    role={'doctors':'DOCTOR','patients':'PATIENT'}.get(kind)
    if not role:
        raise APIError(404,'queue_not_found','Approval queue not found')
    return role


def queue(kind):
    return listing(applicant_role(kind),*pagination(),pending=True)


def approve_applicant(kind,user_id):
    return review(g.user,user_id,applicant_role(kind),True)


def reject_applicant(kind,user_id):
    return review(g.user,user_id,applicant_role(kind),False,parse(Rejection).reason)
