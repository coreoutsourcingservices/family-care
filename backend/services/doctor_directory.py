"""Administrative doctor detail with paginated connected-profile metadata."""
from flask import jsonify, request
from sqlalchemy import select,func
from core.database import db
from core.errors import APIError
from core.http import pagination
from core.models import DoctorProfile,CareProfile,User
from services.repository import user_by_id,serialize_user
from services.approvals import paginate
from services.doctor_onboarding import profile_details

def detail(user_id):
    user=user_by_id(user_id)
    if not user or user.role!='DOCTOR':raise APIError(404,'doctor_not_found','Doctor not found')
    profile=db().get(DoctorProfile,user.id)
    filters=(CareProfile.referred_doctor_id==user.id,CareProfile.deleted_at.is_(None))
    counts=dict(db().execute(select(CareProfile.module,func.count()).where(*filters).group_by(CareProfile.module)).all())
    families=db().scalar(select(func.count(func.distinct(CareProfile.owner_id))).where(*filters))
    return jsonify(user={**serialize_user(user),'doctor':{**profile_details(profile),
        'verification_status':profile.verification_status if profile else None,
        'verification_check':profile.verification_check if profile else None}},
        dashboard=dict(connected_profiles=sum(counts.values()),families=families,child=counts.get('child',0),adult=counts.get('adult',0),women=counts.get('women',0)))

def connected_profiles(user_id):
    user=user_by_id(user_id)
    if not user or user.role!='DOCTOR':raise APIError(404,'doctor_not_found','Doctor not found')
    page,size=pagination()
    query=select(CareProfile).where(CareProfile.referred_doctor_id==user.id,CareProfile.deleted_at.is_(None))
    module=request.args.get('module')
    if module:
        if module not in ('child','adult','women'):raise APIError(422,'invalid_module','Choose child, adult or women')
        query=query.where(CareProfile.module==module)
    search=request.args.get('search','').strip()[:120]
    if search:query=query.where(CareProfile.name.icontains(search,autoescape=True))
    rows,total=paginate(query.order_by(CareProfile.created_at,CareProfile.id),page,size)
    owners={u.id:u for u in db().scalars(select(User).where(User.id.in_({p.owner_id for p in rows}))).all()} if rows else {}
    return jsonify(items=[network_profile(p,owners.get(p.owner_id)) for p in rows],total=total,page=page,per_page=size)


def network_profile(profile,owner):
    # Directory metadata only: a referral connection does not imply clinical sharing consent.
    return dict(id=profile.id,full_name=profile.name,module=profile.module,owner_id=profile.owner_id,
        date_of_birth=profile.dob.isoformat(),gender=profile.gender,profile_type=profile.profile_type,
        updated_at=profile.updated_at.isoformat()+'Z',family_name=owner.full_name if owner else 'Family account',
        family_public_id=owner.public_id if owner else None)


def connected_families(user_id):
    user=user_by_id(user_id)
    if not user or user.role!='DOCTOR':raise APIError(404,'doctor_not_found','Doctor not found')
    page,size=pagination()
    counts=select(CareProfile.owner_id.label('owner_id'),func.count().label('total'),
        func.max(CareProfile.updated_at).label('updated_at')).where(
        CareProfile.referred_doctor_id==user.id,CareProfile.deleted_at.is_(None)).group_by(CareProfile.owner_id).subquery()
    query=select(User,counts.c.total,counts.c.updated_at).join(counts,User.id==counts.c.owner_id)
    search=request.args.get('search','').strip()[:120]
    if search:query=query.where(User.full_name.icontains(search,autoescape=True))
    total=db().scalar(select(func.count()).select_from(query.subquery()))
    rows=db().execute(query.order_by(User.full_name,User.id).offset((page-1)*size).limit(size)).all()
    return jsonify(items=[dict(id=u.id,full_name=u.full_name,public_id=u.public_id,connected_profiles=count,
        updated_at=updated.isoformat()+'Z') for u,count,updated in rows],total=total,page=page,per_page=size)


def connected_family(user_id,family_id):
    return family_response(user_id,family_id)


def connected_member(user_id,family_id,profile_id):
    return family_response(user_id,family_id,profile_id)


def family_response(user_id,family_id,profile_id=None):
    user=user_by_id(user_id)
    if not user or user.role!='DOCTOR':raise APIError(404,'doctor_not_found','Doctor not found')
    owner=user_by_id(family_id)
    if not owner or owner.role!='PATIENT':raise APIError(404,'connection_not_found','No matching connection to this doctor')
    if profile_id:
        from uuid import UUID
        try:profile_id=str(UUID(profile_id))
        except ValueError:raise APIError(404,'connection_not_found','No matching connection to this doctor') from None
    query=select(CareProfile).where(CareProfile.owner_id==owner.id,CareProfile.referred_doctor_id==user.id,
        CareProfile.deleted_at.is_(None))
    if profile_id:query=query.where(CareProfile.id==profile_id)
    page,size=pagination()
    rows,total=paginate(query.order_by(CareProfile.created_at,CareProfile.id),page,size)
    if not owner or not total:raise APIError(404,'connection_not_found','No matching connection to this doctor')
    return jsonify(family=dict(id=owner.id,full_name=owner.full_name,public_id=owner.public_id),
        items=[network_profile(p,owner) for p in rows],total=total,page=page,per_page=size)
