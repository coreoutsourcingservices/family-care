from datetime import date
from sqlalchemy import select
from core.database import db
from core.models import ChildRecord, ChildRecordRevision, CareProfile
from test_care import patient, create_profile


def test_child_records_persist_and_remain_private(app, client):
    owner = patient(app, client)
    child = create_profile(client, owner)
    base = '/api/v1/children/' + child
    record = dict(title='Measured at clinic', date='2026-10-01', weight='22.4', height='118')
    result = client.post(base+'/growth', headers=owner, json=record)
    assert result.status_code == 201, result.json
    record_id = result.json['record']['id']
    assert client.get(base+'/growth', headers=owner).json['items'][0]['weight'] == '22.4'
    updated = client.patch(base+'/growth/'+record_id, headers=owner, json={'weight':'22.8'})
    assert updated.status_code == 200, updated.json
    assert updated.json['record']['weight'] == '22.8'
    assert client.get(base+'/dashboard', headers=owner).json['counts']['growth'] == 1
    assert client.get(base+'/age', headers=owner).json['age']['total_completed_months'] >= 0
    stranger = patient(app, client, 'other@example.com')
    for suffix in ('/growth', '/records', '/age', '/dashboard', '/health-guide', '/reminders'):
        assert client.get(base+suffix, headers=stranger).status_code == 404
    assert client.post(base+'/growth', headers=stranger, json=record).status_code == 404
    assert client.delete(base+'/growth/'+record_id, headers=stranger).status_code == 404
    assert client.patch(base+'/growth/'+record_id, headers=stranger, json={'weight':'10'}).status_code == 404
    assert client.get(base+'/growth').status_code == 401
    assert client.delete(base+'/growth/'+record_id, headers=owner).status_code == 200
    assert client.get(base+'/growth', headers=owner).json['total'] == 0
    with app.app_context():
        assert db().get(ChildRecord, record_id).deleted_at is not None
        assert len(db().scalars(select(ChildRecordRevision).where(ChildRecordRevision.record_id == record_id)).all()) == 3


def test_child_validation_and_unavailable_clinical_content(app, client):
    owner = patient(app, client)
    child = create_profile(client, owner)
    base = '/api/v1/children/' + child
    for payload in (
        dict(title=' ', date='2026-10-01', weight='20', height='110'),
        dict(title='Measurement', date='2026-10-01', weight='NaN', height='110'),
        dict(title='Measurement', date='2026-10-01'),
        dict(title='Measurement', date='2100-10-01', weight='20', height='110'),
        dict(title='Measurement', date='2000-10-01', weight='20', height='110'),
    ):
        assert client.post(base+'/growth', headers=owner, json=payload).status_code == 422
    assert client.post(base+'/vaccinations/history', headers=owner, json={
        'title':'Reported dose', 'date':'2100-10-01', 'status':'Completed'}).status_code == 422
    for suffix in ('/vaccinations?schedule_type=UIP', '/vaccinations?schedule_type=IAP', '/health-guide'):
        data = client.get(base+suffix, headers=owner).json
        assert data['status'] == 'NOT_AVAILABLE'
    assert client.get(base+'/vaccinations?schedule_type=unknown', headers=owner).status_code == 422
    assert client.get('/api/v1/vaccines').json['items'] == []
    assert client.get('/api/v1/vaccination-schedules').json['items'] == []


def test_record_reminders_and_preferences_are_per_child(app, client):
    owner = patient(app, client)
    first = create_profile(client, owner)
    second = create_profile(client, owner)
    base = '/api/v1/children/' + first
    r = client.post(base+'/vaccinations/history', headers=owner, json={
        'title':'Doctor-provided date', 'date':'2026-11-01', 'status':'Planned'})
    assert r.status_code == 201, r.json
    reminders = client.get(base+'/reminders', headers=owner).json
    assert reminders['total'] == 1
    assert reminders['items'][0]['delivery_status'] == 'IN_APP_ONLY'
    assert client.get('/api/v1/children/'+second+'/reminders', headers=owner).json['total'] == 0
    assert client.put(base+'/reminder-preferences', headers=owner, json={'in_app':False}).status_code == 200
    assert client.get(base+'/reminders', headers=owner).json['total'] == 0
    assert client.put(base+'/reminder-preferences', headers=owner, json={'in_app':True,'email':True}).status_code == 422
    assert client.post(base+'/consultation-requests', headers=owner, json={
        'title':'Request a visit', 'date':'2026-11-01'}).status_code == 409


def test_child_age_clamps_month_end(app, client, monkeypatch):
    import patient.child_routes as routes
    owner = patient(app, client)
    child = create_profile(client, owner)
    with app.app_context():
        db().get(CareProfile, child).dob = date(2024, 1, 31)
        db().commit()
    monkeypatch.setattr(routes, 'today', lambda: date(2024, 2, 29))
    age = client.get('/api/v1/children/'+child+'/age', headers=owner).json['age']
    assert age['total_completed_months'] == 1
    assert age['remaining_days'] == 0


def test_device_import_is_deduplicated(app, client):
    from core.models import uid
    owner = patient(app, client)
    child = create_profile(client, owner)
    base = '/api/v1/children/'+child+'/care-notes'
    payload = {'title':'A milestone', 'date':'2026-10-01', 'source_id':uid()}
    first = client.post(base, headers=owner, json=payload)
    second = client.post(base, headers=owner, json=payload)
    assert first.status_code == 201
    assert second.status_code == 200
    assert first.json['record']['id'] == second.json['record']['id']
    assert client.get(base, headers=owner).json['total'] == 1


def test_consultation_requests_are_visible_only_to_connected_doctor(app, client):
    from test_referrals import doctor
    from test_workflows import PASSWORD, bearer
    owner = patient(app, client)
    first_id, _ = doctor(app)
    second_id, _ = doctor(app, email='other-doctor@example.com', public_id='D000002')
    child = create_profile(client, owner)
    with app.app_context():
        db().get(CareProfile, child).referred_doctor_id = first_id
        db().commit()
    base = '/api/v1/children/'+child
    result = client.post(base+'/consultation-requests', headers=owner, json={
        'title':'Routine review', 'date':'2026-11-01', 'status':'CONFIRMED'})
    assert result.status_code == 201
    assert result.json['record']['status'] == 'REQUESTED'
    first = bearer(client.post('/api/v1/doctors/login', json={'email':'rahul@example.com','password':PASSWORD}))
    second = bearer(client.post('/api/v1/doctors/login', json={'email':'other-doctor@example.com','password':PASSWORD}))
    assert client.get(base+'/consultation-requests', headers=first).json['total'] == 1
    assert client.get('/api/v1/doctors/consultation-requests', headers=first).json['total'] == 1
    assert client.get(base+'/consultation-requests', headers=second).status_code == 404
    assert client.get('/api/v1/doctors/consultation-requests', headers=second).json['total'] == 0
    assert client.get(base+'/care-notes', headers=first).status_code == 403
    assert client.post(base+'/consultation-requests', headers=first, json={'title':'x','date':'2026-11-01'}).status_code == 403
