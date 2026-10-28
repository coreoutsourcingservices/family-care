from core.database import db
from core.models import CareReport
from conftest import create_account
from test_workflows import PASSWORD, bearer
from test_care import patient, create_profile


def staff(app, client, role='ADMIN', email='staff@example.com'):
    create_account(app, role, email)
    prefix = 'admin' if role == 'ADMIN' else 'superadmin'
    headers = bearer(client.post('/api/v1/'+prefix+'/login', json={'email':email,'password':PASSWORD}))
    return prefix, headers


def test_patient_member_counts_and_details(app, client):
    owner = patient(app, client)
    self_id = create_profile(client, owner, kind='self', module='adult')
    child = create_profile(client, owner, full_name='Child One', guardian_contact='+919876543210',
                           emergency_contacts=[{'name':'Parent','mobile_number':'+919876543210','relationship':'Father'}])
    create_profile(client, owner, module='women')
    account = client.get('/api/v1/patients/me', headers=owner).json['user']
    prefix, admin = staff(app, client)
    base = '/api/v1/'+prefix+'/patients/'+account['id']
    users = client.get('/api/v1/admin/patients', headers=admin).json['items']
    assert users[0]['profile_counts'] == dict(total=3,members=2,self=1,child=1,adult=1,women=1)
    detail = client.get(base, headers=admin)
    assert detail.status_code == 200
    assert detail.json['user']['id'] == account['id']
    assert 'password_hash' not in detail.json['user']
    assert client.get(base+'/profiles', headers=admin).json['total'] == 3
    filtered = client.get(base+'/profiles?module=child&per_page=1', headers=admin)
    assert filtered.json['total'] == 1
    assert filtered.json['items'][0]['id'] == child
    detail = client.get(base+'/profiles/'+child, headers=admin)
    assert detail.status_code == 200
    assert detail.json['profile']['profile_type'] == 'member'
    assert detail.json['profile']['full_name'] == 'Child One'
    assert detail.json['owner']['id'] == account['id']
    assert detail.json['profile']['emergency_contacts'][0]['name'] == 'Parent'
    assert client.get(base+'/profiles/'+self_id, headers=admin).json['profile']['profile_type'] == 'self'
    assert client.get('/api/v1/admin/patients/'+account['public_id'], headers=admin).status_code == 200


def test_directory_permissions_and_membership_binding(app, client):
    first = patient(app, client)
    child = create_profile(client, first)
    first_id = client.get('/api/v1/patients/me', headers=first).json['user']['id']
    second = patient(app, client, 'second@example.com')
    second_id = client.get('/api/v1/patients/me', headers=second).json['user']['id']
    _, admin = staff(app, client)
    for path in ('/api/v1/admin/patients/'+first_id, '/api/v1/admin/patients/'+first_id+'/profiles',
                 '/api/v1/admin/patients/'+first_id+'/profiles/'+child):
        assert client.get(path).status_code == 401
        assert client.get(path, headers=first).status_code == 403
    assert client.get('/api/v1/admin/patients/'+second_id+'/profiles/'+child, headers=admin).status_code == 404
    assert client.get('/api/v1/admin/patients/'+second_id, headers=admin).json['profile_counts']['total'] == 0
    assert client.get('/api/v1/admin/patients/'+second_id+'/profiles', headers=admin).json['items'] == []
    assert client.get('/api/v1/admin/patients/'+first_id+'/profiles?module=unknown', headers=admin).status_code == 422
    assert client.get('/api/v1/admin/patients/'+first_id+'/profiles?page=0', headers=admin).status_code == 400
    _, superadmin = staff(app, client, 'SUPERADMIN', 'owner@example.com')
    assert client.get('/api/v1/superadmin/patients/'+first_id+'/profiles/'+child, headers=superadmin).status_code == 200
    assert client.get('/api/v1/superadmin/patients/'+first_id, headers=admin).status_code == 403
    assert client.get('/api/v1/admin/patients/'+first_id, headers=superadmin).status_code == 403


def test_profile_reports_are_counted_without_exposing_files(app, client):
    owner = patient(app, client)
    child = create_profile(client, owner)
    account = client.get('/api/v1/patients/me', headers=owner).json['user']
    with app.app_context():
        db().add(CareReport(profile_id=child,name='Private report.pdf',content_type='application/pdf',content=b'private'))
        db().commit()
    _, admin = staff(app, client)
    result = client.get('/api/v1/admin/patients/'+account['id']+'/profiles/'+child, headers=admin)
    assert result.json['profile']['report_count'] == 1
    assert 'reports' not in result.json['profile']
    assert 'content' not in result.json['profile']
