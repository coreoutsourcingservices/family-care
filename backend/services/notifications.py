"""Authenticated notification REST API and transactional event helper."""
import hmac
from flask import Blueprint, g, jsonify
from sqlalchemy import select, func, update
from core.database import db
from core.models import AppNotification, User, UserSession, now
from core.errors import APIError
from core.http import pagination
from core.routing import route
from core.security import encode_token, decode_token, eligible, digest
from services.approvals import paginate

bp=Blueprint('notifications',__name__,url_prefix='/api/v1/notifications')
ROLES=('PATIENT','DOCTOR','ADMIN','SUPERADMIN')

def serialize(row):
    return dict(id=row.id,type=row.kind,title=row.title,body=row.body,data=row.data,created_at=row.created_at.isoformat()+'Z',read_at=row.read_at.isoformat()+'Z' if row.read_at else None)

def enqueue(user_id,kind,title,body,data=None,event_key=None,mirror=True):
    if not user_id:return
    user=db().get(User,user_id)
    if not user or user.account_status!='ACTIVE':return
    if event_key:
        existing=db().scalar(select(AppNotification).where(AppNotification.user_id==user_id,AppNotification.event_key==event_key))
        if existing:return existing
    row=AppNotification(user_id=user_id,kind=kind,title=title,body=body,data=data or {},event_key=event_key)
    db().add(row);db().flush()
    if mirror and user.role=='DOCTOR':
        from doctor.notifications import queue_notification, MESSAGES
        if kind in MESSAGES:queue_notification(user_id,kind,event_key or 'general:'+str(row.id))
    return row

def count(user_id):
    return db().scalar(select(func.count()).select_from(AppNotification).where(AppNotification.user_id==user_id,AppNotification.read_at.is_(None)))

def inbox():
    page,size=pagination()
    rows,total=paginate(select(AppNotification).where(AppNotification.user_id==g.user.id).order_by(AppNotification.id.desc()),page,size)
    return jsonify(items=[serialize(row) for row in rows],total=total,unread_count=count(g.user.id),page=page,per_page=size)

def unread():return jsonify(unread_count=count(g.user.id))

def mark(notification_id):
    row=db().scalar(select(AppNotification).where(AppNotification.id==notification_id,AppNotification.user_id==g.user.id).with_for_update())
    if not row:raise APIError(404,'not_found','Notification not found')
    if not row.read_at:row.read_at=now()
    if g.user.role=='DOCTOR' and row.event_key:
        from core.models import DoctorNotification
        other=db().scalar(select(DoctorNotification).where(DoctorNotification.user_id==g.user.id,DoctorNotification.event_key==row.event_key))
        if other:other.read_at=row.read_at
    db().commit()
    return jsonify(notification=serialize(row),unread_count=count(g.user.id))

def read_all():
    db().execute(update(AppNotification).where(AppNotification.user_id==g.user.id,AppNotification.read_at.is_(None)).values(read_at=now()))
    if g.user.role=='DOCTOR':
        from core.models import DoctorNotification
        db().execute(update(DoctorNotification).where(DoctorNotification.user_id==g.user.id,DoctorNotification.read_at.is_(None)).values(read_at=now()))
    db().commit()
    return jsonify(message='Notifications marked as read',unread_count=0)

def test():
    row=enqueue(g.user.id,'test','Notifications connected','Your realtime notification connection is working.')
    db().commit()
    return jsonify(notification=serialize(row)),201

def ticket():
    value=encode_token(g.user,'notification_socket',1,sid=g.auth_session.id,password_version=digest(g.user.password_hash))
    return jsonify(ticket=value,expires_in=60)

def socket_user(token=None,claims=None):
    claims=claims or decode_token(token,'notification_socket')
    user=db().get(User,claims['sub']);session=db().get(UserSession,claims.get('sid'))
    eligible(user)
    if not session or session.user_id!=user.id or session.revoked_at or session.expires_at<=now() or not hmac.compare_digest(claims.get('password_version',''),digest(user.password_hash)):
        raise APIError(401,'session_revoked','Sign in again')
    return user,claims

route(bp,'',inbox,roles=ROLES)
route(bp,'/unread-count',unread,roles=ROLES)
route(bp,'/socket-ticket',ticket,'POST',roles=ROLES,limited=True)
route(bp,'/test',test,'POST',roles=ROLES,limited=True)
route(bp,'/<int:notification_id>/read',mark,'POST',roles=ROLES)
route(bp,'/read-all',read_all,'POST',roles=ROLES)

def scan_due():
    """Generic notices only; no measurements, medicine names or patient names in payloads."""
    from datetime import timedelta, date
    from core.models import CareProfile, ChildPreferences, ChildRecord
    from patient.child_routes import today
    from services.vaccination import timeline
    day=today();near=day+timedelta(days=3)
    for profile in db().scalars(select(CareProfile).where(CareProfile.module=='child',CareProfile.deleted_at.is_(None))):
        owner=db().get(User,profile.owner_id)
        if not owner or not owner.email_verified or owner.approval_status!='APPROVED' or owner.account_status!='ACTIVE':continue
        pref=db().get(ChildPreferences,profile.id)
        if pref and not pref.in_app:continue
        due=[]
        for row in db().scalars(select(ChildRecord).where(ChildRecord.profile_id==profile.id,ChildRecord.kind=='vaccination',ChildRecord.deleted_at.is_(None))):
            value=row.data.get('nextDate') or (row.data.get('date') if row.data.get('status')=='Planned' else None)
            if value and value<=near.isoformat():due.append((row.id,value))
        for scheme in ('UIP','IAP'):
            for item in timeline(profile,scheme)['items']:
                policy=item.get('reminders',{})
                if not policy.get('enabled') or not policy.get('in_app',True) or item.get('status') not in ('UPCOMING','DUE','OVERDUE'):continue
                start=date.fromisoformat(item['recommended_date']);end=date.fromisoformat(item['window_end'])
                if (start-day).days in policy.get('before_days',[]) or policy.get('on_due') and start<=day<=end or (day-end).days in policy.get('overdue_days',[]):due.append((item['id'],day.isoformat()))
        for source,due_date in due:
            event='vaccine-due:'+profile.id+':'+source+':'+due_date
            data={'profile_id':profile.id,'area':'vaccination'}
            for recipient in (profile.owner_id,profile.referred_doctor_id):
                enqueue(recipient,'vaccination_due','Child vaccination reminder','A vaccination date needs attention. Sign in to review the child care timeline.',data,event_key=event)
    db().commit()
