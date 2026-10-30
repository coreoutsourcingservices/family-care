"""Versioned source-based routine windows; never generates catch-up prescriptions."""
import hashlib
import json
from calendar import monthrange
from datetime import date, timedelta
from flask import g, jsonify, request
from sqlalchemy import select, func
from core.database import db
from core.errors import APIError
from core.http import pagination
from core.models import (Vaccine, VaccineSchedule, VaccineAudit, ChildVaccinationContext,
    ChildRecord, CareReport, DoctorProfile, User, CareProfile, ChildPreferences,
    EmailNotification, VaccineReminderDelivery, now)
from core.schemas import parse
from core.vaccination_schemas import (VaccineInput, ScheduleInput, EligibilityInput,
    ReminderInput, AssignReview, MedicalReview, RetireInput, ChildContextInput)
from services.approvals import paginate


def display_age_group(dob, on_date):
    """Presentation bucket only; routine eligibility and dates remain unchanged."""
    for lower, upper, key in ((0,1,'0-1'),(1,3,'1-3'),(3,5,'3-5'),(5,10,'5-10'),(10,13,'10-13')):
        if age_date(dob, lower, 'years') <= on_date < age_date(dob, upper, 'years'):
            return key
    return 'other'


def today():
    from patient.child_routes import today as product_date
    return product_date()


def fingerprint(data):
    return hashlib.sha256(json.dumps(data,sort_keys=True,separators=(',',':')).encode()).hexdigest()


def log(action, vaccine=None, schedule=None, snapshot=None):
    db().add(VaccineAudit(vaccine_id=vaccine.id if vaccine else schedule.vaccine_id,
        schedule_id=schedule.id if schedule else None,actor_id=g.user.id,action=action,
        data=snapshot if snapshot is not None else dict(schedule.data) if schedule else dict(vaccine.data)))


def vaccine_row(identifier, lock=False):
    query=select(Vaccine).where(Vaccine.id==str(identifier))
    row=db().scalar(query.with_for_update() if lock else query)
    if not row:raise APIError(404,'vaccine_not_found','Vaccine not found')
    return row


def schedule_row(identifier, lock=False):
    query=select(VaccineSchedule).where(VaccineSchedule.id==str(identifier))
    row=db().scalar(query.with_for_update() if lock else query)
    if not row:raise APIError(404,'schedule_not_found','Schedule not found')
    return row


def vaccine_data(row):
    return dict(row.data,id=row.id,code=row.code,active=row.active)


def schedule_data(row, private=False):
    data=dict(row.data,id=row.id,status=row.status,published_at=row.published_at.isoformat()+'Z' if row.published_at else None)
    if private:data.update(reviewer_id=row.reviewer_id,created_by=row.created_by)
    return data


def qualified_reviewer(identifier):
    user=db().get(User,str(identifier));profile=db().get(DoctorProfile,str(identifier))
    if not user or user.role!='DOCTOR' or not user.email_verified or user.account_status!='ACTIVE' or user.approval_status!='APPROVED' or user.must_change_password or not profile or profile.verification_status!='APPROVED' or not profile.qualification or not profile.medical_registration_number:
        raise APIError(422,'reviewer_not_qualified','Choose an approved, verified registered doctor')
    return user,profile


def vaccines_admin():
    if request.method=='GET':
        page,size=pagination();rows,total=paginate(select(Vaccine).order_by(Vaccine.code),page,size)
        return jsonify(items=[vaccine_data(row) for row in rows],total=total,page=page,per_page=size)
    data=parse(VaccineInput).model_dump(mode='json');row=Vaccine(code=data['code'],active=data['active'],data=data)
    db().add(row);db().flush();log('vaccine_created',vaccine=row);db().commit()
    return jsonify(vaccine=vaccine_data(row)),201


def edit_vaccine(vaccine_id):
    row=vaccine_row(vaccine_id,True);data=parse(VaccineInput).model_dump(mode='json')
    if data['code']!=row.code:raise APIError(409,'immutable_code','Vaccine code cannot change; create a new catalog entry')
    log('vaccine_updated',vaccine=row);row.data=data;row.active=data['active'];db().commit()
    return jsonify(vaccine=vaccine_data(row))


