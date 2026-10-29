from datetime import timedelta
from unittest.mock import patch
import pytest
import jwt
from sqlalchemy import select, update
from core.database import db
from core.models import User, OTPChallenge, EmailNotification, UserSession, now
from core.security import decode_token
from services.otp import otp_code
from conftest import create_account

PASSWORD = 'Password8!'


def registration(role='patients', email='user@example.com'):
    data = dict(full_name='Example User', email=email, mobile_number='+919876543210',
                password=PASSWORD, confirm_password=PASSWORD)
    if role == 'doctors':
        data.update(qualification='MBBS', medical_registration_number='TEST-123', registering_council='Test Council')
    return data


def code(app, response):
    with app.app_context():
        claims = decode_token(response.json['challenge_token'], 'challenge')
        return otp_code(claims['cid'])


def verify(app, client, response, role='patients', login=False, headers=None):
    if login:
        assert response.status_code == 200 and 'challenge_token' not in response.json
        return response
    return client.post(f'/api/v1/{role}/'+('verify-login-otp' if login else 'verify-email'),
                       json={'challenge_token': response.json['challenge_token'], 'otp': code(app, response)}, headers=headers or {})


def bearer(response):
    return {'Authorization': 'Bearer '+response.json['access_token']}


def submit_doctor_profile(client, verified):
    return client.post('/api/v1/doctors/setup-profile', json={
        'setup_token': verified.json['setup_token'], 'qualification': 'MBBS',
        'medical_registration_number': 'TEST-123', 'registering_council': 'Test Council',
        'address': 'Doctor Street, Delhi 110001', 'clinic_address': 'Clinic Road, Delhi 110002',
        'years_of_experience': 5})


def super_login(app, client):
    create_account(app)
    return client.post('/api/v1/superadmin/login', json={'username': 'superadmin', 'password': PASSWORD})


def test_health_docs_and_validation(client):
    assert client.get('/health').status_code == 200
    spec = client.get('/api/openapi.json').json
    assert len(spec['paths']) >= 40
    assert client.get('/api/docs').status_code == 200
    result = client.post('/api/v1/patients/register', json={'password': 'secret'})
    assert result.status_code == 422
    assert b'secret' not in result.data


def test_patient_signup_jwt_profile_and_password_login(app, client):
    registered = client.post('/api/v1/patients/register', json=registration())
    assert registered.status_code == 202 and 'access_token' not in registered.json
    session = verify(app, client, registered)
    assert session.status_code == 200
    assert session.json['user']['public_id'].startswith('C')
    me = client.get('/api/v1/patients/me', headers=bearer(session))
    assert me.status_code == 200 and me.json['user']['email_verified']
    assert 'password_hash' not in str(me.json)
    step = client.post('/api/v1/patients/login', json={'email': 'user@example.com', 'password': PASSWORD})
    assert step.status_code == 200 and 'access_token' in step.json
    assert verify(app, client, step, login=True).status_code == 200


def test_admin_full_approval_and_password_login(app, client):
    super_session = super_login(app, client)
    registered = client.post('/api/v1/admin/register', json=registration('admin', 'admin@example.com'))
    verified = verify(app, client, registered, 'admin')
    assert verified.status_code == 202
    assert verified.json['user']['public_id'].startswith('A')
    credentials = {'email': 'admin@example.com', 'password': PASSWORD}
    assert client.post('/api/v1/admin/login', json=credentials).status_code == 403
    pending = client.get('/api/v1/superadmin/admin-requests', headers=bearer(super_session))
    assert pending.json['total'] == 1
    target = verified.json['user']['public_id']
    assert client.post(f'/api/v1/superadmin/admins/{target}/approve', headers=bearer(super_session)).status_code == 200
    step = client.post('/api/v1/admin/login', json=credentials)
    session = verify(app, client, step, 'admin', login=True)
    assert session.status_code == 200
    assert client.get('/api/v1/admin/dashboard', headers=bearer(session)).status_code == 200
    assert client.get('/api/v1/superadmin/dashboard', headers=bearer(session)).status_code == 403
    assert client.post(f'/api/v1/superadmin/admins/{target}/approve', headers=bearer(super_session)).status_code == 409


