from flask import request, jsonify, g
from sqlalchemy import select
from core.database import db
from core.models import DoctorProfile, User, now
from core.errors import APIError
from services.repository import serialize_user


def pagination():
    try:
        page, per_page = int(request.args.get('page', 1)), int(request.args.get('per_page', 25))
    except ValueError:
        raise APIError(400, 'invalid_pagination', 'page and per_page must be integers') from None
    if page < 1 or not 1 <= per_page <= 100:
        raise APIError(400, 'invalid_pagination', 'page >= 1 and 1 <= per_page <= 100 required')
    return page, per_page


def profile():
    result = serialize_user(g.user)
    if g.user.role == 'DOCTOR':
        doctor = db().get(DoctorProfile, g.user.id)
        result['doctor'] = {key: getattr(doctor, key) for key in ('qualification', 'specialization',
                              'medical_registration_number', 'registering_council', 'nmr_id', 'verification_status',
                              'address', 'clinic_address', 'years_of_experience')}
    return jsonify(user=result)


def locked_current_user():
    return db().scalar(select(User).where(User.id == g.user.id).with_for_update())
