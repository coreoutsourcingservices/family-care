import io
import zipfile
from datetime import timedelta
import pytest
from sqlalchemy import select
from core.database import db
from core.models import CareReport, DoctorHandoff, User, WomenAccessGrant, FamilyInvitation, now, uid
from test_care import patient, create_profile
from test_referrals import doctor
from test_workflows import bearer, PASSWORD


@pytest.fixture
def handoff_setup(app, client):
    owner=patient(app,client)
    profile=create_profile(client,owner,kind='self',module='women',date_of_birth='1990-01-01')
    source,source_code=doctor(app)
    recipient,recipient_code=doctor(app,email='second@example.com',public_id='D000002')
    sh=bearer(client.post('/api/v1/doctors/login',json={'email':'rahul@example.com','password':PASSWORD}))
    rh=bearer(client.post('/api/v1/doctors/login',json={'email':'second@example.com','password':PASSWORD}))
    assert client.post(f'/api/v1/patients/profiles/{profile}/connect-doctor',headers=owner,json={'referral_id':source_code}).status_code==200
    assert client.put(f'/api/v1/women/profiles/{profile}/sharing',headers=owner,json={'recipient_id':source,'permissions':{'records':'view'}}).status_code==200
    with app.app_context():
        report=CareReport(id=uid(),profile_id=profile,name='lab-report.pdf',content_type='application/pdf',content=b'%PDF-1.4 Synthetic test report',storage_provider='database')
        db().add(report);db().commit();report_id=report.id
        public_id=db().get(User,recipient).public_id
    body=dict(doctor_identifier=recipient_code,summary=['Reason for referral: specialist review','Please review the selected lab report.'],report_ids=[report_id],expires_in_days=7)
    return dict(owner=owner,profile=profile,source=source,recipient=recipient,sh=sh,rh=rh,body=body,report=report_id,public_id=public_id)


def request(client, fixture, **changes):
    return client.post(f"/api/v1/doctors/women/{fixture['profile']}/handoffs",headers=fixture['sh'],json={**fixture['body'],**changes})


def decide(client,fixture,handoff_id,decision='APPROVED',headers=None):
    return client.put(f"/api/v1/women/profiles/{fixture['profile']}/handoffs/{handoff_id}",headers=headers or fixture['owner'],json={'decision':decision})


@pytest.mark.parametrize('identifier',['referral','public'])
def test_patient_approved_doctor_referral_and_revocation(app,client,handoff_setup,identifier):
    f=handoff_setup
    response=request(client,f,doctor_identifier=f['public_id'] if identifier=='public' else f['body']['doctor_identifier'])
    assert response.status_code==201,response.json
    row=response.json['handoff'];path='/api/v1/doctors/handoffs/'+row['id']+'/download'
    assert row['status']=='PENDING'
    assert client.get('/api/v1/doctors/handoffs',headers=f['rh']).json['items']==[]
    assert client.get(path,headers=f['rh']).status_code==403
    assert client.get(path,headers=f['sh']).status_code==403
    assert decide(client,f,row['id'],headers=f['rh']).status_code==403
    assert decide(client,f,row['id']).status_code==200
    received=client.get('/api/v1/doctors/handoffs',headers=f['rh']).json['items']
    assert len(received)==1 and received[0]['summary']==f['body']['summary']
    response=client.get(path,headers=f['rh'])
    assert response.status_code==200,response.json
    with zipfile.ZipFile(io.BytesIO(response.data)) as archive:
        assert len(archive.namelist())==2
        assert 'specialist review' in archive.read('referral-summary.txt').decode()
        assert archive.read(f['report']+'_lab-report.pdf').startswith(b'%PDF')
    # This limited referral must not grant broader Women workspace access.
    assert client.get(f"/api/v1/women/profiles/{f['profile']}/workspace",headers=f['rh']).status_code==403
    assert decide(client,f,row['id'],'REVOKED').status_code==200
    assert client.get(path,headers=f['rh']).status_code==403
    assert client.get('/api/v1/doctors/handoffs',headers=f['rh']).json['items']==[]


