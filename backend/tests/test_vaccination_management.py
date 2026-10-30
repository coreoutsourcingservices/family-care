from datetime import date
from sqlalchemy import select
from conftest import create_account
from test_workflows import PASSWORD, bearer
from test_care import patient, create_profile, cloud
from test_referrals import doctor
from core.database import db
from core.models import DoctorProfile, VaccineSchedule, EmailNotification, VaccineReminderDelivery, CareProfile
from services.vaccination import age_date


def setup_staff(app, client):
    create_account(app,'ADMIN','admin@example.com')
    admin=bearer(client.post('/api/v1/admin/login',json={'email':'admin@example.com','password':PASSWORD}))
    doctor_id,_=doctor(app)
    with app.app_context():
        db().get(DoctorProfile,doctor_id).verification_status='APPROVED';db().commit()
    reviewer=bearer(client.post('/api/v1/doctors/login',json={'email':'rahul@example.com','password':PASSWORD}))
    return admin,reviewer,doctor_id


def draft(client,admin,**extra):
    vaccine=client.post('/api/v1/admin/vaccination/vaccines',headers=admin,json=dict(code='TEST',name_en='Synthetic vaccine',category='Government',protects_against='Test only'))
    assert vaccine.status_code==201,vaccine.json
    payload=dict(vaccine_id=vaccine.json['vaccine']['id'],schedule_type='UIP',dose_code='D1',dose_name='Synthetic dose',version='test-v1',age_label='Test age',age_unit='years',age_start=8,age_end=9,route='IM',source_url='https://example.org/test-guideline',source_reference='Synthetic testing only',effective_from='2020-01-01',eligibility={'requires_clinical_review':False},reminders={'email':True})
    payload.update(extra)
    result=client.post('/api/v1/admin/vaccination/schedules',headers=admin,json=payload)
    assert result.status_code==201,result.json
    return result.json['schedule'],payload


def approve(client,admin,reviewer,doctor_id,schedule):
    path='/api/v1/admin/vaccination/schedules/'+schedule['id']
    assert client.post(path+'/submit-review',headers=admin,json={'reviewer_id':doctor_id}).status_code==200
    result=client.post('/api/v1/doctors/vaccination-reviews/'+schedule['id'],headers=reviewer,json={'decision':'APPROVE','notes':'Synthetic source reviewed for testing only.','attestation':True})
    assert result.status_code==200,result.json
    result=client.post(path+'/publish',headers=admin,json={})
    assert result.status_code==200,result.json
    return path


def test_independent_review_publication_and_immutable_versions(app,client):
    admin,reviewer,doctor_id=setup_staff(app,client)
    row,payload=draft(client,admin)
    path='/api/v1/admin/vaccination/schedules/'+row['id']
    assert client.get('/api/v1/vaccines').json['total']==0
    assert client.post(path+'/publish',headers=admin,json={}).status_code==409
    assert client.post('/api/v1/doctors/vaccination-reviews/'+row['id'],headers=reviewer,json={'decision':'APPROVE','notes':'Synthetic review without assignment','attestation':True}).status_code==403
    assert client.post(path+'/submit-review',headers=admin,json={'reviewer_id':doctor_id}).status_code==200
    assert client.put(path,headers=admin,json=payload).status_code==409
    assert client.post('/api/v1/doctors/vaccination-reviews/'+row['id'],headers=reviewer,json={'decision':'APPROVE','notes':'Synthetic source reviewed for testing','attestation':False}).status_code==422
    assert client.post('/api/v1/doctors/vaccination-reviews/'+row['id'],headers=reviewer,json={'decision':'APPROVE','notes':'Synthetic source reviewed for testing','attestation':True}).status_code==200
    with app.app_context():
        changed=db().get(VaccineSchedule,row['id']);changed.data={**changed.data,'instructions':'Tampered after approval'};db().commit()
    assert client.post(path+'/publish',headers=admin,json={}).status_code==409
    assert client.post(path+'/withdraw',headers=admin,json={}).status_code==200
    assert client.put(path,headers=admin,json=payload).status_code==200
    approve(client,admin,reviewer,doctor_id,row)
    assert client.get('/api/v1/vaccines').json['total']==1
    assert client.get('/api/v1/vaccination-schedules?schedule_type=IAP').json['total']==0
    assert client.put(path+'/eligibility',headers=admin,json={'gender':'Girls'}).status_code==409
    assert client.put(path,headers=admin,json=payload).status_code==409
    assert client.post(path+'/withdraw',headers=admin,json={}).status_code==409
    assert client.get('/api/v1/admin/vaccination/audit',headers=admin).json['total']>=6
    assert client.post(path+'/retire',headers=admin,json={'reason':'Synthetic version retired'}).status_code==200
    assert client.get('/api/v1/vaccines').json['total']==0
    assert client.get('/api/v1/vaccination-schedules/'+row['id']).status_code==200


