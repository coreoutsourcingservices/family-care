import pytest
from sqlalchemy import select, func
from core.database import db
from core.models import User, DoctorProfile, PatientProfile, uid
from core.security import password_hasher
from core.referrals import make_referral_id
from test_workflows import registration, verify, bearer, PASSWORD


def doctor(app, email='rahul@example.com', public_id='D000001', approved=True):
    with app.app_context():
        user = User(id=uid(), full_name='Dr Rahul Kumar', email=email, phone_number='+919876543211',
                    public_id=public_id if db().bind.dialect.name == 'sqlite' else None,
                    password_hash=password_hasher.hash(PASSWORD), role='DOCTOR', email_verified=True,
                    approval_status='APPROVED' if approved else 'PENDING_APPROVAL')
        db().add(user)
        db().flush()
        db().refresh(user)
        profile = DoctorProfile(user_id=user.id, qualification='MBBS',
                                medical_registration_number=uid(), registering_council='Test Council')
        db().add(profile)
        db().commit()
        return user.id, profile.referral_id


def test_referral_name_and_public_id():
    assert make_referral_id('Dr Rahul Kumar', 'D000001') == 'rahulkumarD000001'
    assert make_referral_id('  Dr. Rahul Kumar ', 'D000002') == 'rahulkumarD000002'
    assert make_referral_id('Doctor Rahul-Kumar', 'D000003') == 'rahulkumarD000003'


def test_doctor_referral_contact_and_patient_signup_connection(app, client):
    doctor_id, referral_id = doctor(app)
    login = client.post('/api/v1/doctors/login', json={'email':'rahul@example.com','password':PASSWORD})
    detail = client.get('/api/v1/doctors/referral', headers=bearer(login))
    assert detail.status_code == 200
    assert detail.json['doctor'] == dict(referral_id=referral_id, public_id=login.json['user']['public_id'],
        full_name='Dr Rahul Kumar', email='rahul@example.com', mobile_number='+919876543211',
        account_status='ACTIVE', approval_status='APPROVED')
    assert login.json['user']['referral_id'] == referral_id
    data = registration()
    data['referral_id'] = referral_id.upper()
    pending = client.post('/api/v1/patients/register', json=data)
    assert pending.status_code == 202
    with app.app_context():
        assert db().scalar(select(func.count()).select_from(User)) == 1
        assert db().scalar(select(PatientProfile)) is None
    patient = verify(app, client, pending)
    assert patient.status_code == 200
    assert patient.json['user']['referred_doctor']['referral_id'] == referral_id
    with app.app_context():
        profile = db().get(PatientProfile, patient.json['user']['id'])
        assert profile.referred_by_doctor_id == doctor_id and profile.referred_at
    assert client.get('/api/v1/patients/doctor',headers=bearer(patient)).json['doctor']['email'] == 'rahul@example.com'
    patients = client.get('/api/v1/doctors/patients',headers=bearer(login))
    assert patients.status_code == 200 and patients.json['total'] == 1
    assert client.get('/api/v1/doctors/patients',headers=bearer(patient)).status_code == 403


@pytest.mark.parametrize('approved', [True, False])
def test_invalid_or_unapproved_referral_creates_no_patient(app, client, approved):
    _, referral_id = doctor(app, approved=approved)
    data = registration()
    data['referral_id'] = 'doesnotexistD999999' if approved else referral_id
    result = client.post('/api/v1/patients/register',json=data)
    assert result.status_code == 422 and result.json['error']['code'] == 'invalid_referral'
    with app.app_context():
        assert db().scalar(select(func.count()).select_from(User)) == 1
        assert not app.extensions['pending_signups'].all()


def test_referral_rechecked_when_signup_otp_is_verified(app, client):
    doctor_id, referral_id = doctor(app)
    data = registration()
    data['referral_id'] = referral_id
    pending = client.post('/api/v1/patients/register',json=data)
    with app.app_context():
        db().get(User, doctor_id).account_status = 'SUSPENDED'
        db().commit()
    assert verify(app, client, pending).status_code == 422
    with app.app_context():
        assert db().scalar(select(func.count()).select_from(User)) == 1


def test_existing_patient_connection_idempotent_and_scoped(app, client):
    _, referral_id = doctor(app)
    _, second = doctor(app, 'other@example.com', 'D000002')
    pending = client.post('/api/v1/patients/register',json=registration())
    patient = verify(app, client, pending)
    headers = bearer(patient)
    assert client.get('/api/v1/patients/doctor',headers=headers).json['doctor'] is None
    for _ in range(2):
        assert client.post('/api/v1/patients/connect-doctor',json={'referral_id':referral_id},headers=headers).status_code == 200
    assert client.post('/api/v1/patients/connect-doctor',json={'referral_id':second},headers=headers).status_code == 409
    other = client.post('/api/v1/doctors/login',json={'email':'other@example.com','password':PASSWORD})
    assert client.get('/api/v1/doctors/patients',headers=bearer(other)).json['total'] == 0
    assert client.post('/api/v1/patients/connect-doctor',json={'referral_id':referral_id}).status_code == 401


def test_referral_stable_when_name_changes(app):
    doctor_id, referral_id = doctor(app)
    with app.app_context():
        db().get(User,doctor_id).full_name = 'Dr New Name'
        db().commit()
        assert db().get(DoctorProfile,doctor_id).referral_id == referral_id
