from conftest import create_account
from test_workflows import PASSWORD
from test_care import create_profile
from test_referrals import doctor


def headers(portal,csrf=None):
    values={'X-Auth-Transport':'cookie','X-Requested-With':'FamilyCare','X-FamilyCare-Portal':portal}
    if csrf:values['X-CSRF-Token']=csrf
    return values


def test_patient_and_doctor_cookies_refresh_logout_are_independent(app,client):
    create_account(app,'PATIENT','parent@example.com')
    doctor(app,email='physician@example.com')
    p=client.post('/api/v1/patients/login',json={'email':'parent@example.com','password':PASSWORD},headers=headers('patient'))
    assert p.status_code==200
    ph=headers('patient',p.json['csrf_token'])
    child=create_profile(client,ph)
    d=client.post('/api/v1/doctors/login',json={'email':'physician@example.com','password':PASSWORD},headers=headers('doctor'))
    assert d.status_code==200
    dh=headers('doctor',d.json['csrf_token'])
    assert client.get('/api/v1/patients/me',headers=ph).json['user']['role']=='PATIENT'
    assert client.get('/api/v1/doctors/me',headers=dh).json['user']['role']=='DOCTOR'
    for scheme in ('UIP','IAP'):
        assert client.get('/api/v1/children/'+child+'/vaccinations?schedule_type='+scheme,headers=ph).status_code==200
    assert client.get('/api/v1/children/'+child+'/vaccinations',headers=dh).status_code==403
    refreshed=client.post('/api/v1/auth/refresh',json={},headers=ph)
    assert refreshed.status_code==200 and refreshed.json['user']['role']=='PATIENT'
    assert client.post('/api/v1/auth/logout',json={},headers=dh).status_code==200
    assert client.get('/api/v1/patients/me',headers=ph).status_code==200
    assert client.get('/api/v1/doctors/me',headers=dh).status_code==401


def test_legacy_role_cookie_does_not_authenticate_other_portal(app,client):
    doctor(app,email='legacy@example.com')
    old={k:v for k,v in headers('doctor').items() if k!='X-FamilyCare-Portal'}
    assert client.post('/api/v1/doctors/login',json={'email':'legacy@example.com','password':PASSWORD},headers=old).status_code==200
    assert client.get('/api/v1/doctors/me',headers=headers('doctor')).status_code==200
    result=client.get('/api/v1/patients/me',headers=headers('patient'))
    assert result.status_code==401 and result.json['error']['code']=='portal_session_changed'
