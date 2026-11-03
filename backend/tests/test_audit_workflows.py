from datetime import timedelta
from uuid import uuid4
from sqlalchemy import select
from core.database import db
from core.models import CareProfile,DoctorConsultation,DoctorPrescription,now
from test_care import patient,create_profile
from test_referrals import doctor
from test_workflows import bearer,PASSWORD

def clinician(app,client):
    identifier,referral=doctor(app)
    headers=bearer(client.post('/api/v1/doctors/login',json={'email':'rahul@example.com','password':PASSWORD}))
    return identifier,referral,headers

def test_prescription_draft_issue_immutable_void_and_owner_access(app,client):
    owner=patient(app,client);doctor_id,referral,headers=clinician(app,client)
    profile=create_profile(client,owner,referral_id=referral)
    path=f'/api/v1/doctors/care-profiles/{profile}/prescriptions'
    value={'medicines':[{'name':'Synthetic test medicine','strength':'Test strength','dose':'Test dose','frequency':'Test frequency','duration':'Test duration'}],'instructions':'Synthetic workflow only'}
    response=client.post(path,headers=headers,json=value)
    assert response.status_code==200,response.json
    row=response.json['prescription']
    patient_path=f'/api/v1/patients/profiles/{profile}/prescriptions'
    assert client.get(patient_path,headers=owner).json['items']==[]
    assert client.post(path+'/'+row['id']+'/decision',headers=headers,json={'action':'ISSUE','version':row['version'],'attestation':False}).status_code==422
    issued=client.post(path+'/'+row['id']+'/decision',headers=headers,json={'action':'ISSUE','version':row['version'],'attestation':True})
    assert issued.status_code==200,issued.json
    assert issued.json['prescription']['data']['issuer']['registration']
    assert client.put(path+'/'+row['id'],headers=headers,json={**value,'version':issued.json['prescription']['version']}).status_code==409
    assert len(client.get(patient_path,headers=owner).json['items'])==1
    outsider=patient(app,client,'outsider@example.com')
    assert client.get(patient_path,headers=outsider).status_code==404
    assert client.post(path+'/'+row['id']+'/decision',headers=headers,json={'action':'VOID','version':issued.json['prescription']['version'],'attestation':True,'reason':'Synthetic correction'}).status_code==200
    assert client.get(patient_path,headers=owner).json['items'][0]['status']=='VOID'
    with app.app_context():assert db().get(DoctorPrescription,row['id']).void_reason=='Synthetic correction'

def test_confirmed_appointments_conflicts_reschedule_and_slots(app,client):
    owner=patient(app,client);doctor_id,referral,headers=clinician(app,client)
    profile=create_profile(client,owner,module='adult',kind='self',date_of_birth='1990-01-01')
    start=now()+timedelta(days=2)
    slot=client.post('/api/v1/doctors/appointment-slots',headers=headers,json={'starts_at':start.isoformat()+'Z','duration_minutes':30})
    assert slot.status_code==201,slot.json
    assert client.post('/api/v1/doctors/appointment-slots',headers=headers,json={'starts_at':(start+timedelta(minutes=10)).isoformat()+'Z'}).status_code==409
    assert len(client.get(f'/api/v1/patients/doctor-directory/{doctor_id}/slots',headers=owner).json['items'])==1
    path=f'/api/v1/patients/profiles/{profile}/consultations'
    first=client.post(path,headers=owner,json={'doctor_id':doctor_id,'concern':'Test visit','requested_at':start.isoformat()+'Z'}).json['consultation']
    second=client.post(path,headers=owner,json={'doctor_id':doctor_id,'concern':'Second visit','requested_at':(start+timedelta(minutes=10)).isoformat()+'Z'}).json['consultation']
    endpoint='/api/v1/doctors/consultation-visits/'
    confirmed=client.patch(endpoint+first['id']+'/status',headers=headers,json={'status':'CONFIRMED','confirmed_at':start.isoformat()+'Z','version':first['version']})
    assert confirmed.status_code==200,confirmed.json
    assert confirmed.json['consultation']['confirmed_at']
    assert client.patch(endpoint+second['id']+'/status',headers=headers,json={'status':'CONFIRMED'}).status_code==409
    assert client.delete('/api/v1/doctors/appointment-slots/'+slot.json['slot']['id'],headers=headers).status_code==409
    assert client.patch(endpoint+first['id']+'/status',headers=headers,json={'status':'COMPLETED'}).status_code==409
    latest=confirmed.json['consultation']['version']
    assert client.patch(endpoint+first['id']+'/status',headers=headers,json={'status':'CONFIRMED','confirmed_at':(start+timedelta(hours=2)).isoformat()+'Z','version':latest}).status_code==200
    assert client.patch(endpoint+first['id']+'/status',headers=headers,json={'status':'CANCELLED','version':latest}).status_code==409

def test_adult_structured_fields_units_versions_and_validation(app,client):
    owner=patient(app,client);profile=create_profile(client,owner,module='adult',kind='self',date_of_birth='1990-01-01')
    path=f'/api/v1/patients/adults/{profile}/records'
    payload={'kind':'glucose','title':'Synthetic reading','date':'2026-01-01','glucose':5.5,'units':'mmol/L','reading_context':'Fasting','measurement_time':'08:30'}
    first=client.post(path,headers=owner,json=payload)
    assert first.status_code==201,first.json
    row=first.json['record'];assert row['units']=='mmol/L'
    assert client.patch(path+'/'+row['id'],headers=owner,json={**payload,'version':'outdated'}).status_code==409
    assert client.post(path,headers=owner,json={**payload,'units':'unknown'}).status_code==422
    assert client.post(path,headers=owner,json={**payload,'measurement_time':'29:00'}).status_code==422
    assert client.post(path,headers=owner,json={'kind':'bp','title':'Invalid','date':'2026-01-01','systolic':80,'diastolic':120}).status_code==422