def test_doctor_review_and_approval_email_queue(app, client):
    create_account(app, 'ADMIN', 'admin@example.com')
    login = client.post('/api/v1/admin/login', json={'email': 'admin@example.com', 'password': PASSWORD})
    admin = verify(app, client, login, 'admin', login=True)
    registered = client.post('/api/v1/doctors/register', json=registration('doctors', 'doctor@example.com'))
    verified = verify(app, client, registered, 'doctors')
    credentials = {'email': 'doctor@example.com', 'password': PASSWORD}
    assert client.post('/api/v1/doctors/login', json=credentials).json['requires_profile_setup']
    assert submit_doctor_profile(client, verified).status_code == 202
    target = verified.json['user']['public_id']
    assert client.post(f'/api/v1/admin/doctors/{target}/approve', headers=bearer(admin)).status_code == 200
    session = client.post('/api/v1/doctors/login', json=credentials)
    assert session.status_code == 200
    assert client.get('/api/v1/doctors/me', headers=bearer(session)).json['user']['doctor']['verification_status'] == 'APPROVED'
    with app.app_context():
        assert db().scalar(select(EmailNotification).where(EmailNotification.template == 'doctor_approved'))


def test_rejection_and_doctor_resubmission(app, client):
    create_account(app, 'ADMIN', 'admin@example.com')
    step = client.post('/api/v1/admin/login', json={'email': 'admin@example.com', 'password': PASSWORD})
    admin = verify(app, client, step, 'admin', login=True)
    registered = client.post('/api/v1/doctors/register', json=registration('doctors', 'doctor@example.com'))
    verified = verify(app, client, registered, 'doctors')
    assert submit_doctor_profile(client, verified).status_code == 202
    target = verified.json['user']['public_id']
    assert client.post(f'/api/v1/admin/doctors/{target}/reject', json={'reason': 'Need valid certificate'}, headers=bearer(admin)).status_code == 200
    result = client.post('/api/v1/doctors/approval-status', json={'email': 'doctor@example.com', 'password': PASSWORD})
    assert result.json['rejection_reason'] == 'Need valid certificate'
    data = {'email': 'doctor@example.com', 'password': PASSWORD, 'qualification': 'MBBS',
            'medical_registration_number': 'NEW-123', 'registering_council': 'Test Council'}
    assert client.post('/api/v1/doctors/resubmit', json=data).status_code == 202


def test_otp_attempt_limit_no_plaintext_storage(app, client):
    registered = client.post('/api/v1/patients/register', json=registration())
    correct = code(app, registered)
    wrong = '000000' if correct != '000000' else '111111'
    for _ in range(5):
        assert client.post('/api/v1/patients/verify-email', json={'challenge_token': registered.json['challenge_token'], 'otp': wrong}).status_code == 400
    assert verify(app, client, registered).status_code == 400
    with app.app_context():
        item = app.extensions['pending_signups'].all()[0]
        assert item['attempts'] == 5 and correct not in item['code_hash']
        assert db().scalar(select(User)) is None
        assert db().scalar(select(OTPChallenge)) is None
        assert db().scalar(select(EmailNotification)) is None


def test_otp_expiry_resend_and_replay(app, client):
    registered = client.post('/api/v1/patients/register', json=registration())
    data = {'challenge_token': registered.json['challenge_token']}
    assert client.post('/api/v1/patients/resend-otp', json=data).status_code == 429
    with app.app_context():
        import time
        item = app.extensions['pending_signups'].all()[0]
        item['sent_at'] = time.time() - 61
        item['expires_at'] = time.time() - 1
    assert verify(app, client, registered).status_code == 400
    resent = client.post('/api/v1/patients/resend-otp', json=data)
    assert resent.status_code == 200
    assert verify(app, client, registered).status_code == 400
    assert verify(app, client, resent).status_code == 200
    assert verify(app, client, resent).status_code == 400


def test_challenge_not_access_token_and_cross_role(app, client):
    registered = client.post('/api/v1/patients/register', json=registration())
    assert client.get('/api/v1/patients/me', headers={'Authorization': 'Bearer '+registered.json['challenge_token']}).status_code == 401
    assert verify(app, client, registered, 'admin').status_code == 401


def test_refresh_rotation_reuse_revokes_access(app, client):
    session = super_login(app, client)
    old = session.json['refresh_token']
    rotated = client.post('/api/v1/auth/refresh', json={'refresh_token': old})
    assert rotated.status_code == 200 and rotated.json['refresh_token'] != old
    assert client.post('/api/v1/auth/refresh', json={'refresh_token': old}).status_code == 401
    assert client.get('/api/v1/superadmin/me', headers=bearer(rotated)).status_code == 401


def test_logout_revokes_access(app, client):
    session = super_login(app, client)
    assert client.post('/api/v1/auth/logout', headers=bearer(session)).status_code == 200
    assert client.get('/api/v1/superadmin/me', headers=bearer(session)).status_code == 401


