"""Aggregate organization dashboard; never exposes child medical record contents."""
from datetime import datetime,timezone
from zoneinfo import ZoneInfo
from sqlalchemy import select,func,or_,extract,text
from core.database import db
from core.models import User,CareProfile,ApprovalRequest,AuditLog,ChildRecord,ChildGrowthNutritionSetting


def visible_users():
    return (User.role.in_(['ADMIN','PATIENT','DOCTOR']),or_(User.role!='DOCTOR',User.id.in_(select(ApprovalRequest.applicant_id))))


def person(user):
    return dict(id=user.id,public_id=user.public_id,full_name=user.full_name,email=user.email,
        role=user.role,approval_status=user.approval_status,account_status=user.account_status,
        created_at=user.created_at.isoformat()+'Z')


def summary(admin=False):
    from patient.child_routes import today
    from services.vaccination import age_date
    current=today();month=current.year*12+current.month-1
    first_year,first_month=divmod(month-11,12)
    def month_start(year,month):return datetime(year,month,1,tzinfo=ZoneInfo('Asia/Kolkata')).astimezone(timezone.utc).replace(tzinfo=None)
    start=month_start(first_year,first_month+1)
    current_start=month_start(current.year,current.month)
    filters=visible_users()+((User.role.in_(['DOCTOR','PATIENT']),) if admin else ())
    totals=dict(db().execute(select(User.role,func.count()).where(*filters).group_by(User.role)).all())
    added=dict(db().execute(select(User.role,func.count()).where(*filters,User.created_at>=current_start).group_by(User.role)).all())
    calendar_date=func.datetime(User.created_at,'+330 minutes') if db().bind.dialect.name=='sqlite' else User.created_at+text("INTERVAL '5 hours 30 minutes'")
    years=extract('year',calendar_date);months=extract('month',calendar_date)
    grouped=db().execute(select(User.role,years,months,func.count()).where(*filters,User.created_at>=start).group_by(User.role,years,months)).all()
    per_month={(role,int(y)*12+int(m)-1):count for role,y,m,count in grouped}
    baseline=dict(db().execute(select(User.role,func.count()).where(*filters,User.created_at<start).group_by(User.role)).all())
    running={role:baseline.get(role,0) for role in ('PATIENT','DOCTOR','ADMIN')};growth=[]
    for index in range(month-11,month+1):
        year,m=divmod(index,12)
        for role in running:running[role]+=per_month.get((role,index),0)
        growth.append(dict(month=f'{year}-{m+1:02}',patients=running['PATIENT'],doctors=running['DOCTOR'],administrators=running['ADMIN']))
    child_filters=(CareProfile.module=='child',CareProfile.deleted_at.is_(None),CareProfile.dob>age_date(current,-13,'years'),CareProfile.dob<=current)
    children=db().scalar(select(func.count()).select_from(CareProfile).where(*child_filters))
    new_children=db().scalar(select(func.count()).select_from(CareProfile).where(*child_filters,CareProfile.created_at>=current_start))
    inactive=db().scalar(select(func.count()).select_from(CareProfile).join(ChildGrowthNutritionSetting,ChildGrowthNutritionSetting.profile_id==CareProfile.id).where(*child_filters,ChildGrowthNutritionSetting.active.is_(False)))
    record_counts=dict(db().execute(select(ChildRecord.kind,func.count()).join(CareProfile,CareProfile.id==ChildRecord.profile_id)
        .where(*child_filters,ChildRecord.deleted_at.is_(None),ChildRecord.kind.in_(['growth','nutrition','vaccination'])).group_by(ChildRecord.kind)).all())
    pending_query=select(User).where(*filters,User.role.in_(['ADMIN','DOCTOR']),User.approval_status=='PENDING_APPROVAL',User.email_verified.is_(True))
    pending_total=db().scalar(select(func.count()).select_from(pending_query.subquery()))
    pending=db().scalars(pending_query.order_by(User.created_at,User.id).limit(4)).all()
    recent=db().scalars(select(User).where(*filters).order_by(User.created_at.desc(),User.id).limit(5)).all()
    event_query=select(AuditLog)
    if admin:event_query=event_query.where(AuditLog.actor_id.in_(select(User.id).where(*filters)),AuditLog.action.in_(['registered','care_profile_created','care_profile_updated']))
    events=db().scalars(event_query.order_by(AuditLog.created_at.desc(),AuditLog.id.desc()).limit(5)).all()
    ids={value for row in events for value in (row.actor_id,row.target_id) if value}
    names={row.id:row.full_name for row in db().scalars(select(User).where(User.id.in_(ids))).all()} if ids else {}
    approved=db().scalar(select(func.count()).select_from(User).where(*filters,User.role=='DOCTOR',User.approval_status=='APPROVED'))
    return dict(approved_doctors=approved,metrics={key:dict(total=totals.get(role,0),this_month=added.get(role,0)) for key,role in [('administrators','ADMIN'),('doctors','DOCTOR'),('patients','PATIENT')]}|
            {'children':dict(total=children,this_month=new_children)},monthly_growth=growth,
        recent_registrations=[person(user) for user in recent],
        pending_requests=dict(total=pending_total,items=[dict(person(user),can_review=user.role==('DOCTOR' if admin else 'ADMIN')) for user in pending]),
        recent_activities=[dict(id=row.id,action=row.action,person=names.get(row.target_id) or names.get(row.actor_id) or 'System',created_at=row.created_at.isoformat()+'Z') for row in events],
        child_care=dict(total_children=children,active_guides=children-inactive,inactive_guides=inactive,
            growth_records=record_counts.get('growth',0),nutrition_records=record_counts.get('nutrition',0),vaccination_records=record_counts.get('vaccination',0)),
        as_of=current.isoformat())


def search(admin=False):
    from flask import request,jsonify
    query=request.args.get('q','').strip()[:80]
    if len(query)<2:return jsonify(items=[])
    pattern='%'+query.replace('\\','\\\\').replace('%','\\%').replace('_','\\_')+'%'
    rows=db().scalars(select(User).where(*visible_users(),User.role.in_(['DOCTOR','PATIENT'] if admin else ['DOCTOR','PATIENT','ADMIN']),or_(User.full_name.ilike(pattern,escape='\\'),User.email.ilike(pattern,escape='\\'),User.public_id.ilike(pattern,escape='\\')))
        .order_by(User.full_name,User.id).limit(8)).all()
    return jsonify(items=[person(row) for row in rows])
