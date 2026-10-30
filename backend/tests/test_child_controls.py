from datetime import date,timedelta
from sqlalchemy import select
from core.database import db
from core.models import AppNotification,ChildRecord,ChildRecordRevision,CareProfile,ReportText,User
from test_care import patient,create_profile
from test_referrals import doctor
from test_workflows import bearer,PASSWORD
from test_report_text import report

def test_guardian_defaults_edits_and_soft_delete_revoke_access(app,client):
    headers=patient(app,client)
    with app.app_context():
        db().scalar(select(User).where(User.email=='family@example.com')).phone_number='+919876543210'
        db().commit()
    _,referral=doctor(app)
    profile=create_profile(client,headers,date_of_birth='2020-01-01',referral_id=referral)
    path=f'/api/v1/patients/profiles/{profile}'
    initial=client.get(path,headers=headers).json['profile']
    assert initial['guardian_name'] and initial['guardian_contact']
    values=dict(full_name='Updated Child',date_of_birth='2020-02-02',guardian_name='Another Guardian',guardian_contact='+919876543299')
    other=patient(app,client,'other-family@example.com')
    assert client.patch(path,headers=other,json=values).status_code==404
    assert client.delete(path,headers=other).status_code==404
    result=client.patch(path,headers=headers,json=values)
    assert result.status_code==200,result.json
    assert result.json['profile']['guardian_name']=='Another Guardian'
    doc=bearer(client.post('/api/v1/doctors/login',json={'email':'rahul@example.com','password':PASSWORD}))
    assert client.get(f'/api/v1/doctors/care-profiles/{profile}',headers=doc).status_code==200
    assert client.delete(path,headers=headers).status_code==200
    assert client.get(path,headers=headers).status_code==404
    assert client.get('/api/v1/patients/profiles',headers=headers).json['total']==0
    assert client.get('/api/v1/children',headers=headers).json['total']==0
    assert client.get(f'/api/v1/doctors/care-profiles/{profile}',headers=doc).status_code==404
    with app.app_context():assert db().get(CareProfile,profile).deleted_at is not None

def test_doctor_child_writes_are_scoped_and_private_history_hidden(app,client):
    headers=patient(app,client)
    _,referral=doctor(app)
    profile=create_profile(client,headers,referral_id=referral,date_of_birth='2020-01-01')
    private=create_profile(client,headers,date_of_birth='2020-01-01')
    doc=bearer(client.post('/api/v1/doctors/login',json={'email':'rahul@example.com','password':PASSWORD}))
    base=f'/api/v1/doctors/care-profiles/{profile}/child-records'
    assert client.post(base+'/history',headers=doc,json={}).status_code==404
    assert client.post(f'/api/v1/doctors/care-profiles/{private}/child-records/growth',headers=doc,json={}).status_code==404
    assert client.post(base+'/care',headers=headers,json={}).status_code==403
    growth=dict(title='Clinic growth measurement',date='2026-01-01',weight='18',height='110',notes='Clinician recommendation')
    result=client.post(base+'/growth',headers=doc,json=growth)
    assert result.status_code==201,result.json
    row=result.json['record']
    assert row['verification_status']=='DOCTOR_REPORTED'
    assert client.patch(f'/api/v1/children/{profile}/growth/{row["id"]}',headers=headers,json={'weight':'19'}).status_code==403
    assert client.get(f'/api/v1/children/{profile}/records',headers=headers).json['items'][0]['notes']=='Clinician recommendation'
    assert client.post(f'/api/v1/children/{profile}/medical-history',headers=headers,json={'title':'Private history','date':'2026-01-01'}).status_code==201
    shared=client.get(f'/api/v1/doctors/care-profiles/{profile}/records',headers=doc)
    assert shared.json['total']==1 and shared.json['items'][0]['kind']=='growth'
    inbox=client.get('/api/v1/notifications',headers=headers)
    assert inbox.json['items'][0]['type']=='child_record_added'
    assert 'Clinic growth measurement' not in inbox.json['items'][0]['body']

    overview=f'/api/v1/patients/profiles/{profile}/doctor-overview'
    visible=client.get(overview,headers=headers)
    assert visible.status_code==200,visible.json
    assert visible.json['total']==1
    assert visible.json['items'][0]['author_name']
    assert visible.json['doctor']['public_id']
    assert 'degree_photo' not in visible.json['doctor']
    stranger=patient(app,client,'stranger@example.com')
    assert client.get(overview,headers=stranger).status_code==404
    assert client.post(base+'/prescription',headers=doc,json={'title':'Instructions','date':'2026-01-01','notes':''}).status_code==422
    prescription=client.post(base+'/prescription',headers=doc,json={'title':'Follow-up instructions','date':'2026-01-01','notes':'Return for review as discussed.'})
    assert prescription.status_code==201,prescription.json
    assert prescription.json['record']['category']=='Prescription'
    assert client.get(base+'/prescription',headers=doc).json['total']==1
    assert client.get(overview,headers=headers).json['total']==2