def test_suspension_revokes_admin_session(app, client):
    super_session = super_login(app, client)
    create_account(app, 'ADMIN', 'admin@example.com')
    step = client.post('/api/v1/admin/login', json={'email': 'admin@example.com', 'password': PASSWORD})
    admin = verify(app, client, step, 'admin', login=True)
    target = admin.json['user']['public_id']
    assert client.post(f'/api/v1/superadmin/admins/{target}/suspend', headers=bearer(super_session)).status_code == 200
    assert client.get('/api/v1/admin/me', headers=bearer(admin)).status_code in (401,403)
    assert client.post(f'/api/v1/superadmin/admins/{target}/reactivate', headers=bearer(super_session)).status_code == 200
    assert client.get('/api/v1/admin/me', headers=bearer(admin)).status_code == 401


def test_initial_superadmin_password_rotation_and_seed_idempotency(app, client):
    from scripts.seed_superadmin import seed
    with app.app_context():
        account, created = seed('superadmin', 'super@example.com', 'superadmin@2026')
        assert created
        original = account.password_hash
        assert not seed('superadmin', 'super@example.com', 'OtherPassword8!')[1]
        assert account.password_hash == original
    step = client.post('/api/v1/superadmin/login', json={'username': 'superadmin', 'password': 'superadmin@2026'})
    assert step.status_code == 202 and 'access_token' not in step.json
    changed = client.post('/api/v1/auth/initial-password', json={'challenge_token': step.json['challenge_token'],
             'current_password': 'superadmin@2026', 'new_password': 'NewPassword8!', 'confirm_password': 'NewPassword8!'})
    assert changed.status_code == 200
    assert client.get('/api/v1/superadmin/me', headers=bearer(changed)).status_code == 200
    assert client.post('/api/v1/superadmin/login', json={'username': 'superadmin', 'password': 'superadmin@2026'}).status_code == 401


def test_password_reset_revokes_sessions(app, client):
    session = super_login(app, client)
    email = session.json['user']['email']
    step = client.post('/api/v1/auth/forgot-password', json={'email': email})
    reset = client.post('/api/v1/auth/reset-password', json={'challenge_token': step.json['challenge_token'],
             'otp': code(app, step), 'new_password': 'NewPassword8!', 'confirm_password': 'NewPassword8!'})
    assert reset.status_code == 200
    assert client.get('/api/v1/superadmin/me', headers=bearer(session)).status_code == 401


def test_unknown_reset_same_shape(client):
    response = client.post('/api/v1/auth/forgot-password', json={'email': 'absent@example.com'})
    assert response.status_code == 202 and 'challenge_token' in response.json


def test_cookie_transport_csrf_and_no_json_token_leak(app, client):
    create_account(app)
    credentials = {'username': 'superadmin', 'password': PASSWORD}
    assert client.post('/api/v1/superadmin/login', json=credentials, headers={'X-Auth-Transport': 'cookie'}).status_code == 403
    headers = {'X-Auth-Transport': 'cookie', 'X-Requested-With': 'FamilyCare', 'Origin': 'http://localhost:3000'}
    session = client.post('/api/v1/superadmin/login', json=credentials, headers=headers)
    assert session.status_code == 200 and 'access_token' not in session.json and 'refresh_token' not in session.json
    assert client.get('/api/v1/superadmin/me').status_code == 200
    assert client.post('/api/v1/auth/refresh', headers=headers).status_code == 403
    headers['X-CSRF-Token'] = session.json['csrf_token']
    refreshed = client.post('/api/v1/auth/refresh', headers=headers)
    assert refreshed.status_code == 200
    headers['X-CSRF-Token'] = refreshed.json['csrf_token']
    assert client.post('/api/v1/auth/logout', headers=headers).status_code == 200


def test_password_policy_and_forbidden_fields(client):
    data = registration()
    data['password'] = data['confirm_password'] = '12345678'
    assert client.post('/api/v1/patients/register', json=data).status_code == 202
    data['role'] = 'SUPERADMIN'
    assert client.post('/api/v1/patients/register', json=data).status_code == 422
    data.pop('role'); data['password'] = data['confirm_password'] = '1234567'
    assert client.post('/api/v1/patients/register', json=data).status_code == 422


def test_invalid_expired_jwt_and_sql_injection(app, client):
    session = super_login(app, client)
    token = session.json['access_token']
    with app.app_context():
        claims = decode_token(token, 'access'); claims['exp'] = now() - timedelta(seconds=10)
        expired = jwt.encode(claims, app.config['JWT_SECRET_KEY'], algorithm='HS256')
    for value in ('bad.token.value', expired):
        assert client.get('/api/v1/superadmin/me', headers={'Authorization': 'Bearer '+value}).status_code == 401
    assert client.post('/api/v1/superadmin/login', json={'username': "' OR 1=1 --", 'password': PASSWORD}).status_code == 401


