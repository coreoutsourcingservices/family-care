"""Retain user-deleted content for 30 days; never restore permissions or sessions."""
from datetime import timedelta
from flask import g, jsonify
from sqlalchemy import select, delete, or_
from core.database import db
from core.errors import APIError
from core.models import (RecycleItem, CareProfile, CareReport, ChildRecord, AdultRecord,
    WomenDiaryRecord, ProfilePlanner, CustomerNote, AuditLog, DoctorProfile, FamilyInvitation, ReportText, now, uid)
from services.repository import audit

TYPES={'activity_log':AuditLog,'profile':CareProfile,'report':CareReport,'child_record':ChildRecord,'adult_record':AdultRecord,
       'women_diary':WomenDiaryRecord,'planner':ProfilePlanner,'customer_note':CustomerNote}
LABELS={'activity_log':'Activity entry','profile':'Care profile','report':'Medical report','child_record':'Child care record',
    'adult_record':'Adult care record','women_diary':'Women diary entry','planner':'Note or task',
    'customer_note':'Personal note','doctor_photo':'Doctor image'}


def retain(kind,row,actor_id=None,profile_id=None,group_id=None,payload=None):
    """Caller owns the transaction and sets deleted_at on persistent content."""
    stamp=now()
    item=RecycleItem(id=uid(),entity_type=kind,entity_id=row.id if hasattr(row,'id') else str(row),
        actor_id=actor_id or g.user.id,profile_id=profile_id,group_id=group_id,
        payload=payload or {},deleted_at=stamp,expires_at=stamp+timedelta(days=30))
    db().add(item)
    return item


def visible_bin():
    # Admin cannot restore or purge history deleted from the superadmin portal.
    from sqlalchemy import func
    query=select(RecycleItem)
    if g.user.role!='SUPERADMIN':
        query=query.where(func.coalesce(RecycleItem.payload['portal'].as_string(),'admin')!='superadmin')
    return query


def listing():
    from core.http import pagination
    from services.approvals import paginate
    from core.models import User
    from core.security import encode_token
    from hashlib import sha256
    selected=sorted(db().scalars(visible_bin().with_only_columns(RecycleItem.id)).all())
    delete_token=encode_token(g.user,'empty_recycle_bin',10,portal=g.user.role,count=len(selected),fingerprint=sha256('|'.join(selected).encode()).hexdigest())
    page,size=pagination()
    rows,total=paginate(visible_bin().order_by(RecycleItem.deleted_at.desc(),RecycleItem.id.desc()),page,size)
    actors={u.id:u for u in db().scalars(select(User).where(User.id.in_({r.actor_id for r in rows})))} if rows else {}
    # Deliberately exclude report names, medical contents, photo storage keys and notes.
    return jsonify(items=[dict(id=r.id,type=r.entity_type,label=LABELS.get(r.entity_type,'Deleted item'),
        actor=actors[r.actor_id].full_name if r.actor_id in actors else 'Unknown',
        deleted_at=r.deleted_at.isoformat()+'Z',expires_at=r.expires_at.isoformat()+'Z',
        expired=r.expires_at<=now(),requires_report=bool(r.group_id)) for r in rows],total=total,page=page,per_page=size,delete_token=delete_token)


def restore(item_id):
    item=db().scalar(visible_bin().where(RecycleItem.id==str(item_id)).with_for_update())
    if not item:raise APIError(404,'recycle_item_not_found','Deleted item not found')
    if item.expires_at<=now():raise APIError(409,'recycle_expired','The 30-day restore period has ended')
    if item.group_id:raise APIError(409,'restore_report_first','Restore the linked report to recover this imported record')
    if item.entity_type=='doctor_photo':
        profile=db().scalar(select(DoctorProfile).where(DoctorProfile.user_id==item.entity_id).with_for_update())
        if not profile:raise APIError(409,'restore_unavailable','Doctor profile is unavailable')
        if (profile.onboarding_images or {}).get(item.payload['kind']):
            raise APIError(409,'image_exists','Remove the current image before restoring this image')
        profile.onboarding_images={**(profile.onboarding_images or {}),item.payload['kind']:item.payload['asset']}
    else:
        model=TYPES.get(item.entity_type)
        row=db().scalar(select(model).where(model.id==item.entity_id).with_for_update()) if model else None
        if not row or not row.deleted_at:raise APIError(409,'restore_unavailable','This content is no longer available')
        if item.profile_id and item.entity_type!='profile':
            profile=db().get(CareProfile,item.profile_id)
            if not profile or profile.deleted_at:raise APIError(409,'restore_parent_first','Restore the care profile first')
        row.deleted_at=None
        if item.entity_type in ('women_diary','planner'):
            row.version+=1
        if item.entity_type=='report':
            # Restore only imported child records removed as part of this report deletion.
            linked=db().scalars(select(RecycleItem).where(RecycleItem.group_id==item.id,RecycleItem.expires_at>now()).with_for_update()).all()
            for child in linked:
                record=db().get(ChildRecord,child.entity_id)
                if record and record.deleted_at:record.deleted_at=None
                db().delete(child)
    audit('recycle_item_restored',item.actor_id,g.user.id)
    db().delete(item);db().commit()
    return jsonify(message='Item restored')


def destroy_asset(asset,resource_type):
    import cloudinary.uploader
    from services.care_uploads import credentials
    result=cloudinary.uploader.destroy(asset,resource_type=resource_type,type='authenticated',invalidate=True,**credentials())
    if result.get('result') not in ('ok','not found'):
        raise RuntimeError('Cloud storage deletion failed')


