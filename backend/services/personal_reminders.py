"""Idempotent, private in-app reminders; no email or browser-push claim."""
from sqlalchemy import select,or_
from core.database import db
from core.models import CareProfile,WomenDiaryRecord,AdultRecord,AppNotification,FamilyInvitation

def key(kind,row):return 'personal-reminder:'+kind+':'+row.id+':'+row.data.get('date','')

def scan(user_id):
    from patient.child_routes import today
    from services.women_workspace import primary_id
    from services.notifications import enqueue
    day=today().isoformat()
    accepted=select(FamilyInvitation.profile_id).where(FamilyInvitation.member_id==user_id,FamilyInvitation.accepted_at.is_not(None),FamilyInvitation.revoked_at.is_(None))
    profiles=db().scalars(select(CareProfile).where(CareProfile.deleted_at.is_(None),CareProfile.module.in_(['adult','women']),or_(CareProfile.owner_id==user_id,CareProfile.id.in_(accepted)))).all()
    for profile in profiles:
        if primary_id(profile)!=user_id:continue
        model=WomenDiaryRecord if profile.module=='women' else AdultRecord
        query=select(model).where(model.profile_id==profile.id,model.deleted_at.is_(None))
        query=query.where(model.section=='reminder') if profile.module=='women' else query.where(model.kind=='reminder')
        for row in db().scalars(query):
            if row.data.get('status')!='Planned' or not row.data.get('date') or row.data['date']>day:continue
            enqueue(user_id,'personal_reminder','Your health reminder is due','Open your private profile to review this reminder.',{'profile_id':profile.id,'module':profile.module,'record_id':row.id},event_key=key(profile.module,row))
    db().commit()

def delivery(kind,row,user_id):
    return 'AVAILABLE_IN_APP' if db().scalar(select(AppNotification.id).where(AppNotification.user_id==user_id,AppNotification.event_key==key(kind,row)).limit(1)) else 'SAVED_ONLY'