def test_eligibility_history_and_private_records(app,client,monkeypatch):
    monkeypatch.setattr('services.vaccination.today',lambda:date(2026,10,28))
    admin,reviewer,doctor_id=setup_staff(app,client)
    row,_=draft(client,admin,eligibility={'gender':'Girls','states':['Bihar'],'districts':['Patna'],'requires_clinical_review':False})
    approve(client,admin,reviewer,doctor_id,row)
    owner=patient(app,client);child=create_profile(client,owner);base='/api/v1/children/'+child
    assert client.get(base+'/vaccinations',headers=owner).json['items'][0]['status']=='REVIEW_REQUIRED'
    context=dict(country='IN',state='Bihar',district='Patna',gender='Boys',history_status='PARENT_REPORTED',email_reminders=False)
    assert client.put(base+'/vaccination-context',headers=owner,json=context).status_code==200
    assert client.get(base+'/vaccinations',headers=owner).json['items'][0]['status']=='NOT_APPLICABLE'
    context['gender']='Girls';client.put(base+'/vaccination-context',headers=owner,json=context)
    assert client.get(base+'/vaccinations',headers=owner).json['items'][0]['status']=='DUE'
    record=dict(title='Parent vaccination card',date='2026-10-01',status='Completed',vaccine_id=row['vaccine_id'],schedule_id=row['id'])
    result=client.post(base+'/vaccinations/history',headers=owner,json=record)
    assert result.status_code==201,result.json
    assert result.json['record']['dose_code']=='D1'
    assert client.get(base+'/vaccinations',headers=owner).json['items'][0]['status']=='COMPLETED'
    assert client.get(base+'/records',headers=admin).status_code==403
    assert client.get('/api/v1/admin/vaccination/vaccines',headers=owner).status_code==403
    other=patient(app,client,'stranger@example.com')
    assert client.get(base+'/vaccination-context',headers=other).status_code==404
    assert client.post(base+'/vaccinations/history',headers=owner,json={**record,'certificate_id':'bad-id'}).status_code==422
    assert client.post(base+'/vaccinations/history',headers=owner,json={**record,'certificate_id':row['id']}).status_code==422


def test_reminders_deduplicate_and_cancel_after_optout(app,client,monkeypatch):
    monkeypatch.setattr('services.vaccination.today',lambda:date(2026,10,28))
    admin,reviewer,doctor_id=setup_staff(app,client)
    row,_=draft(client,admin,age_unit='days',age_start=0,age_end=0)
    approve(client,admin,reviewer,doctor_id,row)
    owner=patient(app,client);child=create_profile(client,owner,date_of_birth='2026-10-28');base='/api/v1/children/'+child
    context=dict(country='IN',history_status='PARENT_REPORTED',email_reminders=True)
    client.put(base+'/vaccination-context',headers=owner,json=context)
    assert client.get(base+'/reminders',headers=owner).json['total']==1
    with app.app_context():
        from services.vaccination import queue_reminder_emails
        queue_reminder_emails();queue_reminder_emails()
        assert len(db().scalars(select(VaccineReminderDelivery)).all())==1
        notification=db().scalar(select(EmailNotification).where(EmailNotification.template.like('vaccination_reminder_%')))
        notification_id=notification.id
    client.put(base+'/vaccination-context',headers=owner,json={**context,'email_reminders':False})
    with app.app_context():
        from services.email import process_one
        assert process_one() is True
        assert db().get(EmailNotification,notification_id).status=='CANCELLED'


def test_calendar_and_missing_previous_dose(app,client,monkeypatch):
    assert age_date(date(2024,1,31),1,'months')==date(2024,2,29)
    assert age_date(date(2024,2,29),1,'years')==date(2025,2,28)
    monkeypatch.setattr('services.vaccination.today',lambda:date(2026,10,28))
    admin,reviewer,doctor_id=setup_staff(app,client)
    row,_=draft(client,admin,previous_dose_code='D0',minimum_interval_days=28)
    approve(client,admin,reviewer,doctor_id,row)
    owner=patient(app,client);child=create_profile(client,owner);base='/api/v1/children/'+child
    client.put(base+'/vaccination-context',headers=owner,json={'country':'IN','history_status':'PARENT_REPORTED'})
    item=client.get(base+'/vaccinations',headers=owner).json['items'][0]
    assert item['status']=='REVIEW_REQUIRED'
    assert item['recommended_date']=='2026-05-14'
    assert 'Previous dose' in item['reasons'][0]