def test_external_referral_download_requires_woman_approval(app,client,handoff_setup):
    f=handoff_setup
    response=request(client,f,doctor_identifier='',external_name='External specialist',external_email='outside@example.com')
    assert response.status_code==201,response.json
    row=response.json['handoff'];path='/api/v1/doctors/handoffs/'+row['id']+'/download'
    assert row['external'] is True
    assert client.get(path,headers=f['sh']).status_code==403
    assert decide(client,f,row['id']).status_code==200
    assert client.get(path,headers=f['sh']).status_code==200
    assert client.get(path,headers=f['rh']).status_code==404


@pytest.mark.parametrize('condition',['expiry','source_revoked','source_disconnected','recipient_suspended','report_removed'])
def test_revalidate_access_on_every_download(app,client,handoff_setup,condition):
    f=handoff_setup;row=request(client,f).json['handoff'];assert decide(client,f,row['id']).status_code==200
    with app.app_context():
        if condition=='expiry':db().get(DoctorHandoff,row['id']).expires_at=now()-timedelta(seconds=1)
        elif condition=='source_revoked':db().scalar(select(WomenAccessGrant).where(WomenAccessGrant.profile_id==f['profile'])).revoked_at=now()
        elif condition=='source_disconnected':
            from core.models import CareProfile
            db().get(CareProfile,f['profile']).referred_doctor_id=None
        elif condition=='recipient_suspended':db().get(User,f['recipient']).account_status='SUSPENDED'
        else:db().delete(db().get(CareReport,f['report']))
        db().commit()
    assert client.get('/api/v1/doctors/handoffs/'+row['id']+'/download',headers=f['sh']).status_code in (403,409)


def test_scope_validation_and_decline(app,client,handoff_setup):
    f=handoff_setup
    assert request(client,f,report_ids=[uid()]).status_code==409
    assert request(client,f,doctor_identifier='unknown-id').status_code==422
    assert request(client,f,summary=[' ']).status_code==422
    assert request(client,f,doctor_identifier='',external_name='No contact').status_code==422
    assert client.post(f"/api/v1/doctors/women/{f['profile']}/handoffs",headers=f['rh'],json=f['body']).status_code==403
    row=request(client,f).json['handoff'];assert decide(client,f,row['id'],'DECLINED').status_code==200
    assert decide(client,f,row['id']).status_code==409
    assert client.get('/api/v1/doctors/handoffs/'+row['id']+'/download',headers=f['sh']).status_code==403


def test_invited_woman_approves_instead_of_family_owner(app,client,handoff_setup):
    f=handoff_setup;member=patient(app,client,'woman@example.com')
    with app.app_context():
        mid=db().scalar(select(User.id).where(User.email=='woman@example.com'))
        owner_id=db().scalar(select(User.id).where(User.email=='family@example.com'))
        db().add(FamilyInvitation(owner_id=owner_id,member_id=mid,profile_id=f['profile'],token_hash='handoff-test',
            full_name='Woman',email='woman@example.com',module='women',accepted_at=now(),expires_at=now()+timedelta(days=1)))
        db().commit()
    row=request(client,f).json['handoff']
    assert decide(client,f,row['id']).status_code==403
    assert decide(client,f,row['id'],headers=member).status_code==200


def test_handoff_api_contract_uses_distinct_decision_schema(client):
    spec=client.get('/api/openapi.json').json
    path='/api/v1/women/profiles/{profile_id}/handoffs/{handoff_id}'
    assert spec['paths'][path]['put']['requestBody']['content']['application/json']['schema']['$ref'].endswith('/HandoffDecision')
    assert 'application/zip' in spec['paths']['/api/v1/doctors/handoffs/{handoff_id}/download']['get']['responses']['200']['content']
