"""Single-use invitation link; family email OTP approves member account creation."""
import hmac
import secrets
import smtplib
from datetime import timedelta
from urllib.parse import quote
from flask import Blueprint, current_app, g, jsonify
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from core.database import db
from core.errors import APIError
from core.models import FamilyInvitation, User, PatientProfile, CareProfile, uid, now
from core.security import digest, password_hasher
from core.routing import route
from core.schemas import parse
from core.family_schemas import FamilyInvite, FamilySetup, FamilyOTP
from services.repository import find_user, audit, serialize_user
from services.otp import otp_code, code_hash
from services.email import send_mail
from services.care import profile_data

bp=Blueprint('family_invitations',__name__,url_prefix='/api/v1')


def deliver(email,subject,body):
    try:send_mail(email,subject,body,uid())
    except (OSError,smtplib.SMTPException,RuntimeError):
        raise APIError(503,'email_delivery_failed','Email could not be sent. Please try again.') from None


def summary(row):
    return dict(id=row.id,full_name=row.full_name,email=row.email,module=row.module,
        relationship=row.relationship,status='ACCEPTED' if row.accepted_at else 'REVOKED' if row.revoked_at else 'EXPIRED' if row.expires_at<=now() else 'PENDING',
        expires_at=row.expires_at.isoformat()+'Z',profile_id=row.profile_id)


def resolve(token):
    row=db().scalar(select(FamilyInvitation).where(FamilyInvitation.token_hash==digest(token)).with_for_update())
    if not row:raise APIError(404,'invite_not_found','Invitation not found')
    if row.accepted_at or row.revoked_at or row.expires_at<=now():
        raise APIError(410,'invite_unavailable','Invitation expired, revoked or already accepted')
    owner=db().scalar(select(User).where(User.id==row.owner_id).with_for_update())
    if not owner or owner.account_status!='ACTIVE':raise APIError(410,'invite_unavailable','Inviting family is unavailable')
    return row,owner


def create_invite():
    value=parse(FamilyInvite)
    if find_user(value.email):raise APIError(409,'account_exists','This email already has an account; no existing account is linked automatically')
    # Serialise invitation creation within a family.
    db().scalar(select(User).where(User.id==g.user.id).with_for_update())
    existing=db().scalar(select(FamilyInvitation).where(FamilyInvitation.owner_id==g.user.id,
        FamilyInvitation.email==value.email,FamilyInvitation.accepted_at.is_(None),
        FamilyInvitation.revoked_at.is_(None),FamilyInvitation.expires_at>now()))
    if existing:raise APIError(409,'invite_exists','An active invitation already exists; revoke it before sending another')
    token=secrets.token_urlsafe(32)
    row=FamilyInvitation(id=uid(),owner_id=g.user.id,token_hash=digest(token),
        full_name=value.full_name,email=value.email,module=value.module,relationship=value.relationship,
        expires_at=now()+timedelta(hours=24))
    db().add(row);db().flush()
    base=current_app.config['FAMILY_INVITE_FRONTEND_URL'].rstrip('/')
    link=base+'/customer/family-invite#token='+quote(token)
    deliver(row.email,'FamilyCare - Family invitation',
        f'Hello {row.full_name},\n{g.user.full_name} ({g.user.email}) invited you to their family as {row.relationship}.\n'
        f'Care area: {row.module}.\nOpen this one-use link within 24 hours:\n{link}\n'
        'Set your own password. The inviting family receives the setup approval OTP. '
        'Accepting links your care profile with this family; they can access that shared profile. Ignore this email if unexpected.')
    audit('family_invite_sent',g.user.id,g.user.id);db().commit()
    return jsonify(invitation=summary(row),email_status='sent'),201


def list_invites():
    from core.http import pagination
    from services.approvals import paginate
    page,size=pagination()
    rows,total=paginate(select(FamilyInvitation).where(FamilyInvitation.owner_id==g.user.id).order_by(FamilyInvitation.created_at.desc()),page,size)
    return jsonify(items=[summary(row) for row in rows],total=total,page=page,per_page=size)


def revoke_invite(invite_id):
    row=db().scalar(select(FamilyInvitation).where(FamilyInvitation.id==str(invite_id),FamilyInvitation.owner_id==g.user.id).with_for_update())
    if not row:raise APIError(404,'invite_not_found','Invitation not found')
    if row.accepted_at:raise APIError(409,'invite_accepted','Accepted membership cannot be revoked as an invitation')
    row.revoked_at=now();row.pending=None;db().commit()
    return jsonify(message='Invitation revoked')


def preview(token):
    row,owner=resolve(token)
    return jsonify(invitation=summary(row),family=dict(full_name=owner.full_name,email=owner.email),
        form=dict(full_name=row.full_name,email=row.email,readonly=['full_name','email']),
        otp_destination='inviting_family_email',shared_profile=True)


