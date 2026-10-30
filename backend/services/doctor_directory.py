"""Administrative doctor detail with paginated connected-profile metadata."""
from flask import jsonify
from sqlalchemy import select
from core.database import db
from core.errors import APIError
from core.http import pagination
from core.models import DoctorProfile,CareProfile
from services.repository import user_by_id,serialize_user
from services.approvals import paginate
from services.doctor_onboarding import profile_details

def detail(user_id):
    user=user_by_id(user_id)
    if not user or user.role!='DOCTOR':raise APIError(404,'doctor_not_found','Doctor not found')
    profile=db().get(DoctorProfile,user.id)
    return jsonify(user={**serialize_user(user),'doctor':profile_details(profile)})

def connected_profiles(user_id):
    user=user_by_id(user_id)
    if not user or user.role!='DOCTOR':raise APIError(404,'doctor_not_found','Doctor not found')
    page,size=pagination()
    rows,total=paginate(select(CareProfile).where(CareProfile.referred_doctor_id==user.id).order_by(CareProfile.created_at,CareProfile.id),page,size)
    return jsonify(items=[dict(id=p.id,full_name=p.name,module=p.module,owner_id=p.owner_id,date_of_birth=p.dob.isoformat()) for p in rows],total=total,page=page,per_page=size)