def schedules_admin():
    if request.method=='GET':
        page,size=pagination();rows,total=paginate(select(VaccineSchedule).order_by(VaccineSchedule.created_at.desc(),VaccineSchedule.id),page,size)
        return jsonify(items=[schedule_data(row,True) for row in rows],total=total,page=page,per_page=size)
    data=parse(ScheduleInput).model_dump(mode='json');vaccine=vaccine_row(data['vaccine_id'])
    data['vaccine']=vaccine_data(vaccine)
    row=VaccineSchedule(vaccine_id=vaccine.id,schedule_type=data['schedule_type'],dose_code=data['dose_code'],version=data['version'],created_by=g.user.id,data=data)
    db().add(row);db().flush();log('schedule_created',schedule=row);db().commit()
    return jsonify(schedule=schedule_data(row,True)),201


def require_draft(row):
    if row.status!='DRAFT':raise APIError(409,'immutable_schedule','Only a draft can be edited. Published versions are immutable; create a new version.')


def edit_schedule(schedule_id):
    row=schedule_row(schedule_id,True);require_draft(row)
    data=parse(ScheduleInput).model_dump(mode='json');vaccine=vaccine_row(data['vaccine_id'])
    log('schedule_updated',schedule=row)
    data['vaccine']=vaccine_data(vaccine);row.data=data
    row.vaccine_id=vaccine.id;row.schedule_type=data['schedule_type'];row.dose_code=data['dose_code'];row.version=data['version']
    db().commit();return jsonify(schedule=schedule_data(row,True))


def edit_section(schedule_id, section):
    row=schedule_row(schedule_id,True);require_draft(row)
    value=parse(EligibilityInput if section=='eligibility' else ReminderInput).model_dump(mode='json')
    log(section+'_updated',schedule=row);data=dict(row.data);data[section]=value;row.data=data
    db().commit();return jsonify(schedule=schedule_data(row,True))


def reviewers():
    rows=db().execute(select(User,DoctorProfile).join(DoctorProfile,DoctorProfile.user_id==User.id).where(
        User.role=='DOCTOR',User.email_verified.is_(True),User.approval_status=='APPROVED',User.account_status=='ACTIVE',
        User.must_change_password.is_(False),DoctorProfile.verification_status=='APPROVED').order_by(User.full_name)).all()
    return jsonify(items=[dict(id=user.id,name=user.full_name,qualification=profile.qualification,
        registration=profile.medical_registration_number,council=profile.registering_council) for user,profile in rows])


def submit_review(schedule_id):
    row=schedule_row(schedule_id,True);require_draft(row)
    value=parse(AssignReview);reviewer,_=qualified_reviewer(value.reviewer_id)
    if reviewer.id==row.created_by:raise APIError(403,'independent_review','A separate qualified doctor must review the draft')
    data=dict(row.data);data['vaccine']=vaccine_data(vaccine_row(row.vaccine_id))
    row.data=data;row.reviewer_id=reviewer.id;row.reviewed_hash=None;row.reviewed_at=None;row.status='IN_REVIEW'
    log('review_requested',schedule=row);db().commit();return jsonify(schedule=schedule_data(row,True))


def withdraw(schedule_id):
    row=schedule_row(schedule_id,True)
    if row.status not in ('IN_REVIEW','APPROVED'):raise APIError(409,'invalid_state','Only an unpublished review can be withdrawn')
    row.status='DRAFT';row.reviewer_id=None;row.reviewed_hash=None;row.reviewed_at=None
    data=dict(row.data);data.pop('medical_review',None);row.data=data
    log('review_withdrawn',schedule=row);db().commit();return jsonify(schedule=schedule_data(row,True))


def review_queue():
    qualified_reviewer(g.user.id);page,size=pagination()
    rows,total=paginate(select(VaccineSchedule).where(VaccineSchedule.reviewer_id==g.user.id,
        VaccineSchedule.status=='IN_REVIEW').order_by(VaccineSchedule.created_at,VaccineSchedule.id),page,size)
    return jsonify(items=[schedule_data(row) for row in rows],total=total,page=page,per_page=size)


def medical_review(schedule_id):
    reviewer,profile=qualified_reviewer(g.user.id);row=schedule_row(schedule_id,True)
    if row.reviewer_id!=reviewer.id:raise APIError(403,'not_assigned','This review is assigned to another doctor')
    if row.status!='IN_REVIEW':raise APIError(409,'invalid_state','This draft is no longer awaiting review')
    value=parse(MedicalReview)
    if not value.attestation or not value.notes.strip():raise APIError(422,'attestation_required','Source verification and professional competency attestation are required')
    data=dict(row.data)
    data['medical_review']=dict(name=reviewer.full_name,qualification=profile.qualification,
        registration=profile.medical_registration_number,council=profile.registering_council,
        notes=value.notes,reviewed_at=now().isoformat()+'Z')
    row.data=data;row.reviewed_at=now()
    row.status='APPROVED' if value.decision=='APPROVE' else 'DRAFT'
    row.reviewed_hash=fingerprint(data) if value.decision=='APPROVE' else None
    log('medical_review_'+value.decision.lower(),schedule=row);db().commit()
    return jsonify(schedule=schedule_data(row))


