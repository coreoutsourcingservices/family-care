import io
from unittest.mock import patch
import pytest
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from core.database import db
from core.models import CareProfile, CareReport, uid
from conftest import create_account
from test_workflows import PASSWORD, bearer
from test_referrals import doctor


def patient(app, client, email='family@example.com'):
    create_account(app, 'PATIENT', email)
    return bearer(client.post('/api/v1/patients/login', json={'email':email,'password':PASSWORD}))


def profile_data(kind='member', module='child', **extra):
    values = dict(profile_type=kind, module=module, full_name='Aarav Kumar', date_of_birth='2018-05-14')
    values.update(extra)
    return values


def create_profile(client, headers, **extra):
    result = client.post('/api/v1/patients/profiles', json=profile_data(**extra), headers=headers)
    assert result.status_code == 201, result.json
    return result.json['profile']['id']


@pytest.fixture
def cloud(app, monkeypatch):
    for key, value in [('CLOUD_NAME','test-cloud'),('API_KEY','test-key'),('API_SECRET','test-secret')]:
        monkeypatch.setitem(app.config, 'CLOUDINARY_'+key, value)
    def upload(stream, **options):
        return dict(public_id=options['public_id'], type=options['type'],
                    resource_type=options['resource_type'], asset_id='test-asset',
                    secure_url='https://res.cloudinary.com/test-cloud/'+options['resource_type']+'/authenticated/'+options['public_id'],
                    format='png' if options['resource_type']=='image' else 'pdf')
    with patch('services.care_uploads.cloudinary.uploader.upload',side_effect=upload) as uploader:
        yield uploader


def upload(client, headers, profile_id, content=b'%PDF-1.7\nreport', filename='blood-test.pdf'):
    return client.post(f'/api/v1/patients/profiles/{profile_id}/reports', headers=headers,
        data={'file':(io.BytesIO(content),filename)}, content_type='multipart/form-data')


def test_self_child_adult_women_and_parent_connection(app,client):
    headers=patient(app,client)
    parent_id=create_profile(client,headers,kind='self',module='adult')
    # Parent must be older than the child.
    with app.app_context():
        from datetime import date
        db().get(CareProfile,parent_id).dob=date(1990,1,1)
        db().commit()
    child_id=create_profile(client,headers,parent_profile_id=parent_id,guardian_contact='+919876543210')
    create_profile(client,headers,module='women')
    create_profile(client,headers,module='adult')
    result=client.get('/api/v1/patients/profiles',headers=headers)
    assert result.status_code==200 and result.json['total']==4
    child=client.get('/api/v1/patients/profiles/'+child_id,headers=headers).json['profile']
    assert child['parent_profile_id']==parent_id and child['date_of_birth']=='2018-05-14'
    duplicate=client.post('/api/v1/patients/profiles',json=profile_data('self','adult'),headers=headers)
    assert duplicate.status_code==409
    assert client.get('/api/v1/patients/profiles?module=women',headers=headers).json['total']==1


def test_profiles_and_parent_links_cannot_cross_accounts(app,client):
    first=patient(app,client)
    parent_id=create_profile(client,first,kind='self',module='adult')
    other=patient(app,client,'other-family@example.com')
    assert client.get('/api/v1/patients/profiles/'+parent_id,headers=other).status_code==404
    result=client.post('/api/v1/patients/profiles',json=profile_data(parent_profile_id=parent_id),headers=other)
    assert result.status_code==404
    assert client.get('/api/v1/patients/profiles',headers=other).json['total']==0
    assert client.post('/api/v1/patients/profiles',json=profile_data()).status_code==401
    assert client.post('/api/v1/patients/profiles',json=profile_data(date_of_birth='2099-01-01'),headers=first).status_code==422


def test_profile_referral_exposes_only_linked_doctors_profiles(app,client,cloud):
    _,referral=doctor(app)
    doctor(app,'second@example.com','D000002')
    headers=patient(app,client)
    profile_id=create_profile(client,headers,referral_id=referral)
    assert upload(client,headers,profile_id).status_code==201
    first=bearer(client.post('/api/v1/doctors/login',json={'email':'rahul@example.com','password':PASSWORD}))
    other=bearer(client.post('/api/v1/doctors/login',json={'email':'second@example.com','password':PASSWORD}))
    assert client.get('/api/v1/doctors/care-profiles',headers=first).json['total']==1
    assert client.get(f'/api/v1/doctors/care-profiles/{profile_id}/reports',headers=first).json['total']==1
    assert client.get(f'/api/v1/doctors/care-profiles/{profile_id}/reports',headers=other).status_code==404
    assert client.post('/api/v1/patients/profiles',json=profile_data(),headers=first).status_code==403