def test_mail_worker_sends_and_is_not_repeated(app, client):
    from services.email import process_one
    registered = client.post('/api/v1/patients/register', json=registration())
    verify(app, client, registered)
    client.post('/api/v1/auth/forgot-password', json={'email': 'user@example.com'})
    with app.app_context(), patch('services.email.send_mail') as sender:
        assert process_one()
        assert sender.call_count == 1
        assert not process_one()


def test_mail_worker_retries(app, client):
    from services.email import process_one
    registered = client.post('/api/v1/patients/register', json=registration())
    verify(app, client, registered)
    client.post('/api/v1/auth/forgot-password', json={'email': 'user@example.com'})
    with app.app_context(), patch('services.email.send_mail', side_effect=OSError):
        assert process_one()
        item = db().scalar(select(EmailNotification))
        assert item.attempts == 1 and item.status == 'PENDING' and item.available_at > now()


def test_doctor_required_registration_and_duplicate_constraints(app, client):
    data = registration('doctors', 'doctor1@example.com')
    bad = dict(data); bad['medical_registration_number'] = '!invalid'
    assert client.post('/api/v1/doctors/register', json=bad).status_code == 422
    registered = client.post('/api/v1/doctors/register', json=data)
    assert registered.status_code == 202
    assert verify(app, client, registered, 'doctors').status_code == 202
    data['email'] = 'doctor2@example.com'
    assert client.post('/api/v1/doctors/register', json=data).status_code == 409


def test_change_password_and_session_revocation(app, client):
    session = super_login(app, client)
    sessions = client.get('/api/v1/auth/sessions', headers=bearer(session))
    assert len(sessions.json['items']) == 1
    changed = client.post('/api/v1/auth/change-password', headers=bearer(session), json={
        'current_password': PASSWORD, 'new_password': 'ChangedPassword8!', 'confirm_password': 'ChangedPassword8!'})
    assert changed.status_code == 200
    assert client.get('/api/v1/superadmin/me', headers=bearer(session)).status_code == 401


def test_wrong_jwt_issuer_audience_and_type(app, client):
    session = super_login(app, client)
    with app.app_context():
        claims = decode_token(session.json['access_token'], 'access')
    for field, value in [('aud', 'other-client'), ('iss', 'supabase'), ('type', 'challenge')]:
        modified = dict(claims); modified[field] = value
        token = jwt.encode(modified, app.config['JWT_SECRET_KEY'], algorithm='HS256')
        assert client.get('/api/v1/superadmin/me', headers={'Authorization': 'Bearer '+token}).status_code == 401


def test_otp_restart_after_attempt_exhaustion(app, client):
    registered = client.post('/api/v1/patients/register', json=registration())
    with app.app_context():
        import time
        item = app.extensions['pending_signups'].all()[0]
        item['attempts'] = 5
        item['sent_at'] = time.time() - 61
    restarted = client.post('/api/v1/auth/request-email-verification', json={'email': 'user@example.com', 'password': PASSWORD})
    assert restarted.status_code == 202
    assert verify(app, client, restarted).status_code == 200


def test_rate_limit_returns_json_429(app):
    from app import create_app
    limited = create_app(dict(TESTING=True, DATABASE_URL='', JWT_SECRET_KEY='x'*48,
                              OTP_HMAC_SECRET='y'*48, RATELIMIT_STORAGE_URI='memory://',
                              RATELIMIT_ENABLED=True, APP_ENV='development'))
    local = limited.test_client()
    for _ in range(10):
        assert local.post('/api/v1/superadmin/login', json={'username': 'rate-test', 'password': PASSWORD}).status_code == 503
    result = local.post('/api/v1/superadmin/login', json={'username': 'rate-test', 'password': PASSWORD})
    assert result.status_code == 429 and 'error' in result.json


@pytest.mark.parametrize('role', ['patients', 'admin', 'doctors'])
def test_signup_writes_nothing_until_verified(app, client, role, mock_signup_mail):
    registered = client.post(f'/api/v1/{role}/register', json=registration(role))
    assert registered.status_code == 202
    assert registered.json['email_status'] == 'sent'
    assert registered.json['user_id'] is None
    assert mock_signup_mail.call_count == 1
    with app.app_context():
        from core.database import Base
        from sqlalchemy import func
        for table in Base.metadata.sorted_tables:
            assert db().scalar(select(func.count()).select_from(table)) == 0
    verified = verify(app, client, registered, role)
    assert verified.status_code == (200 if role == 'patients' else 202)
    with app.app_context():
        assert db().scalar(select(User)).email_verified
    assert verify(app, client, registered, role).status_code == 400