def publish(schedule_id):
    row=schedule_row(schedule_id,True)
    if row.status!='APPROVED' or row.reviewed_hash!=fingerprint(row.data):raise APIError(409,'medical_review_required','An unchanged draft must be approved by its assigned qualified doctor before publication')
    qualified_reviewer(row.reviewer_id)
    if not vaccine_row(row.vaccine_id).active:raise APIError(409,'inactive_vaccine','Activate the vaccine before publishing')
    row.status='PUBLISHED';row.published_at=now();log('schedule_published',schedule=row);db().commit()
    return jsonify(schedule=schedule_data(row,True))


def retire(schedule_id):
    row=schedule_row(schedule_id,True);value=parse(RetireInput)
    if row.status!='PUBLISHED':raise APIError(409,'invalid_state','Only a published version can be retired')
    row.status='RETIRED';log('schedule_retired',schedule=row,snapshot={'reason':value.reason,'version':row.version});db().commit()
    return jsonify(schedule=schedule_data(row,True))


def audits():
    page,size=pagination();rows,total=paginate(select(VaccineAudit).order_by(VaccineAudit.created_at.desc(),VaccineAudit.id),page,size)
    return jsonify(items=[dict(id=row.id,action=row.action,schedule_id=row.schedule_id,vaccine_id=row.vaccine_id,
        created_at=row.created_at.isoformat()+'Z',snapshot=row.data) for row in rows],total=total,page=page,per_page=size)


def published(schedule_type='UIP', version_id=None):
    query=select(VaccineSchedule).join(Vaccine,Vaccine.id==VaccineSchedule.vaccine_id).where(Vaccine.active.is_(True),VaccineSchedule.status=='PUBLISHED',VaccineSchedule.schedule_type==schedule_type)
    if version_id:
        from uuid import UUID
        try:version_id=str(UUID(version_id))
        except (ValueError,TypeError):raise APIError(422,'invalid_version','Invalid schedule version')
        query=query.where(VaccineSchedule.id==version_id)
    rows=db().scalars(query.order_by(VaccineSchedule.published_at.desc(),VaccineSchedule.id)).all()
    chosen={}
    for row in rows:
        data=row.data
        if date.fromisoformat(data['effective_from'])>today() or data.get('effective_to') and date.fromisoformat(data['effective_to'])<today():continue
        key=(row.vaccine_id,row.dose_code)
        if key not in chosen or data['effective_from']>chosen[key].data['effective_from']:chosen[key]=row
    return list(chosen.values())


def public_catalog():
    seen={}
    for scheme in ('UIP','IAP'):
        for row in published(scheme):seen[row.vaccine_id]=row.data['vaccine']
    return jsonify(items=sorted(seen.values(),key=lambda item:item['code']),total=len(seen),status='AVAILABLE' if seen else 'NOT_AVAILABLE')


def public_schedules():
    from patient.child_routes import schedule_type
    rows=published(schedule_type(),request.args.get('schedule_version_id'))
    return jsonify(items=[schedule_data(row) for row in rows],total=len(rows),status='AVAILABLE' if rows else 'NOT_AVAILABLE')


def child_context(profile):
    row=db().get(ChildVaccinationContext,profile.id)
    return row.data if row else {}


def context_endpoint(child_id):
    from patient.child_routes import child
    profile=child(child_id,lock=request.method=='PUT')
    if request.method=='GET':return jsonify(context=child_context(profile))
    data=parse(ChildContextInput).model_dump(mode='json');row=db().get(ChildVaccinationContext,profile.id)
    if row:row.data=data
    else:db().add(ChildVaccinationContext(profile_id=profile.id,data=data))
    db().commit();return jsonify(context=data)


def age_date(dob,value,unit):
    if unit in ('days','weeks'):return dob+timedelta(days=value*(7 if unit=='weeks' else 1))
    months=value*(12 if unit=='years' else 1)+dob.month-1
    years,month=divmod(months,12);year=dob.year+years;month+=1
    return date(year,month,min(dob.day,monthrange(year,month)[1]))


