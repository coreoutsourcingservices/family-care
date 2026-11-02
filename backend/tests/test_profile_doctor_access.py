from datetime import timedelta
from core.database import db
from core.models import CareReport,ProfileDoctorGrant,AdultRecord,now
from test_care import patient,create_profile
from test_referrals import doctor
from test_workflows import bearer,PASSWORD


def test_scoped_reports_expiry_and_revoke(app,client):
    owner=patient(app,client);profile=create_profile(client,owner,module='adult',date_of_birth='1990-01-01')
    private=create_profile(client,owner,module='women',date_of_birth='1990-01-01')
    doctor_id,referral=doctor(app)
    dh=bearer(client.post('/api/v1/doctors/login',json={'email':'rahul@example.com','password':PASSWORD}))
    with app.app_context():
        shared=CareReport(profile_id=profile,name='Selected.pdf',content_type='application/pdf',content=b'%PDF-test',storage_provider='database')
        hidden=CareReport(profile_id=profile,name='Private.pdf',content_type='application/pdf',content=b'%PDF-private',storage_provider='database')
        db().add_all([shared,hidden]);db().commit();sid=shared.id;hid=hidden.id
    access=f'/api/v1/patients/profiles/{profile}/doctor-access'
    response=client.put(access,headers=owner,json={'referral_id':referral,'scopes':['reports'],'report_ids':[sid],'expires_at':(now()+timedelta(hours=1)).isoformat()+'Z'})
    assert response.status_code==200,response.json
    base=f'/api/v1/doctors/care-profiles/{profile}'
    assert client.get(base,headers=dh).status_code==200
    assert [r['id'] for r in client.get(base+'/reports',headers=dh).json['items']]==[sid]
    assert client.get(base+'/reports/'+sid+'/download',headers=dh).status_code==200
    assert client.get(base+'/reports/'+hid+'/download',headers=dh).status_code==404
    assert client.get(base+'/records',headers=dh).status_code==403
    assert client.get(f'/api/v1/doctors/care-profiles/{private}',headers=dh).status_code==404
    with app.app_context():db().get(ProfileDoctorGrant,profile).expires_at=now()-timedelta(seconds=1);db().commit()
    assert client.get(base,headers=dh).status_code==404
    assert client.get(base+'/reports/'+sid+'/download',headers=dh).status_code==404
    assert client.get('/api/v1/doctors/care-profiles',headers=dh).json['items']==[]
    assert client.put(access,headers=owner,json={'referral_id':referral,'scopes':['reports'],'expires_at':None}).status_code==200
    assert client.delete(access,headers=owner).status_code==200
    assert client.get(base,headers=dh).status_code==404


def test_record_type_limits_also_apply_to_consultation_inbox(app,client):
    owner=patient(app,client);profile=create_profile(client,owner,module='adult',date_of_birth='1990-01-01')
    _,referral=doctor(app)
    dh=bearer(client.post('/api/v1/doctors/login',json={'email':'rahul@example.com','password':PASSWORD}))
    with app.app_context():
        db().add_all([AdultRecord(profile_id=profile,kind='bp',data={'title':'Selected','date':'2026-01-01'}),AdultRecord(profile_id=profile,kind='consultation_request',data={'title':'Not shared','date':'2026-01-01'})]);db().commit()
    path=f'/api/v1/patients/profiles/{profile}/doctor-access'
    assert client.put(path,headers=owner,json={'referral_id':referral,'scopes':['records'],'record_kinds':['bp']}).status_code==200
    records=client.get(f'/api/v1/doctors/care-profiles/{profile}/records',headers=dh).json['items']
    assert [r['kind'] for r in records]==['bp']
    assert client.get('/api/v1/doctors/consultation-requests',headers=dh).json['items']==[]
    assert client.get(f'/api/v1/doctors/care-profiles/{profile}/reports',headers=dh).status_code==403
    stranger=patient(app,client,'stranger-grant@example.com')
    assert client.put(path,headers=stranger,json={'referral_id':referral,'scopes':['reports']}).status_code==404
    child=create_profile(client,owner)
    assert client.put(f'/api/v1/patients/profiles/{child}/doctor-access',headers=owner,json={'referral_id':referral,'scopes':['reports']}).status_code==422