def test_versions_unqualified_reviewers_and_due_states(app,client,monkeypatch):
    monkeypatch.setattr('services.vaccination.today',lambda:date(2026,10,28))
    admin,reviewer,doctor_id=setup_staff(app,client)
    row,payload=draft(client,admin)
    with app.app_context():
        db().get(DoctorProfile,doctor_id).verification_status='PENDING';db().commit()
    path='/api/v1/admin/vaccination/schedules/'+row['id']
    assert client.post(path+'/submit-review',headers=admin,json={'reviewer_id':doctor_id}).status_code==422
    with app.app_context():
        db().get(DoctorProfile,doctor_id).verification_status='APPROVED';db().commit()
    approve(client,admin,reviewer,doctor_id,row)
    newer=client.post('/api/v1/admin/vaccination/schedules',headers=admin,json={**payload,'version':'test-v2','effective_from':'2026-01-01','age_start':9,'age_end':10}).json['schedule']
    approve(client,admin,reviewer,doctor_id,newer)
    schedules=client.get('/api/v1/vaccination-schedules').json['items']
    assert len(schedules)==1 and schedules[0]['id']==newer['id']
    assert client.get('/api/v1/vaccination-schedules?schedule_version_id='+row['id']).json['items'][0]['id']==row['id']
    assert client.get('/api/v1/vaccination-schedules?schedule_version_id=invalid').status_code==422
    owner=patient(app,client);child=create_profile(client,owner);base='/api/v1/children/'+child
    client.put(base+'/vaccination-context',headers=owner,json={'country':'IN','history_status':'PARENT_REPORTED'})
    assert client.get(base+'/vaccinations',headers=owner).json['items'][0]['status']=='UPCOMING'
    monkeypatch.setattr('services.vaccination.today',lambda:date(2030,10,28))
    result=client.get(base+'/vaccinations',headers=owner).json['items'][0]
    assert result['status']=='OVERDUE' and result['recommended_date']=='2027-05-14'
    assert 'not been shifted' in result['reasons'][0]


def test_review_rejection_invalid_rules_and_cross_child_certificate(app,client,cloud):
    from test_care import upload
    admin,reviewer,doctor_id=setup_staff(app,client)
    row,payload=draft(client,admin)
    assert client.post('/api/v1/admin/vaccination/schedules',headers=admin,json={**payload,'version':'bad','age_end':1}).status_code==422
    assert client.put('/api/v1/admin/vaccination/schedules/'+row['id']+'/eligibility',headers=admin,json={'districts':['Patna']}).status_code==422
    assert client.put('/api/v1/admin/vaccination/schedules/'+row['id']+'/reminders',headers=admin,json={'before_days':[-1]}).status_code==422
    path='/api/v1/admin/vaccination/schedules/'+row['id']
    client.post(path+'/submit-review',headers=admin,json={'reviewer_id':doctor_id})
    result=client.post('/api/v1/doctors/vaccination-reviews/'+row['id'],headers=reviewer,json={'decision':'REJECT','notes':'Synthetic source needs further verification.','attestation':True})
    assert result.json['schedule']['status']=='DRAFT'
    assert client.post(path+'/publish',headers=admin,json={}).status_code==409
    owner=patient(app,client);child=create_profile(client,owner);other=create_profile(client,owner)
    report=upload(client,owner,other).json['report']['id']
    result=client.post('/api/v1/children/'+child+'/vaccinations/history',headers=owner,json={'title':'Unlisted historical dose','date':'2026-10-01','status':'Completed','certificate_id':report})
    assert result.status_code==422
    own_report=upload(client,owner,child).json['report']['id']
    result=client.post('/api/v1/children/'+child+'/vaccinations/history',headers=owner,json={'title':'Unlisted historical dose','date':'2026-10-01','status':'Completed','certificate_id':own_report})
    assert result.status_code==201,result.json