def send_approval(row,owner,pending):
    if pending.get('sent_at') and now().timestamp()-pending['sent_at']<60:
        raise APIError(429,'otp_cooldown','Wait 60 seconds before requesting another OTP')
    cid=uid()
    deliver(owner.email,'FamilyCare - Approve family member setup',
        f'{owner.full_name},\n{row.full_name} ({row.email}) is accepting your {row.module} invitation as {row.relationship}.\n'
        f'Share this approval OTP with that member only: {otp_code(cid)}\nValid for 5 minutes. '
        'This code approves creation of their independent login and links their care profile to your family.')
    row.pending={**pending,'cid':cid,'code_hash':code_hash(cid,otp_code(cid)),
        'sent_at':now().timestamp(),'expires_at':(now()+timedelta(minutes=5)).timestamp(),'attempts':0}
    db().commit()
    return jsonify(message='Approval OTP sent to the inviting family email.',email_status='sent',
        otp_destination='inviting_family_email',expires_in=300,resend_after=60),202


def setup(token):
    row,owner=resolve(token);value=parse(FamilySetup)
    if value.full_name!=row.full_name or str(value.email).lower()!=row.email:
        raise APIError(422,'invite_identity_locked','Name and email must match the family invitation')
    if find_user(row.email):raise APIError(409,'account_exists','This email already has an account')
    if row.pending and now().timestamp()-row.pending['sent_at']<60:
        raise APIError(429,'otp_cooldown','Wait 60 seconds before requesting another OTP')
    return send_approval(row,owner,dict(mobile_number=value.mobile_number,date_of_birth=value.date_of_birth.isoformat(),password_hash=password_hasher.hash(value.password)))


def resend(token):
    row,owner=resolve(token)
    if not row.pending:raise APIError(409,'setup_required','Submit the member setup form first')
    return send_approval(row,owner,row.pending)


def verify(token):
    row,owner=resolve(token);value=parse(FamilyOTP);pending=row.pending
    if not pending or pending['expires_at']<=now().timestamp() or pending['attempts']>=5:
        raise APIError(400,'otp_unavailable','OTP expired or attempts exhausted; request a fresh OTP')
    if not hmac.compare_digest(pending['code_hash'],code_hash(pending['cid'],value.otp)):
        row.pending={**pending,'attempts':pending['attempts']+1};db().commit()
        raise APIError(400,'invalid_otp','Invalid OTP')
    if find_user(row.email):raise APIError(409,'account_exists','This email already has an account')
    user=User(id=uid(),public_id=('C'+secrets.token_hex(6)) if db().bind.dialect.name=='sqlite' else None,
        role='PATIENT',full_name=row.full_name,email=row.email,phone_number=pending['mobile_number'],
        password_hash=pending['password_hash'],email_verified=True,approval_status='APPROVED',account_status='ACTIVE')
    db().add(user)
    try:
        db().flush();db().refresh(user)
        db().add(PatientProfile(user_id=user.id))
        from datetime import date
        profile=CareProfile(id=uid(),owner_id=owner.id,profile_type='member',module=row.module,
            name=row.full_name,dob=date.fromisoformat(pending['date_of_birth']),guardian_contact='',guardian_name='',emergency_contacts=[])
        db().add(profile);db().flush()
        row.member_id=user.id;row.profile_id=profile.id;row.accepted_at=now();row.pending=None
        from services.notifications import enqueue
        enqueue(owner.id,'family_member_joined','Family member joined',f'{row.full_name} completed their profile.',{'profile_id':profile.id,'module':row.module},'family-joined:'+row.id)
        audit('family_member_joined',user.id,owner.id);db().commit()
    except IntegrityError:
        db().rollback();raise APIError(409,'account_exists','The account or invitation was already completed') from None
    return jsonify(message='Profile setup complete. Sign in with your own email and password.',user=serialize_user(user),profile=profile_data(profile),family=dict(full_name=owner.full_name,relationship=row.relationship)),201


route(bp,'/patients/family-invitations',create_invite,'POST',roles=('PATIENT',),schema=FamilyInvite,limited=True)
route(bp,'/patients/family-invitations',list_invites,roles=('PATIENT',))
route(bp,'/patients/family-invitations/<uuid:invite_id>',revoke_invite,'DELETE',roles=('PATIENT',))
route(bp,'/family-invitations/<token>',preview,limited=True)
route(bp,'/family-invitations/<token>/setup',setup,'POST',schema=FamilySetup,limited=True)
route(bp,'/family-invitations/<token>/resend-otp',resend,'POST',limited=True)
route(bp,'/family-invitations/<token>/verify-otp',verify,'POST',schema=FamilyOTP,limited=True)