def test_women_period_overlap_dates_and_structured_screening(app,client):
    owner=patient(app,client);profile=create_profile(client,owner,module='women',kind='self',date_of_birth='1990-01-01')
    path=f'/api/v1/women/profiles/{profile}/diary/'
    first={'section':'cycle','data':{'title':'Period','date':'2026-09-01','end':'2026-09-05'},'version':0}
    assert client.put(path+str(uuid4()),headers=owner,json=first).status_code==200
    overlapping={**first,'data':{**first['data'],'date':'2026-09-03'}}
    assert client.put(path+str(uuid4()),headers=owner,json=overlapping).status_code==409
    assert client.put(path+str(uuid4()),headers=owner,json={'section':'symptoms','data':{'title':'Test','date':'2026-09-01','pain_score':'11'}}).status_code==422
    assert client.put(path+str(uuid4()),headers=owner,json={'section':'screening','data':{'title':'Follow-up','date':'2026-09-01','status':'Result received','next':'2026-12-01'}}).status_code==200

def test_private_reminders_deliver_once_and_report_actual_inbox_state(app,client):
    from core.models import AppNotification
    from patient.child_routes import today
    owner=patient(app,client);profile=create_profile(client,owner,module='women',kind='self',date_of_birth='1990-01-01')
    identifier=str(uuid4());base=f'/api/v1/women/profiles/{profile}'
    assert client.put(base+'/diary/'+identifier,headers=owner,json={'section':'reminder','data':{'title':'Private medical task','date':today().isoformat(),'status':'Planned'}}).status_code==200
    before=client.get(base+'/workspace',headers=owner).json['records']
    assert next(r for r in before if r['id']==identifier)['delivery_status']=='SAVED_ONLY'
    for _ in range(2):assert client.get('/api/v1/notifications/unread-count',headers=owner).status_code==200
    after=client.get(base+'/workspace',headers=owner).json['records']
    assert next(r for r in after if r['id']==identifier)['delivery_status']=='AVAILABLE_IN_APP'
    with app.app_context():
        reminders=db().scalars(select(AppNotification).where(AppNotification.kind=='personal_reminder')).all()
        assert len(reminders)==1
        assert 'Private medical task' not in reminders[0].body
    outsider=patient(app,client,'reminder-outsider@example.com')
    assert not any(r['type']=='personal_reminder' for r in client.get('/api/v1/notifications',headers=outsider).json['items'])

def test_women_prescription_edit_scope_and_expiry_are_enforced(app,client):
    from core.models import WomenAccessGrant
    owner=patient(app,client);doctor_id,referral,headers=clinician(app,client)
    profile=create_profile(client,owner,module='women',kind='self',date_of_birth='1990-01-01')
    assert client.post(f'/api/v1/patients/profiles/{profile}/connect-doctor',headers=owner,json={'referral_id':referral}).status_code==200
    grant_path=f'/api/v1/women/profiles/{profile}/sharing'
    value={'recipient_id':doctor_id,'permissions':{'records':'view'},'expires_at':(now()+timedelta(days=1)).isoformat()+'Z'}
    response=client.put(grant_path,headers=owner,json=value)
    assert response.status_code==200,response.json
    path=f'/api/v1/doctors/care-profiles/{profile}/prescriptions'
    draft={'medicines':[{'name':'Synthetic medicine','strength':'Test','dose':'Test','frequency':'Test','duration':'Test'}]}
    assert client.get(path,headers=headers).status_code==200
    assert client.post(path,headers=headers,json=draft).status_code==403
    response=client.put(grant_path,headers=owner,json={**value,'permissions':{'records':'edit'}})
    assert client.post(path,headers=headers,json=draft).status_code==200
    with app.app_context():
        db().get(WomenAccessGrant,response.json['grant']['id']).expires_at=now()-timedelta(seconds=1);db().commit()
    assert client.get(path,headers=headers).status_code==403

def test_linked_completed_vaccine_cannot_be_duplicated_by_new_schedule_version(app,client):
    from test_vaccination_management import setup_staff,draft,approve
    from core.models import ChildRecord,VaccineSchedule
    admin,reviewer,doctor_id=setup_staff(app,client)
    schedule,payload=draft(client,admin)
    approve(client,admin,reviewer,doctor_id,schedule)
    owner=patient(app,client);profile=create_profile(client,owner)
    path=f'/api/v1/children/{profile}/vaccinations/history'
    record={'title':'Synthetic dose','date':'2026-01-01','status':'Completed','schedule_id':schedule['id']}
    first=client.post(path,headers=owner,json=record)
    assert first.status_code==201,first.json
    assert first.json['record']['vaccine_id']==schedule['vaccine_id']
    assert client.post(path,headers=owner,json=record).status_code==409
    response=client.post('/api/v1/admin/vaccination/schedules',headers=admin,json={**payload,'version':'test-v2'})
    assert response.status_code==201,response.json
    replacement=response.json['schedule'];approve(client,admin,reviewer,doctor_id,replacement);new_id=replacement['id']
    assert client.post(path,headers=owner,json={**record,'schedule_id':new_id}).status_code==409
