from unittest.mock import patch
from sqlalchemy import select
from core.database import db
from core.models import DoctorProfile, User, ApprovalRequest
from conftest import create_account
from test_doctor_onboarding import basic_signup
from test_workflows import submit_doctor_profile, bearer, PASSWORD


def admin_session(app, client):
    create_account(app, 'ADMIN', 'admin@example.com')
    return bearer(client.post('/api/v1/admin/login', json={'email':'admin@example.com','password':PASSWORD}))


def provider_data(url):
    if 'askmydoc' in url:
        return {'success':True,'data':{'doctor_name':'Example User','reg_number':'TEST-123','state_council':'Test Council'}}
    if 'postalpincode' in url:
        pin=url.rsplit('/',1)[-1]
        return [{'Status':'Success','PostOffice':[{'State':'Delhi','District':'New Delhi','Name':'Example Office','Pincode':pin}]}]
    return [{'display_name':'Example Clinic, Delhi, India','lat':'28.6','lon':'77.2'}]


def test_check_does_not_approve_caches_and_exposes_three_states(app, client):
    headers=admin_session(app, client)
    verified=basic_signup(app, client)
    assert verified.json['user']['doctor_status']=='pending'
    target=verified.json['user']['public_id']
    assert client.get('/api/v1/admin/doctors',headers=headers).json['total']==0
    assert not any(row['role']=='DOCTOR' for row in client.get('/api/v1/admin/dashboard',headers=headers).json['counts'])
    assert client.post(f'/api/v1/admin/doctors/{target}/check',headers=headers).status_code==409
    assert submit_doctor_profile(client,verified).status_code==202
    assert any(row['role']=='DOCTOR' for row in client.get('/api/v1/admin/dashboard',headers=headers).json['counts'])
    path=f'/api/v1/admin/doctors/{target}/check'
    assert client.post(path).status_code==401
    with patch('services.doctor_verification.fetch_json',side_effect=provider_data) as external, patch('services.doctor_verification.geocoder_slot',return_value=True):
        response=client.post(path,headers=headers)
        assert response.status_code==200
        report=response.json['verification_check']
        assert report['registration']['status']=='match'
        assert report['address']['status']=='area_match'
        assert report['clinic']['status']=='locations_found'
        assert report['auto_approved'] is False
        assert response.json['doctor_status']=='pending'
        count=external.call_count
        repeated=client.post(path,headers=headers)
        assert repeated.json['cached'] is True and external.call_count==count
    with app.app_context():
        assert db().scalar(select(User).where(User.role=='DOCTOR')).approval_status=='PENDING_APPROVAL'
        assert db().scalar(select(ApprovalRequest)).status=='PENDING'
    listing=client.get('/api/v1/admin/doctors?status=pending',headers=headers).json
    assert listing['total']==1 and listing['items'][0]['doctor_status']=='pending'
    assert listing['items'][0]['doctor']['verification_check']['registration']['status']=='match'
    approved=client.post(f'/api/v1/admin/doctors/{target}/approve',headers=headers)
    assert approved.json['user']['doctor_status']=='verified'
    assert client.post(path,headers=headers).status_code==409
    assert client.get('/api/v1/admin/doctors?status=verified',headers=headers).json['total']==1


def test_provider_outage_and_identity_mismatch_never_verify(app,client):
    headers=admin_session(app,client);verified=basic_signup(app,client)
    assert submit_doctor_profile(client,verified).status_code==202
    target=verified.json['user']['public_id'];path=f'/api/v1/admin/doctors/{target}/check'
    with patch('services.doctor_verification.fetch_json',side_effect=TimeoutError),patch('services.doctor_verification.geocoder_slot',return_value=True):
        response=client.post(path,headers=headers)
    assert response.status_code==200
    assert response.json['verification_check']['registration']['status']=='unavailable'
    assert response.json['doctor_status']=='pending'
    with app.app_context():
        db().scalar(select(DoctorProfile)).verification_check=None;db().commit()
    def mismatched(url):
        if 'askmydoc' in url:return {'success':True,'data':{'name':'Another Person','registration_number':'TEST-123','council':'Other Council'}}
        return provider_data(url)
    with patch('services.doctor_verification.fetch_json',side_effect=mismatched),patch('services.doctor_verification.geocoder_slot',return_value=True):
        response=client.post(path,headers=headers)
    assert response.json['verification_check']['registration']['status']=='mismatch'
    rejected=client.post(f'/api/v1/admin/doctors/{target}/reject',headers=headers,json={'reason':'Please correct the details'})
    assert rejected.json['user']['doctor_status']=='rejected'
    resumed=client.post('/api/v1/doctors/login',json={'email':'doctor@example.com','password':PASSWORD})
    assert resumed.json['user']['doctor_status']=='rejected'
    assert submit_doctor_profile(client,resumed).status_code==202
    with app.app_context():
        assert db().scalar(select(DoctorProfile)).verification_check is None


def test_private_address_not_sent_to_geocoder_and_scope_enforced(app,client):
    headers=admin_session(app,client);verified=basic_signup(app,client)
    assert submit_doctor_profile(client,verified).status_code==202
    path=f"/api/v1/admin/doctors/{verified.json['user']['public_id']}/check"
    create_account(app,'PATIENT','patient@example.com')
    patient=bearer(client.post('/api/v1/patients/login',json={'email':'patient@example.com','password':PASSWORD}))
    assert client.post(path,headers=patient).status_code==403
    with patch('services.doctor_verification.fetch_json',side_effect=provider_data) as external,patch('services.doctor_verification.geocoder_slot',return_value=False):
        response=client.post(path,headers=headers)
        urls=[call.args[0] for call in external.call_args_list]
    assert response.json['verification_check']['clinic']['status']=='rate_limited'
    assert all('Doctor+Street' not in url and 'Doctor%20Street' not in url for url in urls)
    assert not any('nominatim' in url for url in urls)


def test_incomplete_and_unexpected_registry_response_are_manual(app):
    from services.doctor_verification import registration_check,postal_check,clinic_check
    values={'medical_registration_number':'123','registering_council':'Delhi Medical Council','full_name':'Dr Example Kumar'}
    with app.app_context():
        with patch('services.doctor_verification.fetch_json',return_value={'success':True,'verified':True}):
            assert registration_check(values)['status']=='manual_review'
        with patch('services.doctor_verification.fetch_json',return_value={'data':{'name':'Dr Example Kumar','reg_number':'123'}}):
            assert registration_check(values)['status']=='manual_review'
        with patch('services.doctor_verification.fetch_json') as external:
            assert postal_check('Address without a PIN')['status']=='manual_review'
            assert external.call_count==0
        app.config['CLINIC_GEOCODING_ENABLED']=False
        with patch('services.doctor_verification.fetch_json') as external:
            assert clinic_check('Example Clinic Delhi 110001')['status']=='manual_review'
            assert external.call_count==0
        app.config['CLINIC_GEOCODING_ENABLED']=True
