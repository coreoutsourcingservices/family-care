"""Read-only account/member directory for the administrative portals."""
from flask import jsonify, request
from sqlalchemy import select, func
from core.database import db
from core.errors import APIError
from core.http import pagination
from core.models import CareProfile, CareReport
from services.repository import user_by_id, serialize_user
from services.approvals import paginate
from services.care import profile_data


def counts_for_users(user_ids):
    result = {key:dict(total=0, members=0, self=0, child=0, adult=0, women=0) for key in user_ids}
    if not user_ids:
        return result
    rows = db().execute(select(CareProfile.owner_id, CareProfile.profile_type, CareProfile.module, func.count())
                        .where(CareProfile.owner_id.in_(user_ids))
                        .group_by(CareProfile.owner_id, CareProfile.profile_type, CareProfile.module))
    for owner, profile_type, module, count in rows:
        result[owner]['total'] += count
        result[owner]['members' if profile_type == 'member' else 'self'] += count
        result[owner][module] += count
    return result


def patient(identifier):
    user = user_by_id(identifier)
    if not user or user.role != 'PATIENT':
        raise APIError(404, 'patient_not_found', 'Patient account not found')
    return user


def account_detail(user_id):
    user = patient(user_id)
    return jsonify(user=dict(serialize_user(user), created_at=user.created_at.isoformat()+'Z'),
                   profile_counts=counts_for_users([user.id])[user.id])


def members(user_id):
    user = patient(user_id)
    page, per_page = pagination()
    query = select(CareProfile).where(CareProfile.owner_id == user.id)
    module = request.args.get('module')
    if module:
        if module not in ('child','adult','women'):
            raise APIError(422, 'invalid_module', 'Choose child, adult or women')
        query = query.where(CareProfile.module == module)
    rows, total = paginate(query.order_by(CareProfile.created_at.desc(), CareProfile.id), page, per_page)
    ids = [row.id for row in rows]
    reports = dict(db().execute(select(CareReport.profile_id, func.count()).where(
        CareReport.profile_id.in_(ids)).group_by(CareReport.profile_id)).all()) if ids else {}
    return jsonify(items=[dict(profile_data(row), report_count=reports.get(row.id,0)) for row in rows],
                   total=total, page=page, per_page=per_page)


def member_detail(user_id, profile_id):
    user = patient(user_id)
    profile = db().scalar(select(CareProfile).where(CareProfile.owner_id == user.id, CareProfile.id == str(profile_id)))
    if not profile:
        raise APIError(404, 'profile_not_found', 'This profile does not belong to the selected patient')
    parent = db().get(CareProfile, profile.parent_profile_id) if profile.parent_profile_id else None
    count = db().scalar(select(func.count()).select_from(CareReport).where(CareReport.profile_id == profile.id))
    return jsonify(profile=dict(profile_data(profile), report_count=count,
                               parent_name=parent.name if parent and parent.owner_id == user.id else None),
                   owner={'id':user.id, 'public_id':user.public_id, 'full_name':user.full_name, 'email':user.email})
