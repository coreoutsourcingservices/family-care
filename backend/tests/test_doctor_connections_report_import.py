from core.database import db
from core.models import CareProfile, CareReport, ReportText, DoctorProfile, PatientProfile, uid
from test_care import patient, create_profile
from test_referrals import doctor
from test_workflows import bearer, PASSWORD

def doctor_headers(app,client):
    doctor_id,referral=doctor(app)
    return doctor_id,referral,bearer(client.post('/api/v1/doctors/login',json={'email':'rahul@example.com','password':PASSWORD}))

def test_practice_profile_is_owned_and_registration_unchanged(app,client):
    doctor_id,referral,headers=doctor_headers(app,client)
    assert client.get('/api/v1/doctors/practice-profile',headers=headers).json['complete'] is False
    data=dict(clinic_name='Example Clinic',city='Pune',address='Example Road 12',experience_years=5,languages=['English','Hindi'],consultation_hours='Monday-Friday 10-4',bio='Example practice')
    assert client.put('/api/v1/doctors/practice-profile',headers=headers,json={**data,'verification_status':'APPROVED'}).status_code==422
    result=client.put('/api/v1/doctors/practice-profile',headers=headers,json=data)
    assert result.status_code==200,result.json
    assert result.json['complete'] is True
    assert client.get('/api/v1/doctors/practice-profile',headers=headers).json['profile']['city']=='Pune'
    owner=patient(app,client)
    assert client.put('/api/v1/doctors/practice-profile',headers=owner,json=data).status_code==403
    with app.app_context():
        profile=db().get(DoctorProfile,doctor_id)
        assert profile.referral_id==referral and profile.qualification=='MBBS' and profile.verification_status=='PENDING'

def test_disconnect_revokes_only_shared_profile_access(app,client):
    _,referral,headers=doctor_headers(app,client)
    owner=patient(app,client)
    child=create_profile(client,owner,referral_id=referral)
    other=create_profile(client,owner,referral_id=referral)
    assert client.post('/api/v1/children/'+child+'/growth',headers=owner,json={'title':'Weight only','date':'2026-10-01','weight':'20'}).status_code==201
    client.post('/api/v1/children/'+child+'/care-notes',headers=owner,json={'title':'Private diary','date':'2026-10-01'})
    result=client.get('/api/v1/doctors/care-profiles/'+child+'/records',headers=headers)
    assert result.status_code==200 and len(result.json['items'])==1
    stranger=patient(app,client,'other@example.com')
    assert client.delete('/api/v1/patients/profiles/'+child+'/doctor',headers=stranger).status_code==404
    assert client.delete('/api/v1/patients/profiles/'+child+'/doctor',headers=owner).status_code==200
    assert client.get('/api/v1/doctors/care-profiles/'+child,headers=headers).status_code==404
    assert client.get('/api/v1/doctors/care-profiles/'+child+'/records',headers=headers).status_code==404
    assert client.get('/api/v1/doctors/care-profiles/'+other,headers=headers).status_code==200
    with app.app_context():
        owner_id=db().get(CareProfile,other).owner_id
        if not db().get(PatientProfile,owner_id): db().add(PatientProfile(user_id=owner_id))
        db().commit()
    assert client.post('/api/v1/patients/connect-doctor',headers=owner,json={'referral_id':referral}).status_code==200
    assert client.delete('/api/v1/patients/doctor',headers=owner).status_code==200
    assert client.get('/api/v1/doctors/care-profiles/'+other,headers=headers).status_code==404
    assert client.get('/api/v1/patients/doctor',headers=owner).json['doctor'] is None

def test_ocr_import_private_confirmed_idempotent(app,client):
    owner=patient(app,client)
    child=create_profile(client,owner)
    with app.app_context():
        report=CareReport(id=uid(),profile_id=child,name='test.pdf',content_type='application/pdf',content=b'%PDF-test')
        db().add(report);db().commit();report_id=report.id
        profile=db().get(CareProfile,child)
        db().add(ReportText(report_id=report_id,requested_by=profile.owner_id,status='COMPLETED',options={},result={'original_text':'Weight: 20 kg'}));db().commit()
    path=f'/api/v1/patients/profiles/{child}/reports/{report_id}/import'
    payload=dict(kind='growth',reviewed=True,record={'title':'Report weight','date':'2026-10-01','weight':'20'})
    assert client.post(path,headers=owner,json={**payload,'reviewed':False}).status_code==422
    stranger=patient(app,client,'stranger@example.com')
    assert client.post(path,headers=stranger,json=payload).status_code==404
    first=client.post(path,headers=owner,json=payload)
    assert first.status_code==201,first.json
    assert first.json['record']['source_report_id']==report_id
    again=client.post(path,headers=owner,json=payload)
    assert again.status_code==200 and again.json['already_imported'] is True
    rows=client.get(f'/api/v1/children/{child}/growth',headers=owner).json['items']
    assert len(rows)==1 and rows[0]['weight']=='20' and not rows[0]['height']
    assert client.get(f'/api/v1/patients/profiles/{child}/imported-records',headers=owner).json['total']==1
    response=client.post(path,headers=owner,json={**payload,'kind':'vaccination','record':{'title':'Test vaccine','date':'2026-10-01','status':'Completed'}})
    assert response.status_code==201,response.json
    records=client.get(f'/api/v1/children/{child}/vaccinations/history',headers=owner).json['items']
    assert records[0]['certificate_id']==report_id and records[0]['verification_status']=='PARENT_REPORTED'
