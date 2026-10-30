from datetime import date
from core.database import db
from core.models import AdultRecordRevision
from sqlalchemy import select
from test_care import patient, create_profile
from test_referrals import doctor
from test_workflows import bearer, PASSWORD

def test_adult_records_persist_edit_delete_and_ownership(app,client):
    headers=patient(app,client)
    profile=create_profile(client,headers,module='adult',date_of_birth='1985-01-01')
    url=f'/api/v1/patients/adults/{profile}/records'
    assert client.get(url,headers=headers).json['items']==[]
    payload=dict(kind='bp',title='Morning reading',date='2026-01-01',systolic=120,diastolic=80)
    result=client.post(url,headers=headers,json=payload)
    assert result.status_code==201,result.json
    record=result.json['record']['id']
    assert client.get(url,headers=headers).json['items'][0]['systolic']==120
    second=patient(app,client,'another@example.com')
    assert client.get(url,headers=second).status_code==404
    assert client.post(url+'/'+record,headers=second,json=payload).status_code==404
    assert client.post(url+'/'+record+'/delete',headers=second).status_code==404
    payload['systolic']=125
    assert client.post(url+'/'+record,headers=headers,json=payload).status_code==200
    assert client.get(url,headers=headers).json['items'][0]['systolic']==125
    assert client.post(url+'/'+record+'/delete',headers=headers).status_code==200
    assert client.get(url,headers=headers).json['items']==[]
    with app.app_context():
        assert len(db().scalars(select(AdultRecordRevision)).all())==3

def test_adult_validation_module_and_doctor_access(app,client):
    headers=patient(app,client)
    profile=create_profile(client,headers,module='adult',date_of_birth='1985-01-01')
    url=f'/api/v1/patients/adults/{profile}/records'
    for extra in ({'systolic':-1,'diastolic':80},{'systolic':120},{'systolic':120,'diastolic':80,'date':'2099-01-01'},{'systolic':120,'diastolic':80,'date':'1980-01-01'}):
        payload=dict(kind='bp',title='Reading',date='2026-01-01')
        payload.update(extra)
        assert client.post(url,headers=headers,json=payload).status_code==422
    for kind,extra in [('glucose',{'glucose':95}),('lipids',{'total':180,'hdl':55}),('medicine',{'context':'Existing prescription'}),('lifestyle',{'minutes':30}),('screening',{}),('history',{}),('reminder',{})]:
        result=client.post(url,headers=headers,json=dict(kind=kind,title='Test '+kind,date='2026-01-01',**extra))
        assert result.status_code==201,result.json
    assert client.post(url,headers=headers,json=dict(kind='consultation_request',title='Review',date='2026-01-01')).status_code==409
    child=create_profile(client,headers,date_of_birth=date.today().replace(year=date.today().year-5).isoformat(),guardian_contact='+919876543210')
    assert client.get(f'/api/v1/patients/adults/{child}/records',headers=headers).status_code==404
    doctor_id,referral=doctor(app)
    doctor_headers=bearer(client.post('/api/v1/doctors/login',json={'email':'rahul@example.com','password':PASSWORD}))
    shared=f'/api/v1/doctors/care-profiles/{profile}/records'
    assert client.get(shared,headers=doctor_headers).status_code==404
    assert client.post(f'/api/v1/patients/profiles/{profile}/connect-doctor',headers=headers,json={'referral_id':referral}).status_code==200
    result=client.post(url,headers=headers,json=dict(kind='consultation_request',title='Review adult BP',date='2026-01-01'))
    assert result.status_code==201,result.json
    shared_records=client.get(shared,headers=doctor_headers)
    assert shared_records.status_code==200 and shared_records.json['total']==8
    requests=client.get('/api/v1/doctors/consultation-requests',headers=doctor_headers)
    assert requests.status_code==200 and requests.json['items'][0]['title']=='Review adult BP'
    assert client.post(url,headers=doctor_headers,json=dict(kind='history',title='No',date='2026-01-01')).status_code==403

def test_aged_child_keeps_same_id_and_history(app,client):
    from core.models import ChildRecord
    headers=patient(app,client)
    _,referral=doctor(app)
    profile=create_profile(client,headers,date_of_birth='2000-01-01',guardian_contact='+919876543210',referral_id=referral)
    with app.app_context():
        db().add(ChildRecord(profile_id=profile,kind='history',data={'title':'Original history','date':'2010-01-01'}))
        db().commit()
    url=f'/api/v1/patients/adults/{profile}/records'
    assert client.post(url,headers=headers,json=dict(kind='bp',title='Adult reading',date='2026-01-01',systolic=120,diastolic=80)).status_code==201
    doctor_headers=bearer(client.post('/api/v1/doctors/login',json={'email':'rahul@example.com','password':PASSWORD}))
    result=client.get(f'/api/v1/doctors/care-profiles/{profile}/records',headers=doctor_headers)
    assert result.status_code==200
    assert {row['title'] for row in result.json['items']}=={'Original history','Adult reading'}