def test_report_review_category_persistence_and_duplicate_import(app,client):
    headers=patient(app,client)
    _,referral=doctor(app)
    profile=create_profile(client,headers,referral_id=referral,date_of_birth='2020-01-01')
    identifier=report(app,profile)
    path=f'/api/v1/patients/profiles/{profile}/reports/{identifier}'
    payload=dict(kind='growth',reviewed=True,record=dict(title='Reviewed measurements',date='2026-01-01',weight='18',height='110'))
    assert client.post(path+'/import',headers=headers,json=payload).status_code==409
    with app.app_context():
        db().add(ReportText(report_id=identifier,requested_by=db().get(CareProfile,profile).owner_id,status='COMPLETED',options={},result={'original_text':'Weight: 18 kg, Height: 110 cm'}));db().commit()
    assert client.post(path+'/import',headers=headers,json={**payload,'reviewed':False}).status_code==422
    result=client.post(path+'/import',headers=headers,json=payload)
    assert result.status_code==201,result.json
    assert client.post(path+'/import',headers=headers,json=payload).json['already_imported'] is True
    assert client.get(f'/api/v1/children/{profile}/records',headers=headers).json['total']==1
    assert client.get(f'/api/v1/patients/profiles/{profile}/reports',headers=headers).json['items'][0]['category']=='Lab tests'
    assert client.patch(path+'/category',headers=headers,json={'category':'Scans'}).status_code==200
    assert client.get(f'/api/v1/patients/profiles/{profile}/reports',headers=headers).json['items'][0]['category']=='Scans'
    doc=bearer(client.post('/api/v1/doctors/login',json={'email':'rahul@example.com','password':PASSWORD}))
    assert client.get(f'/api/v1/doctors/care-profiles/{profile}/reports',headers=doc).json['total']==1
    unshared=report(app,profile)
    assert client.get(f'/api/v1/doctors/care-profiles/{profile}/reports/{unshared}/download',headers=doc).status_code==404

def test_realtime_inbox_read_isolation_ticket_purpose_and_reminders(app,client):
    from services.notifications import scan_due,socket_user
    headers=patient(app,client)
    _,referral=doctor(app)
    profile=create_profile(client,headers,referral_id=referral,date_of_birth='2020-01-01')
    result=client.post('/api/v1/notifications/test',headers=headers,json={})
    assert result.status_code==201
    identifier=result.json['notification']['id']
    other=patient(app,client,'other-account@example.com')
    assert client.post(f'/api/v1/notifications/{identifier}/read',headers=other,json={}).status_code==404
    assert client.get('/api/v1/notifications',headers=other).json['items']==[]
    assert client.post(f'/api/v1/notifications/{identifier}/read',headers=headers,json={}).json['unread_count']==0
    ticket=client.post('/api/v1/notifications/socket-ticket',headers=headers,json={}).json['ticket']
    assert client.get('/api/v1/patients/me',headers={'Authorization':'Bearer '+ticket}).status_code==401
    with app.app_context():
        user,claims=socket_user(ticket)
        assert user.role=='PATIENT'
        db().add(ChildRecord(profile_id=profile,kind='vaccination',data={'title':'Private vaccine name','date':date.today().isoformat(),'status':'Planned'}));db().commit()
        scan_due();scan_due()
        notices=db().scalars(select(AppNotification).where(AppNotification.kind=='vaccination_due')).all()
        assert len(notices)==2
        assert all('Private vaccine name' not in n.body for n in notices)
        db().get(CareProfile,profile).deleted_at=__import__('core.models',fromlist=['now']).now();db().commit()
        before=len(db().scalars(select(AppNotification)).all());scan_due()
        assert len(db().scalars(select(AppNotification)).all())==before
    client.post('/api/v1/auth/logout',headers=headers)
    with app.app_context():
        from core.errors import APIError
        import pytest
        with pytest.raises(APIError):socket_user(ticket)
