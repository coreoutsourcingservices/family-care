"""Private profile notes/tasks with UTC scheduling and idempotent inbox delivery."""
from datetime import datetime, timezone
from typing import Literal
from flask import Blueprint, g, jsonify
from pydantic import Field, model_validator
from sqlalchemy import select
from core.database import db
from core.errors import APIError
from core.models import ProfilePlanner, CareProfile, User, AppNotification, now
from core.routing import route
from core.schemas import Schema, parse
from services.care import accessible_profile
from services.repository import audit

bp=Blueprint('profile_planner',__name__,url_prefix='/api/v1/patients/profiles')

class Entry(Schema):
    kind: Literal['note','task']
    title: str=Field(min_length=1,max_length=160)
    body: str=Field(default='',max_length=5000)
    due_at: datetime | None=None
    completed: bool=False
    version: int=Field(default=0,ge=0)

    @model_validator(mode='after')
    def validate_entry(self):
        self.title=self.title.strip()
        if not self.title:raise ValueError('Enter a title')
        if self.kind=='task' and not self.due_at:raise ValueError('Choose a task date and time')
        if self.due_at:
            if self.due_at.tzinfo is None:raise ValueError('Task time must include a timezone')
            self.due_at=self.due_at.astimezone(timezone.utc).replace(tzinfo=None)
        if self.kind=='note':self.due_at=None;self.completed=False
        return self

def profile(identifier):
    row=accessible_profile(g.user,str(identifier))
    if row.module not in ('adult','women'):raise APIError(404,'profile_not_found','Adult or Women profile required')
    return row

def stamp(value):return value.isoformat()+'Z' if value else None
def data(row):return dict(id=row.id,kind=row.kind,title=row.title,body=row.body,due_at=stamp(row.due_at),completed=bool(row.completed_at),completed_at=stamp(row.completed_at),version=row.version)

def clear_alerts(row):
    for notice in db().scalars(select(AppNotification).where(AppNotification.user_id==row.user_id,AppNotification.kind=='task_due',AppNotification.read_at.is_(None))):
        if notice.data.get('entry_id')==row.id:notice.read_at=now()

def listing(profile_id):
    owner=profile(profile_id)
    rows=db().scalars(select(ProfilePlanner).where(ProfilePlanner.profile_id==owner.id,ProfilePlanner.user_id==g.user.id,ProfilePlanner.deleted_at.is_(None)).order_by(ProfilePlanner.created_at.desc())).all()
    return jsonify(items=[data(row) for row in rows])

def save(profile_id,entry_id=None):
    owner=profile(profile_id);value=parse(Entry)
    row=None
    if entry_id:
        row=db().scalar(select(ProfilePlanner).where(ProfilePlanner.id==str(entry_id),ProfilePlanner.profile_id==owner.id,ProfilePlanner.user_id==g.user.id,ProfilePlanner.deleted_at.is_(None)).with_for_update())
        if not row:raise APIError(404,'entry_not_found','Entry not found')
        if row.version!=value.version:raise APIError(409,'entry_changed','Entry changed. Refresh and try again.')
        if row.kind!=value.kind:raise APIError(422,'kind_changed','Entry type cannot change')
    created=row is None
    if created:
        row=ProfilePlanner(profile_id=owner.id,user_id=g.user.id,kind=value.kind,version=0)
        db().add(row)
    was_complete=bool(row.completed_at)
    if not created and (value.completed or row.due_at!=value.due_at):clear_alerts(row)
    row.title=value.title;row.body=value.body;row.due_at=value.due_at
    row.completed_at=(row.completed_at or now()) if value.completed else None
    row.version+=1
    db().flush()
    if value.completed and not was_complete:
        from services.notifications import enqueue
        enqueue(g.user.id,'task_completed','Task completed','Your task has been marked complete.',{'profile_id':owner.id,'module':owner.module,'area':'planner','entry_id':row.id},event_key='task-complete:'+row.id+':'+str(row.version))
    audit('planner_created' if created else 'planner_updated',g.user.id,g.user.id)
    db().commit()
    return jsonify(entry=data(row)),201 if created else 200

def remove(profile_id,entry_id):
    owner=profile(profile_id)
    row=db().scalar(select(ProfilePlanner).where(ProfilePlanner.id==str(entry_id),ProfilePlanner.profile_id==owner.id,ProfilePlanner.user_id==g.user.id,ProfilePlanner.deleted_at.is_(None)).with_for_update())
    if not row:raise APIError(404,'entry_not_found','Entry not found')
    from services.recycle_bin import retain
    clear_alerts(row);row.deleted_at=now();retain('planner',row,profile_id=owner.id);audit('planner_deleted',g.user.id,g.user.id);db().commit()
    return jsonify(message='Entry removed')

def scan_tasks(user_id=None):
    query=select(ProfilePlanner).join(CareProfile,CareProfile.id==ProfilePlanner.profile_id).join(User,User.id==ProfilePlanner.user_id).where(ProfilePlanner.kind=='task',ProfilePlanner.completed_at.is_(None),ProfilePlanner.deleted_at.is_(None),ProfilePlanner.due_at<=now(),CareProfile.deleted_at.is_(None),User.account_status=='ACTIVE',User.approval_status=='APPROVED',User.email_verified.is_(True))
    if user_id:query=query.where(ProfilePlanner.user_id==user_id)
    from services.notifications import enqueue
    from services.women_workspace import primary_id
    from services.care import patient_profile_access
    for row in db().scalars(query.with_for_update(of=ProfilePlanner)).all():
        owner=db().get(CareProfile,row.profile_id);user=db().get(User,row.user_id)
        # Revoked invitations or transferred ownership stop personal alerts.
        if owner.module=='women':
            if primary_id(owner)!=row.user_id:continue
        elif not db().scalar(select(CareProfile.id).where(CareProfile.id==owner.id,patient_profile_access(user))):continue
        enqueue(row.user_id,'task_due','Task reminder','A saved task is due. Open your notes and tasks to review it.',{'profile_id':owner.id,'module':owner.module,'area':'planner','entry_id':row.id,'due_at':stamp(row.due_at)},event_key='task-due:'+row.id+':'+stamp(row.due_at))
    db().commit()

route(bp,'/<uuid:profile_id>/planner',listing,roles=('PATIENT',))
route(bp,'/<uuid:profile_id>/planner',save,'POST',roles=('PATIENT',))
def update_entry(profile_id,entry_id):return save(profile_id,entry_id)
route(bp,'/<uuid:profile_id>/planner/<uuid:entry_id>',update_entry,'PUT',roles=('PATIENT',))
route(bp,'/<uuid:profile_id>/planner/<uuid:entry_id>',remove,'DELETE',roles=('PATIENT',))