def purge_one():
    item=db().scalar(select(RecycleItem).where(RecycleItem.expires_at<=now(),or_(RecycleItem.retry_after.is_(None),RecycleItem.retry_after<=now())).order_by(RecycleItem.expires_at,RecycleItem.id).with_for_update(skip_locked=True).limit(1))
    if not item:
        db().rollback();return False
    item_id=item.id
    try:
        _purge_item(item)
    except Exception as exc:
        db().rollback()
        failed=db().scalar(select(RecycleItem).where(RecycleItem.id==item_id).with_for_update())
        if failed:
            failed.retry_after=now()+timedelta(hours=1)
            db().commit()
        from flask import current_app
        current_app.logger.warning('Recycle bin purge failed for %s: %s',item_id,type(exc).__name__)
    return True


def _purge_item(item):
    kind=item.entity_type
    if kind=='doctor_photo':
        destroy_asset(item.payload['asset']['public_id'],'image')
    elif kind in TYPES:
        model=TYPES[kind]
        row=db().scalar(select(model).where(model.id==item.entity_id).with_for_update())
        if row and row.deleted_at:
            if kind=='profile':
                newer=db().scalar(select(RecycleItem.id).where(RecycleItem.profile_id==row.id,
                    RecycleItem.id!=item.id,RecycleItem.expires_at>now()).limit(1))
                if newer:
                    raise RuntimeError('Profile contains an item still within its retention period')
                # Preserve the full profile until its own 30 days have passed, then remove cloud files first.
                for report in db().scalars(select(CareReport).where(CareReport.profile_id==row.id).with_for_update()).all():
                    if report.storage_provider=='cloudinary':destroy_asset(report.cloudinary_public_id,report.resource_type)
                invitations=db().scalars(select(FamilyInvitation).where(FamilyInvitation.profile_id==row.id).with_for_update()).all()
                from core.models import User
                from services.repository import revoke_sessions
                for invitation in invitations:
                    if invitation.member_id:
                        member=db().get(User,invitation.member_id)
                        if member:member.account_status='SUSPENDED';revoke_sessions(member.id)
                    invitation.profile_id=None
                db().flush()
                db().execute(delete(RecycleItem).where(RecycleItem.profile_id==row.id,RecycleItem.id!=item.id))
            elif kind=='report':
                if row.storage_provider=='cloudinary':destroy_asset(row.cloudinary_public_id,row.resource_type)
                # Delete the extraction explicitly; the storage operation is idempotent on retry.
                text=db().get(ReportText,row.id)
                if text:db().delete(text)
            db().delete(row)
    else:
        raise RuntimeError('Unknown recycle item type')
    audit('recycle_item_purged',item.actor_id,None)
    db().delete(item);db().commit()


def empty_bin():
    """Permanently remove the confirmed bin snapshot, including unexpired items."""
    from core.schemas import Schema,parse
    from core.security import decode_token
    from pydantic import Field
    from typing import Literal
    from hashlib import sha256
    class Confirmation(Schema):
        token: str = Field(min_length=1,max_length=8000)
        confirmed: Literal[True]
    data=parse(Confirmation)
    claims=decode_token(data.token,'empty_recycle_bin')
    if claims['sub']!=g.user.id or claims.get('portal')!=g.user.role:
        raise APIError(403,'forbidden','This selection belongs to another administrator')
    selected=sorted(db().scalars(visible_bin().with_only_columns(RecycleItem.id)).all())
    if len(selected)!=claims['count'] or sha256('|'.join(selected).encode()).hexdigest()!=claims['fingerprint']:
        raise APIError(409,'selection_changed','Recycle Bin changed. Refresh and confirm again.')
    # Remove nested items before profiles so a failed child asset remains recoverable.
    rows=db().execute(select(RecycleItem.id,RecycleItem.entity_type).where(RecycleItem.id.in_(selected))).all()
    ordered=sorted(rows,key=lambda r:(r.entity_type=='profile',r.id))
    db().rollback()
    deleted=failed=0
    # Activity history commonly contains hundreds of entries. Avoid a remote
    # database transaction and audit insert for every individual entry.
    activity_ids=[identifier for identifier,kind in ordered if kind=='activity_log']
    if activity_ids:
        markers=db().scalars(select(RecycleItem).where(RecycleItem.id.in_(activity_ids)).with_for_update()).all()
        entity_ids=[marker.entity_id for marker in markers]
        db().execute(delete(AuditLog).where(AuditLog.id.in_(entity_ids),AuditLog.deleted_at.is_not(None)))
        db().execute(delete(RecycleItem).where(RecycleItem.id.in_([marker.id for marker in markers])))
        audit('recycle_bin_emptied',actor_id=g.user.id)
        db().commit()
        deleted=len(markers)
    for identifier,kind in ordered:
        if kind=='activity_log':continue
        item=db().scalar(select(RecycleItem).where(RecycleItem.id==identifier).with_for_update())
        if not item:
            db().rollback();continue
        try:
            _purge_item(item)
            deleted+=1
        except Exception:
            db().rollback();failed+=1
            from flask import current_app
            current_app.logger.warning('Manual recycle purge failed for %s',identifier)
    return jsonify(deleted=deleted,failed=failed,message='Some items could not be deleted. Retry later.' if failed else 'Recycle Bin emptied')
