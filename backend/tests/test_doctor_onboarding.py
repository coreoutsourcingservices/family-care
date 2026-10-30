from sqlalchemy import select
from core.database import db
from core.models import ApprovalRequest, DoctorProfile
from conftest import create_account
from test_workflows import registration, verify, bearer, submit_doctor_profile, PASSWORD
import io
from unittest.mock import patch
from core.models import User


def basic_signup(app, client, email='doctor@example.com'):
    registered = client.post('/api/v1/doctors/register', json=registration('patients', email))
    assert registered.status_code == 202
    return verify(app, client, registered, 'doctors')


def test_setup_is_required_before_review_and_dashboard_access(app, client):
    verified = basic_signup(app, client)
    assert verified.status_code == 202
    assert verified.json['requires_profile_setup']
    assert verified.json['user']['approval_status'] == 'PROFILE_REQUIRED'
    assert 'access_token' not in verified.json
    with app.app_context():
        assert db().scalar(select(ApprovalRequest)) is None
    setup_headers = {'Authorization': 'Bearer ' + verified.json['setup_token']}
    assert client.get('/api/v1/doctors/me', headers=setup_headers).status_code == 401
    credentials = {'email': 'doctor@example.com', 'password': PASSWORD}
    resumed = client.post('/api/v1/doctors/login', json=credentials)
    assert resumed.json['requires_profile_setup']
    assert resumed.json['user']['full_name'] == 'Example User'
    create_account(app, 'ADMIN', 'admin@example.com')
    admin = bearer(client.post('/api/v1/admin/login', json={'email': 'admin@example.com', 'password': PASSWORD}))
    target = verified.json['user']['public_id']
    assert client.get('/api/v1/admin/doctor-requests', headers=admin).json['total'] == 0
    assert client.post(f'/api/v1/admin/doctors/{target}/approve', headers=admin).status_code == 409
    submitted = submit_doctor_profile(client, resumed)
    assert submitted.status_code == 202
    assert submitted.json['user']['approval_status'] == 'PENDING_APPROVAL'
    assert submit_doctor_profile(client, resumed).status_code == 409
    pending = client.post('/api/v1/doctors/login', json=credentials)
    assert pending.status_code == 202 and 'access_token' not in pending.json
    assert pending.json['doctor']['clinic_address'] == 'Clinic Road, Delhi 110002'
    requests = client.get('/api/v1/admin/doctor-requests', headers=admin).json
    assert requests['total'] == 1
    doctor = requests['items'][0]['doctor']
    assert doctor['address'] == 'Doctor Street, Delhi 110001'
    assert doctor['clinic_address'] == 'Clinic Road, Delhi 110002'
    assert doctor['years_of_experience'] == 5
    assert client.post(f'/api/v1/admin/doctors/{target}/reject', json={'reason': 'Correct your clinic address'}, headers=admin).status_code == 200
    rejected = client.post('/api/v1/doctors/login', json=credentials)
    assert rejected.json['requires_profile_setup']
    assert rejected.json['rejection_reason'] == 'Correct your clinic address'
    assert rejected.json['doctor']['years_of_experience'] == 5
    assert submit_doctor_profile(client, rejected).status_code == 202
    assert client.post(f'/api/v1/admin/doctors/{target}/approve', headers=admin).status_code == 200
    session = client.post('/api/v1/doctors/login', json=credentials)
    assert session.status_code == 200
    assert client.get('/api/v1/doctors/me', headers=bearer(session)).status_code == 200


def test_setup_validation_and_unverified_token(app, client):
    verified = basic_signup(app, client)
    body = dict(setup_token=verified.json['setup_token'], qualification='MBBS',
                medical_registration_number='VALID-123', registering_council='Example Council',
                address='Delhi 110001', clinic_address='Delhi 110002', years_of_experience=0)
    for field, value in [('address', '     '), ('clinic_address', ''), ('years_of_experience', -1),
                         ('years_of_experience', 2.5), ('qualification', '  '),
                         ('medical_registration_number', '!invalid')]:
        assert client.post('/api/v1/doctors/setup-profile', json={**body, field: value}).status_code == 422
    assert client.post('/api/v1/doctors/setup-profile', json={**body, 'setup_token': 'invalid'}).status_code == 401
    with app.app_context():
        assert db().scalar(select(ApprovalRequest)) is None
    assert client.post('/api/v1/doctors/setup-profile', json=body).status_code == 202
    with app.app_context():
        assert db().scalar(select(DoctorProfile)).years_of_experience == 0