def timeline(profile,scheme='UIP',version_id=None):
    context=child_context(profile);items=[]
    records=db().scalars(select(ChildRecord).where(ChildRecord.profile_id==profile.id,ChildRecord.kind=='vaccination',ChildRecord.deleted_at.is_(None))).all()
    complete=[row for row in records if row.data.get('status')=='Completed']
    for row in published(scheme,version_id):
        data=row.data;rule=data['eligibility'];start=age_date(profile.dob,data['age_start'],data['age_unit']);end=age_date(profile.dob,data['age_end'],data['age_unit'])
        from services.child_vaccination_plan import current_decision
        decision=current_decision(profile,row,context)
        status='UPCOMING' if today()<start else 'DUE' if today()<=end else 'OVERDUE'
        reasons=[]
        matching=[record for record in complete if record.data.get('vaccine_id')==row.vaccine_id and record.data.get('dose_code')==row.dose_code and record.data.get('schedule_type')==scheme]
        if not rule['active']:status='NOT_APPLICABLE';reasons.append('Eligibility rule is inactive')
        elif context.get('country')!=rule['country']:status='REVIEW_REQUIRED';reasons.append('Confirm the child’s country')
        elif rule['gender']!='All' and context.get('gender','Unknown')=='Unknown':status='REVIEW_REQUIRED';reasons.append('Applicable sex/gender has not been recorded')
        elif rule['gender']!='All' and context.get('gender')!=rule['gender']:status='NOT_APPLICABLE';reasons.append('Outside this rule’s stated eligibility')
        elif rule['states'] and not context.get('state'):status='REVIEW_REQUIRED';reasons.append('State is required for this rule')
        elif rule['states'] and context.get('state','').casefold() not in [value.casefold() for value in rule['states']]:status='NOT_APPLICABLE';reasons.append('Outside the published state rule')
        elif rule['districts'] and not context.get('district'):status='REVIEW_REQUIRED';reasons.append('District is required for this rule')
        elif rule['districts'] and context.get('district','').casefold() not in [value.casefold() for value in rule['districts']]:status='NOT_APPLICABLE';reasons.append('Outside the published district rule')
        elif rule['requires_clinical_review'] and not (decision and decision['decision']=='CONFIRM'):status='REVIEW_REQUIRED';reasons.append('This rule requires individual clinical assessment')
        elif context.get('history_status')!='PARENT_REPORTED':status='REVIEW_REQUIRED';reasons.append('Vaccination history is incomplete or unknown')
        elif data.get('previous_dose_code'):
            previous=[record for record in complete if record.data.get('vaccine_id')==row.vaccine_id and record.data.get('dose_code')==data['previous_dose_code'] and record.data.get('schedule_type')==scheme]
            if not previous:status='REVIEW_REQUIRED';reasons.append('Previous dose has no recorded administration date')
            elif max(date.fromisoformat(record.data['date']) for record in previous)+timedelta(days=data['minimum_interval_days'])>start:
                status='REVIEW_REQUIRED';reasons.append('Recorded dose interval needs doctor review; no catch-up date has been generated')
        if decision and decision['decision']=='NOT_APPLICABLE':
            status='NOT_APPLICABLE';reasons.append('Connected doctor recorded this dose as not applicable for this child')
        if matching:status='COMPLETED';reasons.append('Completion is parent-reported, not clinical verification; any eligibility concerns above still require review')
        elif status=='OVERDUE':reasons.append('Routine window has passed. Confirm missed-dose planning with your doctor; dates have not been shifted.')
        items.append(dict(id=row.id,vaccine_id=row.vaccine_id,vaccine=data['vaccine'],dose_code=row.dose_code,dose_name=data['dose_name'],version=row.version,schedule_type=scheme,
            recommended_date=start.isoformat(),window_end=end.isoformat(),status=status,reasons=reasons,
            age_group=display_age_group(profile.dob,start),age_label=data['age_label'],age_unit=data['age_unit'],age_start=data['age_start'],age_end=data['age_end'],
            age_relation='UPCOMING' if today()<start else 'CURRENT' if today()<=end else 'PAST',
            completed_date=max((record.data['date'] for record in matching),default=None),
            route=data['route'],injection_site=data['injection_site'],instructions=data['instructions'],
            source_url=data['source_url'],source_reference=data['source_reference'],medical_review=data.get('medical_review'),reminders=data['reminders']))
    for item in items:
        item['display_status']={'COMPLETED':'Completed','UPCOMING':'Upcoming','DUE':'Upcoming','OVERDUE':'Overdue','REVIEW_REQUIRED':'Doctor Review','NOT_APPLICABLE':'Not Applicable'}[item['status']]
        item['due_now']=item['status']=='DUE'
    counts={key:sum(item['status']==key for item in items) for key in ('COMPLETED','UPCOMING','DUE','OVERDUE','NOT_APPLICABLE','REVIEW_REQUIRED')}
    return dict(items=sorted(items,key=lambda item:(item['recommended_date'],item['dose_name'])),total=len(items),counts=counts,
        status='AVAILABLE' if items else 'NOT_AVAILABLE',schedule_type=scheme,context=context,
        message='Routine dates use published, medically reviewed versions. History is parent-reported. This is not a catch-up prescription.' if items else 'No reviewed schedule has been published for this schedule type.')


