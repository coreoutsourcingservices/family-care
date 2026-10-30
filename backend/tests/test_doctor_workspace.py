from datetime import datetime
from core.database import db
from core.models import ChildRecord, uid
from test_care import patient, create_profile
from test_referrals import doctor
from test_workflows import bearer, PASSWORD


def test_doctor_records_are_read_only_and_limited_to_connected_profiles(app, client):
    _, referral = doctor(app)
    patient_headers = patient(app, client)
    shared = create_profile(client, patient_headers, referral_id=referral)
    private = create_profile(client, patient_headers)
    with app.app_context():
        for profile_id, title, deleted in [(shared, 'Shared care note', False), (private, 'Private care note', False), (shared, 'Removed entry', True)]:
            db().add(ChildRecord(id=uid(), profile_id=profile_id, kind='care',
                data=dict(title=title, date='2026-01-01', notes='Family note'),
                deleted_at=datetime(2026, 1, 2) if deleted else None))
        db().commit()
    headers = bearer(client.post('/api/v1/doctors/login', json=dict(email='rahul@example.com', password=PASSWORD)))
    result = client.get(f'/api/v1/doctors/care-profiles/{shared}/records', headers=headers)
    assert result.status_code == 200
    assert result.json['total'] == 1
    assert result.json['items'][0]['title'] == 'Shared care note'
    assert result.json['items'][0]['verification_status'] == 'PARENT_REPORTED'
    assert client.get(f'/api/v1/doctors/care-profiles/{private}/records', headers=headers).status_code == 404
    assert client.get(f'/api/v1/doctors/care-profiles/{shared}/records', headers=patient_headers).status_code == 403
    assert client.get(f'/api/v1/doctors/care-profiles/{shared}/records').status_code == 401
    assert client.post(f'/api/v1/doctors/care-profiles/{shared}/records', headers=headers, json={}).status_code == 405
    assert client.get(f'/api/v1/doctors/care-profiles/{shared}/records?per_page=101', headers=headers).status_code == 400
