"""A connected qualified doctor may confirm applicability; no catch-up dates are generated."""
from flask import g, request, jsonify
from sqlalchemy import select
from pydantic import Field
from typing import Literal
from uuid import UUID
from core.database import db
from core.models import CareProfile, ChildVaccinationContext, now
from core.schemas import Schema, parse
from core.errors import APIError
from services import vaccination as v

class Decision(Schema):
 schedule_id: UUID
 decision: Literal['CONFIRM','NOT_APPLICABLE']
 notes: str=Field(min_length=20,max_length=2000)
 attestation: bool


def signature(profile,schedule,context):
 return v.fingerprint({'schedule':schedule.data,'dob':profile.dob.isoformat(),'doctor_id':profile.referred_doctor_id,'context':{key:context.get(key) for key in ('country','state','district','gender','history_status')}})


def current_decision(profile,schedule,context):
 entry=context.get('doctor_dose_decisions',{}).get(schedule.id)
 if entry and entry.get('signature')==signature(profile,schedule,context) and entry.get('doctor_id')==profile.referred_doctor_id:return entry
 return None


def plan(profile_id):
 v.qualified_reviewer(g.user.id)
 profile=db().scalar(select(CareProfile).where(CareProfile.id==str(profile_id),CareProfile.module=='child',CareProfile.deleted_at.is_(None),CareProfile.referred_doctor_id==g.user.id).with_for_update())
 if not profile:raise APIError(404,'profile_not_found','Connected child profile not found')
 if request.method=='GET':
  return jsonify(child={'id':profile.id,'name':profile.name},UIP=v.timeline(profile,'UIP'),IAP=v.timeline(profile,'IAP'))
 value=parse(Decision)
 if not value.attestation or len(value.notes.strip())<20:raise APIError(422,'attestation_required','Confirm professional review and enter substantive notes')
 schedule=v.schedule_row(value.schedule_id)
 if schedule.status!='PUBLISHED' and (schedule.status=='RETIRED' or not schedule.data.get('child_visible') or not schedule.data.get('active',True)):
  raise APIError(409,'unpublished_schedule','Select an active visible child plan')
 context=dict(v.child_context(profile))
 if value.decision=='CONFIRM' and (context.get('country')!='IN' or context.get('history_status')!='PARENT_REPORTED'):raise APIError(422,'context_required','Ask the parent to confirm location and vaccination history first')
 if schedule.data['vaccine']['code']=='FC_JE' and (not context.get('state') or not context.get('district')):raise APIError(422,'district_required','JE review needs the child state and district')
 if schedule.data['vaccine']['code']=='FC_HPV' and context.get('gender','Unknown')=='Unknown':raise APIError(422,'context_required','HPV review needs the applicable sex/gender recorded')
 decisions=dict(context.get('doctor_dose_decisions',{}));decisions[schedule.id]=dict(decision=value.decision,notes=value.notes.strip(),doctor_id=g.user.id,reviewed_at=now().isoformat()+'Z',signature=signature(profile,schedule,context))
 context['doctor_dose_decisions']=decisions
 row=db().get(ChildVaccinationContext,profile.id)
 if row:row.data=context
 else:db().add(ChildVaccinationContext(profile_id=profile.id,data=context))
 v.log('child_applicability_reviewed',schedule=schedule,snapshot={'profile_id':profile.id,'decision':value.decision,'notes':value.notes.strip()})
 db().commit();return jsonify(message='Child-specific applicability saved. Recorded doses and routine dates were not changed.')
