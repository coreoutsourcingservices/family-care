import base64
from unittest.mock import patch
from requests import Response
from pywebpush import WebPushException
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import serialization
from sqlalchemy import select
from core.database import db
from core.models import User
from doctor.notification_models import DoctorNotification, DoctorPushSubscription, DoctorPushDelivery
from doctor.notifications import notification_token, queue_notification, deliver_pending
from test_referrals import doctor
from test_care import patient, create_profile
from test_workflows import bearer, PASSWORD


def headers(app, user_id):
    with app.app_context():
        return {'Authorization': 'Bearer ' + notification_token(db().get(User, user_id))}


def subscription():
    point = ec.generate_private_key(ec.SECP256R1()).public_key().public_bytes(serialization.Encoding.X962, serialization.PublicFormat.UncompressedPoint)
    b64 = lambda value: base64.urlsafe_b64encode(value).rstrip(b'=').decode()
    return dict(endpoint='https://fcm.googleapis.com/fcm/send/isolated-test-endpoint', keys=dict(auth=b64(b'0123456789abcdef'), p256dh=b64(point)))


def push_config(app):
    app.config.update(PUSH_VAPID_PRIVATE_KEY='unused-test-private-key', PUSH_VAPID_PUBLIC_KEY='unused-test-public-key', PUSH_VAPID_SUBJECT='mailto:test@example.com')


def test_inbox_ownership_read_status_and_limited_token(app, client):
    first, _ = doctor(app)
    second, _ = doctor(app, email='other@example.com', public_id='D000002')
    with app.app_context():
        queue_notification(first, 'patient_connected', 'test-event')
        queue_notification(first, 'patient_connected', 'test-event')
        db().commit()
    first_headers, second_headers = headers(app, first), headers(app, second)
    result = client.get('/api/v1/doctors/notifications', headers=first_headers)
    assert result.status_code == 200 and result.json['unread'] == 1 and result.json['total'] == 1
    item = result.json['items'][0]
    assert client.get('/api/v1/doctors/notifications', headers=second_headers).json['items'] == []
    assert client.post(f"/api/v1/doctors/notifications/{item['id']}/read", headers=second_headers, json={}).status_code == 404
    assert client.post(f"/api/v1/doctors/notifications/{item['id']}/read", headers=first_headers, json={}).status_code == 200
    assert client.get('/api/v1/doctors/notifications', headers=first_headers).json['unread'] == 0
    assert client.get('/api/v1/doctors/me', headers=first_headers).status_code == 401
    assert client.get('/api/v1/doctors/notifications').status_code == 401


def test_push_subscription_validation_delivery_and_expiry(app, client):
    user_id, _ = doctor(app)
    auth = headers(app, user_id)
    push_config(app)
    data = subscription()
    for endpoint in ('http://localhost:5001/private', 'https://127.0.0.1/private', 'https://fcm.googleapis.com.evil.invalid/push', 'https://fcm.googleapis.com:8080/push'):
        assert client.post('/api/v1/doctors/notifications/subscriptions', headers=auth, json={**data, 'endpoint': endpoint}).status_code == 422
    assert client.post('/api/v1/doctors/notifications/subscriptions', headers=auth, json={**data, 'keys': {'auth': 'bad', 'p256dh': 'bad'}}).status_code == 422
    assert client.post('/api/v1/doctors/notifications/subscriptions', headers=auth, json=data).status_code == 201
    assert client.post('/api/v1/doctors/notifications/subscriptions', headers=auth, json=data).status_code == 201
    with app.app_context():
        queue_notification(user_id, 'consultation_requested', 'request:1')
        db().commit()
        with patch('pywebpush.webpush') as send:
            assert deliver_pending() == 1
            assert deliver_pending() == 0
            assert send.call_count == 1
            assert 'patient' not in send.call_args.kwargs['data'].lower()
            assert send.call_args.kwargs['ttl'] == 3600
        assert db().scalar(select(DoctorPushDelivery)).status == 'SENT'
        queue_notification(user_id, 'report_shared', 'report:1')
        db().commit()
        response = Response(); response.status_code = 410
        with patch('pywebpush.webpush', side_effect=WebPushException('Gone', response=response)):
            assert deliver_pending() == 0
        assert db().scalar(select(DoctorPushSubscription)) is None


def test_new_connection_queues_generic_inbox_and_push(app, client):
    user_id, referral = doctor(app)
    push_config(app)
    assert client.post('/api/v1/doctors/notifications/subscriptions', headers=headers(app, user_id), json=subscription()).status_code == 201
    family = patient(app, client)
    create_profile(client, family, referral_id=referral)
    result = client.get('/api/v1/doctors/notifications', headers=headers(app, user_id))
    assert result.json['unread'] == 1
    assert result.json['items'][0]['kind'] == 'patient_connected'
    assert 'Aarav' not in str(result.json)
    with app.app_context():
        assert db().scalar(select(DoctorPushDelivery)).status == 'PENDING'


def test_transient_push_failure_retries_without_repeating_sent_deliveries(app, client):
    user_id, _ = doctor(app)
    push_config(app)
    auth = headers(app, user_id)
    assert client.post('/api/v1/doctors/notifications/subscriptions', headers=auth, json=subscription()).status_code == 201
    with app.app_context():
        queue_notification(user_id, 'profile_submitted', 'submit:1'); db().commit()
        response = Response(); response.status_code = 503
        with patch('pywebpush.webpush', side_effect=WebPushException('Try later', response=response)) as send:
            assert deliver_pending() == 0
            assert deliver_pending() == 0
            assert send.call_count == 1
        item = db().scalar(select(DoctorPushDelivery))
        assert item.status == 'PENDING' and item.attempts == 1
    assert client.delete('/api/v1/doctors/notifications/subscriptions', headers=auth, json={'endpoint': subscription()['endpoint']}).status_code == 200


def test_approved_notification_token_is_revoked_with_its_session(app, client):
    doctor(app)
    login = client.post('/api/v1/doctors/login', json={'email':'rahul@example.com','password':PASSWORD})
    session = bearer(login)
    me = client.get('/api/v1/doctors/me', headers=session)
    notifications = {'Authorization': 'Bearer ' + me.json['notification_token']}
    assert client.get('/api/v1/doctors/notifications', headers=notifications).status_code == 200
    assert client.post('/api/v1/auth/logout', headers=session).status_code == 200
    assert client.get('/api/v1/doctors/notifications', headers=notifications).status_code == 401