def test_duplicate_credentials_rejected_at_profile_submission(app, client):
    first = basic_signup(app, client)
    second = basic_signup(app, client, 'second@example.com')
    assert submit_doctor_profile(client, first).status_code == 202
    assert submit_doctor_profile(client, second).status_code == 409
    with app.app_context():
        assert len(db().scalars(select(ApprovalRequest)).all()) == 1


def test_legacy_signup_pending_without_setup_resumes_profile(app, client):
    verified = basic_signup(app, client)
    with app.app_context():
        user = db().get(User, verified.json['user']['id'])
        user.approval_status = 'PENDING_APPROVAL'
        db().add(ApprovalRequest(applicant_id=user.id, applicant_role='DOCTOR'))
        db().commit()
    resumed = client.post('/api/v1/doctors/login', json={'email': 'doctor@example.com', 'password': PASSWORD})
    assert resumed.status_code == 202 and resumed.json['requires_profile_setup']
    assert resumed.json['user']['approval_status'] == 'PROFILE_REQUIRED'
    with app.app_context():
        assert db().scalar(select(ApprovalRequest)) is None
    assert submit_doctor_profile(client, resumed).status_code == 202


def test_images_are_private_and_do_not_submit_approval(app, client):
    verified = basic_signup(app, client)
    app.config.update(CLOUDINARY_CLOUD_NAME='test', CLOUDINARY_API_KEY='test', CLOUDINARY_API_SECRET='test')
    def upload(kind, content=b'\x89PNG\r\n\x1a\nimage'):
        return client.post('/api/v1/doctors/setup-images', data={
            'setup_token': verified.json['setup_token'], 'kind': kind,
            'file': (io.BytesIO(content), 'doctor.png')})
    with patch('doctor.onboarding_images.cloudinary.uploader.upload') as cloud:
        cloud.side_effect = lambda *args, **kwargs: dict(public_id=kwargs['public_id'], type='authenticated', resource_type='image', format='png')
        assert upload('profile_photo').status_code == 201
        assert upload('degree_photo').status_code == 201
        assert upload('degree_photo', b'%PDF-invalid').status_code == 422
        assert upload('unknown').status_code == 422
        assert cloud.call_count == 2
    resumed = client.post('/api/v1/doctors/login', json={'email': 'doctor@example.com', 'password': PASSWORD})
    assert set(resumed.json['doctor']['images']) == {'profile_photo', 'degree_photo'}
    with app.app_context():
        assert db().scalar(select(ApprovalRequest)) is None
        assert db().get(User, verified.json['user']['id']).approval_status == 'PROFILE_REQUIRED'
    assert submit_doctor_profile(client, resumed).status_code == 202
    assert upload('degree_photo').status_code == 409


def test_image_upload_failure_keeps_setup_unsubmitted(app, client):
    verified = basic_signup(app, client)
    app.config.update(CLOUDINARY_CLOUD_NAME='test', CLOUDINARY_API_KEY='test', CLOUDINARY_API_SECRET='test')
    with patch('doctor.onboarding_images.cloudinary.uploader.upload', side_effect=RuntimeError('offline')):
        result = client.post('/api/v1/doctors/setup-images', data={
            'setup_token': verified.json['setup_token'], 'kind': 'profile_photo',
            'file': (io.BytesIO(b'\x89PNG\r\n\x1a\nimage'), 'doctor.png')})
    assert result.status_code == 502
    with app.app_context():
        assert db().scalar(select(ApprovalRequest)) is None
        assert db().scalar(select(DoctorProfile)).onboarding_images is None