@pytest.mark.parametrize('content,filename,resource_type',[(b'%PDF-1.7\n'+b'x'*20000,'blood-test.pdf','raw'),(b'\x89PNG\r\n\x1a\nimage','scan.png','image')])
def test_report_cloudinary_metadata_private_links_and_folder(app,client,cloud,content,filename,resource_type):
    headers=patient(app,client)
    profile_id=create_profile(client,headers)
    result=upload(client,headers,profile_id,content,filename)
    assert result.status_code==201, result.json
    report=result.json['report']
    assert report['name']==filename and report['resource_type']==resource_type
    assert report['delivery_type']=='authenticated' and report['storage_provider']=='cloudinary'
    assert report['folder'].endswith('/profiles/'+profile_id+'/child/reports')
    assert report['public_id'].startswith(report['folder']+'/')
    assert report['url_expires_in']==300 and 'signature=' in report['url']
    assert cloud.call_args.kwargs['type']=='authenticated'
    assert report['size_bytes']==len(content)
    with app.app_context():
        assert db().get(CareReport,report['id']).content is None
    assert client.get(f'/api/v1/patients/profiles/{profile_id}/reports',headers=headers).json['total']==1
    other=patient(app,client,'stranger@example.com')
    assert client.get(f'/api/v1/patients/profiles/{profile_id}/reports/{report["id"]}/download',headers=other).status_code==404


def test_upload_configuration_type_and_size_errors(app,client,cloud,monkeypatch):
    headers=patient(app,client)
    profile_id=create_profile(client,headers)
    assert upload(client,headers,profile_id,b'not a pdf','fake.pdf').status_code==422
    assert upload(client,headers,profile_id,b'','empty.pdf').status_code==422
    monkeypatch.setitem(app.config,'MAX_REPORT_BYTES',64)
    assert upload(client,headers,profile_id,b'%PDF-'+b'x'*100).status_code==413
    monkeypatch.setitem(app.config,'CLOUDINARY_API_SECRET','')
    result=upload(client,headers,profile_id)
    assert result.status_code==503 and result.json['error']['code']=='cloudinary_not_configured'
    assert cloud.call_count==0


def test_upload_failure_leaves_no_report(app,client,cloud):
    headers=patient(app,client)
    profile_id=create_profile(client,headers)
    cloud.side_effect=OSError('unavailable')
    assert upload(client,headers,profile_id).status_code==502
    cloud.side_effect=None
    cloud.return_value=dict(public_id='wrong',type='upload',resource_type='raw',secure_url='http://untrusted')
    assert upload(client,headers,profile_id).status_code==502
    with app.app_context():
        assert db().scalar(select(CareReport)) is None


def test_failed_commit_cleans_up_new_cloudinary_asset(app,client,cloud):
    headers=patient(app,client)
    profile_id=create_profile(client,headers)
    with patch('sqlalchemy.orm.Session.commit',side_effect=SQLAlchemyError('unavailable')), patch(
            'services.care_uploads.cloudinary.uploader.destroy') as cleanup:
        assert upload(client,headers,profile_id).status_code==503
        assert cleanup.call_count==1 and cleanup.call_args.kwargs['type']=='authenticated'
    with app.app_context():
        assert db().scalar(select(CareReport)) is None


def test_legacy_database_report_remains_downloadable(app,client):
    headers=patient(app,client)
    profile_id=create_profile(client,headers)
    with app.app_context():
        report=CareReport(id=uid(),profile_id=profile_id,name='old.pdf',content_type='application/pdf',content=b'%PDF-old')
        db().add(report);db().commit();report_id=report.id
    result=client.get(f'/api/v1/patients/profiles/{profile_id}/reports/{report_id}/download',headers=headers)
    assert result.status_code==200 and result.data==b'%PDF-old'


def test_schema_documents_multipart_and_nested_contacts(client):
    spec=client.get('/api/openapi.json').json
    assert 'multipart/form-data' in spec['paths']['/api/v1/patients/profiles/{profile_id}/reports']['post']['requestBody']['content']
    assert 'EmergencyContact' in spec['components']['schemas']