def child_vaccination_list(profile,scheme='UIP',version_id=None,view='all'):
    """Age-based display filters never change routine dates or clinical eligibility."""
    predicates={
        'all':lambda item:True,
        'current':lambda item:item['age_relation']=='CURRENT' and item['status'] not in ('COMPLETED','NOT_APPLICABLE'),
        'upcoming':lambda item:item['age_relation']=='UPCOMING' and item['status'] not in ('COMPLETED','NOT_APPLICABLE'),
        'completed':lambda item:item['status']=='COMPLETED',
        'overdue':lambda item:item['age_relation']=='PAST' and item['status'] not in ('COMPLETED','NOT_APPLICABLE'),
        'review_required':lambda item:item['status']=='REVIEW_REQUIRED',
        'not_applicable':lambda item:item['status']=='NOT_APPLICABLE',
    }
    if view not in predicates:raise APIError(422,'invalid_view','Choose current, upcoming, completed, overdue, review_required, not_applicable or all')
    state=timeline(profile,scheme,version_id)
    from patient.child_routes import child_age
    items=state['items']
    for item in items:item['views']=[key for key,predicate in predicates.items() if predicate(item)]
    state.update(child=dict(id=profile.id,name=profile.name,date_of_birth=profile.dob.isoformat(),age=child_age(profile)),
        as_of_date=today().isoformat(),view=view,total_published=len(items),
        view_counts={key:sum(predicate(item) for item in items) for key,predicate in predicates.items()},
        items=[item for item in items if predicates[view](item)])
    state['total']=len(state['items'])
    state['publication']=publication_readiness(scheme,len(items))
    return state


def publication_readiness(scheme,published_count):
    """Explain an empty clinical list without exposing draft medical content."""
    catalog_count=db().scalar(select(func.count()).select_from(Vaccine).where(Vaccine.active.is_(True)))
    statuses=dict(db().execute(select(VaccineSchedule.status,func.count()).join(Vaccine,Vaccine.id==VaccineSchedule.vaccine_id)
        .where(Vaccine.active.is_(True),VaccineSchedule.schedule_type==scheme).group_by(VaccineSchedule.status)).all())
    if published_count:
        state,message='PUBLISHED','Published vaccination schedules are available.'
    elif statuses.get('APPROVED'):
        state,message='PUBLICATION_PENDING','A reviewed vaccination plan is awaiting publication by the care team.'
    elif statuses.get('IN_REVIEW') or statuses.get('DRAFT'):
        state,message='REVIEW_PENDING','Your care team is preparing and reviewing the vaccination plan. Recommended doses will appear after publication.'
    elif statuses.get('PUBLISHED'):
        state,message='NO_EFFECTIVE_SCHEDULE','No published vaccination plan is currently effective for this programme. Please check with your care team.'
    else:
        state,message='SETUP_REQUIRED','Your care team has not published a vaccination plan yet. Vaccine names in the catalog do not set a child\'s dose or date.'
    return dict(state=state,catalog_count=catalog_count,message=message)


def validate_record(data,profile):
    if data.get('certificate_id'):
        report=db().scalar(select(CareReport).where(CareReport.id==data['certificate_id'],CareReport.profile_id==profile.id))
        if not report:raise APIError(422,'invalid_certificate','Certificate must be a report uploaded to this child’s profile')
    if data.get('schedule_id'):
        schedule=schedule_row(data['schedule_id'])
        if schedule.status not in ('PUBLISHED','RETIRED'):raise APIError(422,'unpublished_schedule','Select a published dose version')
        if data.get('vaccine_id')!=schedule.vaccine_id:raise APIError(422,'invalid_vaccine','Vaccine and dose do not match')
        data['dose_code']=schedule.dose_code;data['schedule_type']=schedule.schedule_type
    elif data.get('vaccine_id'):raise APIError(422,'dose_required','Select a published dose version or use the unlisted record form')