def test_signup_smtp_failure_has_no_database_records(app, client, mock_signup_mail):
    mock_signup_mail.side_effect = OSError('delivery failed')
    registered = client.post('/api/v1/patients/register', json=registration())
    assert registered.status_code == 503
    assert registered.json['error']['code'] == 'email_delivery_failed'
    assert 'challenge_token' not in registered.json
    with app.app_context():
        assert not app.extensions['pending_signups'].all()
        assert db().scalar(select(User)) is None


def test_failed_resend_preserves_previous_otp(app, client, mock_signup_mail):
    import time
    registered = client.post('/api/v1/patients/register', json=registration())
    with app.app_context():
        app.extensions['pending_signups'].all()[0]['sent_at'] = time.time() - 61
    mock_signup_mail.side_effect = OSError('SMTP unavailable')
    resent = client.post('/api/v1/patients/resend-otp', json={
        'challenge_token': registered.json['challenge_token']})
    assert resent.status_code == 503
    assert verify(app, client, registered).status_code == 200


def test_pending_cache_expiry_requires_new_registration(app, client):
    import time
    registered = client.post('/api/v1/patients/register', json=registration())
    with app.app_context():
        app.extensions['pending_signups'].all()[0]['retain_until'] = time.time() - 1
    assert verify(app, client, registered).status_code == 400
    assert client.post('/api/v1/patients/register', json=registration()).status_code == 202


def test_concurrent_pending_verification_creates_one_user(app, client):
    from concurrent.futures import ThreadPoolExecutor
    registered = client.post('/api/v1/patients/register', json=registration())
    body = {'challenge_token': registered.json['challenge_token'], 'otp': code(app, registered)}
    def attempt(_):
        with app.test_client() as local:
            return local.post('/api/v1/patients/verify-email', json=body).status_code
    with ThreadPoolExecutor(max_workers=4) as workers:
        statuses = list(workers.map(attempt, range(4)))
    assert sorted(statuses) == [200, 400, 400, 400]
    with app.app_context():
        assert len(db().scalars(select(User)).all()) == 1


def test_doctor_credentials_checked_again_at_verification(app, client):
    data = registration('doctors', 'first@example.com')
    first = client.post('/api/v1/doctors/register', json=data)
    data['email'] = 'second@example.com'
    second = client.post('/api/v1/doctors/register', json=data)
    assert second.status_code == 202
    assert verify(app, client, first, 'doctors').status_code == 202
    assert verify(app, client, second, 'doctors').status_code == 409
    with app.app_context():
        assert len(db().scalars(select(User)).all()) == 1


def test_admin_patient_directory_is_role_protected(app, client):
    create_account(app, 'ADMIN', 'admin-directory@example.com')
    create_account(app, 'PATIENT', 'patient-directory@example.com')
    assert client.get('/api/v1/admin/patients').status_code == 401
    step = client.post('/api/v1/admin/login', json={'email':'admin-directory@example.com','password':PASSWORD})
    session = verify(app, client, step, 'admin', login=True)
    result = client.get('/api/v1/admin/patients?status=APPROVED&per_page=1', headers=bearer(session))
    assert result.status_code == 200 and result.json['total'] == 1
    assert result.json['items'][0]['email'] == 'patient-directory@example.com'
    patient_step = client.post('/api/v1/patients/login',json={'email':'patient-directory@example.com','password':PASSWORD})
    patient_session = verify(app,client,patient_step,login=True)
    assert client.get('/api/v1/admin/patients',headers=bearer(patient_session)).status_code == 403


@pytest.mark.parametrize('role,path', [('ADMIN','admin'),('PATIENT','patients'),('DOCTOR','doctors'),('SUPERADMIN','superadmin')])
def test_all_roles_email_password_login_without_otp(app,client,role,path):
    email = path+'-login@example.com'
    create_account(app,role,email)
    response=client.post('/api/v1/'+path+'/login',json={'email':email,'password':PASSWORD})
    assert response.status_code == 200 and response.json['user']['role'] == role
    assert 'challenge_token' not in response.json and 'requires_otp' not in response.json
    with app.app_context():
        assert db().scalar(select(OTPChallenge)) is None
        assert db().scalar(select(EmailNotification)) is None
    assert client.post('/api/v1/'+path+'/login',json={'email':email,'password':'WrongPassword8!'}).status_code == 401


def test_retired_login_otp_endpoint(client):
    response=client.post('/api/v1/admin/verify-login-otp',json={'challenge_token':'old','otp':'123456'})
    assert response.status_code == 410
