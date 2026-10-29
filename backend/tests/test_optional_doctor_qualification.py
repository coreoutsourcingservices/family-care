import pytest
from sqlalchemy import select
from core.database import db
from core.models import User, DoctorProfile, ApprovalRequest
from test_workflows import registration, verify, PASSWORD


@pytest.mark.parametrize('degree', ['omitted', None, '', '   ', ' mbbs '])
def test_doctor_can_register_and_verify_with_optional_degree(app, client, degree):
    payload = registration('doctors', 'optional-doctor@example.com')
    if degree == 'omitted':
        payload.pop('qualification')
    else:
        payload['qualification'] = degree
    payload.update(specialization='Pediatrics', nmr_id='EXAMPLE-NMR-12')
    pending = client.post('/api/v1/doctors/register', json=payload)
    assert pending.status_code == 202, pending.json
    with app.app_context():
        assert db().scalar(select(User)) is None
    result = verify(app, client, pending, 'doctors')
    assert result.status_code == 202, result.json
    with app.app_context():
        user = db().scalar(select(User).where(User.email == payload['email']))
        profile = db().get(DoctorProfile, user.id)
        assert profile.qualification == ('MBBS' if degree == ' mbbs ' else None)
        assert profile.registering_council == 'TEST COUNCIL'
        assert profile.medical_registration_number == 'TEST-123'
        assert profile.specialization == 'Pediatrics'
        assert profile.nmr_id == 'EXAMPLE-NMR-12'
        assert user.approval_status == 'PENDING_APPROVAL'
        assert profile.verification_status == 'PENDING'
    assert client.post('/api/v1/doctors/login', json={'email': payload['email'], 'password': PASSWORD}).status_code == 403


@pytest.mark.parametrize('council', [None, '', '  '])
def test_council_is_still_required(client, council):
    payload = registration('doctors')
    payload.pop('qualification')
    if council is None:
        payload.pop('registering_council')
    else:
        payload['registering_council'] = council
    assert client.post('/api/v1/doctors/register', json=payload).status_code == 422


def test_provided_degree_is_validated(client):
    payload = registration('doctors')
    payload['qualification'] = 'X'
    assert client.post('/api/v1/doctors/register', json=payload).status_code == 422


@pytest.mark.parametrize('degree', [None, 'MBBS'])
def test_resubmission_without_degree_preserves_previous_value(app, client, degree):
    payload = registration('doctors', 'resubmit@example.com')
    payload['qualification'] = degree
    pending = client.post('/api/v1/doctors/register', json=payload)
    assert verify(app, client, pending, 'doctors').status_code == 202
    with app.app_context():
        user = db().scalar(select(User).where(User.email == payload['email']))
        user.approval_status = 'REJECTED'
        db().get(DoctorProfile, user.id).verification_status = 'REJECTED'
        db().scalar(select(ApprovalRequest).where(ApprovalRequest.applicant_id == user.id)).status = 'REJECTED'
        db().commit()
    result = client.post('/api/v1/doctors/resubmit', json={
        'email': payload['email'], 'password': PASSWORD,
        'medical_registration_number': 'UPDATED-123', 'registering_council': 'Test Council',
    })
    assert result.status_code == 202, result.json
    with app.app_context():
        profile = db().scalar(select(DoctorProfile))
        assert profile.qualification == degree
        assert profile.medical_registration_number == 'UPDATED-123'


def test_openapi_degree_optional_and_council_required(client):
    schema = client.get('/api/openapi.json').json['components']['schemas']['DoctorRegistration']
    assert 'qualification' not in schema['required']
    assert 'registering_council' in schema['required']