def test_child_list_filters_by_age_and_only_published_doses(app,client,monkeypatch):
    monkeypatch.setattr('services.vaccination.today',lambda:date(2026,10,28))
    monkeypatch.setattr('patient.child_routes.today',lambda:date(2026,10,28))
    admin,reviewer,doctor_id=setup_staff(app,client)
    birth,payload=draft(client,admin,age_unit='days',age_start=0,age_end=1,age_label='Synthetic birth window')
    approve(client,admin,reviewer,doctor_id,birth)
    future=client.post('/api/v1/admin/vaccination/schedules',headers=admin,json={**payload,'dose_code':'LATER','dose_name':'Later synthetic dose','age_unit':'years','age_start':6,'age_end':7,'age_label':'Synthetic later window'}).json['schedule']
    approve(client,admin,reviewer,doctor_id,future)
    hidden=client.post('/api/v1/admin/vaccination/schedules',headers=admin,json={**payload,'dose_code':'HIDDEN','dose_name':'Unpublished dose','child_visible':False}).json['schedule']
    # An approved draft is still invisible until publication.
    client.post('/api/v1/admin/vaccination/schedules/'+hidden['id']+'/submit-review',headers=admin,json={'reviewer_id':doctor_id})
    client.post('/api/v1/doctors/vaccination-reviews/'+hidden['id'],headers=reviewer,json={'decision':'APPROVE','notes':'Synthetic test review, not a clinical recommendation.','attestation':True})
    owner=patient(app,client);baby=create_profile(client,owner,date_of_birth='2026-10-28');older=create_profile(client,owner,date_of_birth='2020-03-01')
    base='/api/v1/children/'+baby+'/vaccinations'
    current=client.get(base+'?view=current',headers=owner)
    assert current.status_code==200,current.json
    state=current.json
    assert state['total']==1 and state['total_published']==2
    assert state['items'][0]['id']==birth['id']
    assert state['items'][0]['status']=='REVIEW_REQUIRED'
    assert state['items'][0]['age_relation']=='CURRENT'
    assert state['items'][0]['age_label']=='Synthetic birth window'
    assert state['child']['id']==baby and state['child']['age']['total_days']==0
    assert state['as_of_date']=='2026-10-28' and state['view_counts']['upcoming']==1
    assert client.get(base+'?view=upcoming',headers=owner).json['items'][0]['id']==future['id']
    assert client.get(base+'?view=all',headers=owner).json['total']==2
    assert client.get(base+'?view=invalid',headers=owner).status_code==422
    older_state=client.get('/api/v1/children/'+older+'/vaccinations?view=current',headers=owner).json
    assert [item['id'] for item in older_state['items']]==[future['id']]
    assert older_state['view_counts']['overdue']==1
    client.put('/api/v1/children/'+baby+'/vaccination-context',headers=owner,json={'country':'IN','history_status':'PARENT_REPORTED'})
    record=client.post('/api/v1/children/'+baby+'/vaccinations/history',headers=owner,json={'title':'Reported completed dose','date':'2026-10-28','status':'Completed','vaccine_id':birth['vaccine_id'],'schedule_id':birth['id']})
    assert record.status_code==201,record.json
    assert client.get(base+'?view=current',headers=owner).json['total']==0
    done=client.get(base+'?view=completed',headers=owner).json['items'][0]
    assert done['completed_date']=='2026-10-28' and done['views']==['all','completed']
    stranger=patient(app,client,'unrelated@example.com')
    assert client.get(base+'?view=current',headers=stranger).status_code==404


def test_unpublished_plan_explains_setup_review_and_publication(app,client):
    owner=patient(app,client);child=create_profile(client,owner)
    url='/api/v1/children/'+child+'/vaccinations?view=all'
    initial=client.get(url,headers=owner).json
    assert initial['publication']['state']=='SETUP_REQUIRED'
    assert initial['publication']['catalog_count']==0 and initial['items']==[]
    admin,reviewer,doctor_id=setup_staff(app,client)
    row,_=draft(client,admin,child_visible=False)
    pending=client.get(url,headers=owner).json
    assert pending['publication']['state']=='REVIEW_PENDING'
    assert pending['publication']['catalog_count']==1 and pending['items']==[]
    assert 'Synthetic vaccine' not in str(pending)
    path='/api/v1/admin/vaccination/schedules/'+row['id']
    client.post(path+'/submit-review',headers=admin,json={'reviewer_id':doctor_id})
    assert client.get(url,headers=owner).json['publication']['state']=='REVIEW_PENDING'
    client.post('/api/v1/doctors/vaccination-reviews/'+row['id'],headers=reviewer,json={'decision':'APPROVE','notes':'Synthetic source checked for testing only.','attestation':True})
    approved=client.get(url,headers=owner).json
    assert approved['publication']['state']=='PUBLICATION_PENDING' and approved['items']==[]
    assert client.post(path+'/publish',headers=admin,json={}).status_code==200
    assert client.get(url,headers=owner).json['publication']['state']=='PUBLISHED'
