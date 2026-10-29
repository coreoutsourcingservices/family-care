from flask import g, jsonify
from sqlalchemy import select
from core.database import db
from core.models import PatientProfile, CareProfile, ChildRecord
from services.care import accessible_profile, profile_data
from services.repository import audit
from core.http import pagination
from services.approvals import paginate

def disconnect_profile(profile_id):
    profile=accessible_profile(g.user,str(profile_id),lock=True)
    doctor_id=profile.referred_doctor_id
    profile.referred_doctor_id=None
    if doctor_id: audit('care_profile_doctor_disconnected',doctor_id,g.user.id)
    db().commit()
    return jsonify(profile=profile_data(profile),message='Doctor removed from this profile')

def disconnect_account():
    patient=db().scalar(select(PatientProfile).where(PatientProfile.user_id==g.user.id).with_for_update())
    doctor_id=patient.referred_by_doctor_id if patient else None
    if doctor_id:
        profiles=db().scalars(select(CareProfile).where(CareProfile.owner_id==g.user.id,CareProfile.referred_doctor_id==doctor_id).with_for_update()).all()
        for profile in profiles: profile.referred_doctor_id=None
        patient.referred_by_doctor_id=None
        patient.referred_at=None
        audit('doctor_referral_disconnected',doctor_id,g.user.id)
        db().commit()
    return jsonify(doctor=None,message='Doctor connection removed')

def doctor_records(profile_id):
    profile=accessible_profile(g.user,str(profile_id))
    page,per_page=pagination()
    query=select(ChildRecord).where(ChildRecord.profile_id==profile.id,ChildRecord.deleted_at.is_(None),ChildRecord.kind.in_(('vaccination','growth','nutrition','history','consultation'))).order_by(ChildRecord.created_at.desc(),ChildRecord.id)
    rows,total=paginate(query,page,per_page)
    from patient.child_routes import record_data
    return jsonify(items=[record_data(row) for row in rows],total=total,page=page,per_page=per_page)