def scheduled_reminders(profile):
    prefs=db().get(ChildPreferences,profile.id)
    if prefs and not prefs.in_app:return []
    items=[]
    for scheme in ('UIP','IAP'):
        for item in timeline(profile,scheme)['items']:
            policy=item['reminders']
            if item['status'] not in ('UPCOMING','DUE','OVERDUE') or not policy['enabled'] or not policy['in_app']:continue
            start=date.fromisoformat(item['recommended_date']);end=date.fromisoformat(item['window_end']);offset=(start-today()).days
            if offset not in policy['before_days'] and not (policy['on_due'] and start<=today()<=end) and (today()-end).days not in policy['overdue_days']:continue
            message=(f'टीके की तारीख {offset} दिन में आने वाली है।' if offset>0 else 'टीका लगवाने का समय आ गया है।' if today()<=end else 'टीके की निर्धारित तारीख निकल चुकी है। डॉक्टर से बात करें।') if policy['language']=='hi' else (f'Vaccination is due in {offset} days.' if offset>0 else 'Vaccination is due now.' if today()<=end else 'Vaccination is overdue. Contact your doctor.')
            items.append(dict(id='schedule-'+item['id'],kind='vaccination',title=item['vaccine']['name_en']+' · '+item['dose_name'],date=item['recommended_date'],status=item['status'],display_status=item['display_status'],days_until_due=offset,message=message,source='PUBLISHED_SCHEDULE',delivery_status='IN_APP',schedule_id=item['id']))
    return items


def queue_reminder_emails():
    # Call from one or more workers; row locks + a unique delivery key deduplicate enqueue.
    profiles=db().scalars(select(CareProfile).join(ChildVaccinationContext,ChildVaccinationContext.profile_id==CareProfile.id).where(CareProfile.module=='child')).all()
    for profile in profiles:
        if not child_context(profile).get('email_reminders'):continue
        owner=db().get(User,profile.owner_id)
        if not owner or not owner.email_verified or owner.account_status!='ACTIVE' or owner.approval_status!='APPROVED':continue
        db().scalar(select(CareProfile).where(CareProfile.id==profile.id).with_for_update())
        for scheme in ('UIP','IAP'):
            for item in timeline(profile,scheme)['items']:
                policy=item['reminders']
                if not policy['enabled'] or not policy['email'] or item['status'] not in ('UPCOMING','DUE','OVERDUE'):continue
                start=date.fromisoformat(item['recommended_date']);end=date.fromisoformat(item['window_end'])
                if (start-today()).days not in policy['before_days'] and not (policy['on_due'] and start==today()) and (today()-end).days not in policy['overdue_days']:continue
                existing=db().scalar(select(VaccineReminderDelivery.id).where(VaccineReminderDelivery.profile_id==profile.id,VaccineReminderDelivery.schedule_id==item['id'],VaccineReminderDelivery.event_date==today(),VaccineReminderDelivery.channel=='email'))
                if existing:continue
                notification=EmailNotification(user_id=owner.id,template='vaccination_reminder_'+policy['language'],context_json='{}')
                db().add(notification);db().flush()
                db().add(VaccineReminderDelivery(profile_id=profile.id,schedule_id=item['id'],event_date=today(),channel='email',notification_id=notification.id))
        db().commit()


def reminder_still_valid(notification):
    delivery=db().scalar(select(VaccineReminderDelivery).where(VaccineReminderDelivery.notification_id==notification.id))
    if not delivery or delivery.event_date!=today():return False
    profile=db().get(CareProfile,delivery.profile_id)
    if not profile or not child_context(profile).get('email_reminders'):return False
    owner=db().get(User,profile.owner_id)
    if not owner or not owner.email_verified or owner.account_status!='ACTIVE' or owner.approval_status!='APPROVED':return False
    schedule=db().get(VaccineSchedule,delivery.schedule_id)
    if not schedule:return False
    for item in timeline(profile,schedule.schedule_type)['items']:
        if item['id']!=schedule.id:continue
        policy=item['reminders']
        if not policy['enabled'] or not policy['email'] or item['status'] not in ('UPCOMING','DUE','OVERDUE'):return False
        start=date.fromisoformat(item['recommended_date']);end=date.fromisoformat(item['window_end'])
        return (start-today()).days in policy['before_days'] or policy['on_due'] and start==today() or (today()-end).days in policy['overdue_days']
    return False
