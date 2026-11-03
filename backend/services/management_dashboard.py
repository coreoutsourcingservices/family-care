"""Aggregate organization dashboard; never exposes child medical record contents."""
from datetime import datetime,timezone,timedelta,date,time
from calendar import monthrange
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
    pending_query=select(User).where(*filters,User.role.in_(['DOCTOR'] if admin else ['ADMIN','DOCTOR','PATIENT']),User.approval_status=='PENDING_APPROVAL',User.email_verified.is_(True))
    pending_by_role=dict(db().execute(pending_query.with_only_columns(User.role,func.count()).group_by(User.role)).all())
    pending_total=db().scalar(select(func.count()).select_from(pending_query.subquery()))
    pending=db().scalars(pending_query.order_by(User.created_at,User.id).limit(4)).all()
    recent=db().scalars(select(User).where(*filters).order_by(User.created_at.desc(),User.id).limit(5)).all()
    event_query=select(AuditLog).where(AuditLog.deleted_at.is_(None))
    if admin:event_query=event_query.where(AuditLog.actor_id.in_(select(User.id).where(*filters)),AuditLog.action.in_(['registered','care_profile_created','care_profile_updated']))
    events=db().scalars(event_query.order_by(AuditLog.created_at.desc(),AuditLog.id.desc()).limit(5)).all()
    ids={value for row in events for value in (row.actor_id,row.target_id) if value}
    names={row.id:row.full_name for row in db().scalars(select(User).where(User.id.in_(ids))).all()} if ids else {}
    approved=db().scalar(select(func.count()).select_from(User).where(*filters,User.role=='DOCTOR',User.approval_status=='APPROVED'))
    return dict(approved_doctors=approved,metrics={key:dict(total=totals.get(role,0),this_month=added.get(role,0)) for key,role in [('administrators','ADMIN'),('doctors','DOCTOR'),('patients','PATIENT')]}|
            {'children':dict(total=children,this_month=new_children)},monthly_growth=growth,
        recent_registrations=[person(user) for user in recent],
        pending_requests=dict(total=pending_total,by_role=pending_by_role,items=[dict(person(user),can_review=user.role=='DOCTOR' if admin else user.role in ('ADMIN','DOCTOR','PATIENT')) for user in pending]),
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


ADMIN_ACTIVITY_ACTIONS = ('registered','care_profile_created','care_profile_updated','login_success',
    'approval_approved','approval_rejected','account_suspended','account_active',
    'care_profile_removed','care_report_deleted','child_record_removed','doctor_vaccination_removed',
    'women_diary_removed','planner_deleted','customer_note_deleted','doctor_profile_photo_removed','recycle_item_restored','recycle_item_purged')


def activity_query(params, reference=None, superadmin=False):
    """Paginated operational metadata for admin, without medical record content."""
    from flask import jsonify, request
    from core.http import pagination
    from core.errors import APIError
    from services.approvals import paginate
    action = params.get('action','').strip()
    if action and not superadmin and action not in ADMIN_ACTIVITY_ACTIONS:
        raise APIError(400,'invalid_action','Choose a supported activity type')
    period=params.get('period','all').strip()
    if period not in ('7d','1m','1y','all','custom'):
        raise APIError(400,'invalid_period','Choose 7d, 1m, 1y, all or custom')
    local_now=reference or datetime.now(ZoneInfo('Asia/Kolkata'))
    start=end=None
    if period=='7d':
        start=local_now-timedelta(days=7)
    elif period in ('1m','1y'):
        month_index=local_now.year*12+local_now.month-1-(1 if period=='1m' else 12)
        year,month=divmod(month_index,12);month+=1
        start=local_now.replace(year=year,month=month,day=min(local_now.day,monthrange(year,month)[1]))
    elif period=='custom':
        try:
            raw_first=params.get('start_date','');raw_last=params.get('end_date','')
            first=date.fromisoformat(raw_first);last=date.fromisoformat(raw_last)
            if first.isoformat()!=raw_first or last.isoformat()!=raw_last or first>last or first.year<2 or last==date.max:raise ValueError()
        except (ValueError,OverflowError):
            raise APIError(400,'invalid_date_range','Choose valid start and end dates in order') from None
        start=datetime.combine(first,time.min,tzinfo=ZoneInfo('Asia/Kolkata'))
        end=datetime.combine(last+timedelta(days=1),time.min,tzinfo=ZoneInfo('Asia/Kolkata'))
    people = select(User.id).where(User.role.in_(['DOCTOR','PATIENT']))
    query = select(AuditLog).where(AuditLog.deleted_at.is_(None),AuditLog.action.in_(ADMIN_ACTIVITY_ACTIONS),
        or_(AuditLog.actor_id.in_(people), AuditLog.target_id.in_(people)))
    if superadmin:query=select(AuditLog).where(AuditLog.deleted_at.is_(None))
    if action:
        query = query.where(AuditLog.action==action)
    if start:
        query=query.where(AuditLog.created_at>=start.astimezone(timezone.utc).replace(tzinfo=None))
    if end:
        query=query.where(AuditLog.created_at<end.astimezone(timezone.utc).replace(tzinfo=None))
    return query


def recent_activity(superadmin=False):
    from flask import jsonify,request,g
    from core.http import pagination
    from services.approvals import paginate
    from core.security import encode_token
    from hashlib import sha256
    reference=datetime.now(ZoneInfo("Asia/Kolkata"))
    query=activity_query(request.args,reference,superadmin)
    cutoff=reference.astimezone(timezone.utc).replace(tzinfo=None)
    query=query.where(AuditLog.created_at<=cutoff)
    selected=sorted(db().scalars(query.with_only_columns(AuditLog.id)).all())
    token=encode_token(g.user,"activity_delete",10,portal="superadmin" if superadmin else "admin",filters={key:request.args.get(key,"") for key in ("period","action","start_date","end_date") if request.args.get(key)},reference=reference.isoformat(),fingerprint=sha256("|".join(selected).encode()).hexdigest(),count=len(selected))
    page,per_page=pagination()
    rows,total=paginate(query.order_by(AuditLog.created_at.desc(),AuditLog.id.desc()),page,per_page)
    ids={value for row in rows for value in (row.actor_id,row.target_id) if value}
    users={user.id:user for user in db().scalars(select(User).where(User.id.in_(ids)))} if ids else {}
    items=[]
    for row in rows:
        person=users.get(row.target_id) if row.target_id in users and users[row.target_id].role in ('DOCTOR','PATIENT') else users.get(row.actor_id)
        actor=users.get(row.actor_id)
        items.append(dict(id=row.id,action=row.action,person=person.full_name if person else 'System',
            person_role=person.role if person else None,actor_name=actor.full_name if actor else 'System / anonymous',
            target_name=users[row.target_id].full_name if row.target_id in users else None,actor_id=row.actor_id,target_id=row.target_id,
            created_at=row.created_at.isoformat()+'Z'))
    return jsonify(items=items,total=total,page=page,per_page=per_page,delete_token=token,actions=db().scalars(select(AuditLog.action).where(AuditLog.deleted_at.is_(None)).distinct().order_by(AuditLog.action)).all() if superadmin else list(ADMIN_ACTIVITY_ACTIONS))


def delete_recent_activity(superadmin=False):
    """Delete only the exact filtered snapshot the administrator confirmed."""
    from flask import g,jsonify
    from core.schemas import Schema,parse
    from pydantic import Field
    from typing import Literal
    from core.errors import APIError
    from core.security import decode_token
    from core.models import now
    from hashlib import sha256
    from services.recycle_bin import retain
    class Selection(Schema):
        token: str = Field(min_length=1,max_length=8000)
        confirmed: Literal[True]
    selection=parse(Selection)
    claims=decode_token(selection.token,'activity_delete')
    if claims['sub']!=g.user.id or claims.get('portal','admin')!=('superadmin' if superadmin else 'admin'):
        raise APIError(403,'forbidden','This selection belongs to another administrator')
    reference=datetime.fromisoformat(claims['reference'])
    query=activity_query(claims['filters'],reference,superadmin).where(AuditLog.created_at<=reference.astimezone(timezone.utc).replace(tzinfo=None))
    rows=db().scalars(query.order_by(AuditLog.id).with_for_update()).all()
    fingerprint=sha256('|'.join(sorted(row.id for row in rows)).encode()).hexdigest()
    if fingerprint!=claims['fingerprint'] or len(rows)!=claims['count']:
        raise APIError(409,'selection_changed','Activity changed. Refresh and confirm your selection again.')
    for row in rows:
        row.deleted_at=now()
        retain('activity_log',row,payload={'portal':'superadmin' if superadmin else 'admin'})
    db().commit()
    return jsonify(deleted=len(rows))
