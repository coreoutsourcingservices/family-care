"""Read-only logs from profiles explicitly connected to the current doctor."""
from flask import g, jsonify
from sqlalchemy import select, union_all, func, literal
from core.database import db
from core.http import pagination
from core.models import ChildRecord, AdultRecord
from services.care import accessible_profile


def records(profile_id):
    profile = accessible_profile(g.user, str(profile_id))
    from datetime import date
    age=date.today().year-profile.dob.year-((date.today().month,date.today().day)<(profile.dob.month,profile.dob.day))
    page, per_page = pagination()
    def shared(model):
        query=select(model.id.label('id'),model.kind.label('kind'),model.data.label('data'),model.created_at.label('created_at'),literal('PARENT_REPORTED' if model is ChildRecord else 'SELF_REPORTED').label('verification_status')).where(model.profile_id==profile.id,model.deleted_at.is_(None))
        if profile.module=='child' and age<=12 and model is ChildRecord:query=query.where(model.kind.in_(['vaccination','growth','nutrition','care','consultation_request']))
        return query
    combined=union_all(shared(ChildRecord),shared(AdultRecord)).subquery()
    total=db().scalar(select(func.count()).select_from(combined))
    rows=db().execute(select(combined).order_by(combined.c.created_at.desc(),combined.c.id).offset((page-1)*per_page).limit(per_page)).mappings().all()
    return jsonify(items=[dict(row['data'],id=row['id'],kind=row['kind'],verification_status=row['verification_status']) for row in rows],total=total,page=page,per_page=per_page)
