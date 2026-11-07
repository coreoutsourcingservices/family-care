import json
from datetime import timedelta
from uuid import uuid4
import pytest
from sqlalchemy import select, func
from core.database import db
from core.models import CapacityAppointment, EmailNotification
from services.capacity_appointments import today
from services.email import process_one
from test_referrals import doctor
from test_care import patient, create_profile
from test_workflows import PASSWORD, bearer


def setup(app, client, capacity=1):
    doctor_id, referral = doctor(app)
    headers = bearer(client.post('/api/v1/doctors/login', json={'email':'rahul@example.com', 'password':PASSWORD}))
    windows = [dict(id=str(uuid4()), start='10:00', end='12:00', capacity=capacity, days=list(range(7))),
               dict(id=str(uuid4()), start='13:00', end='16:00', capacity=2, days=list(range(7)))]
    response = client.put('/api/v1/doctors/appointment-schedule', json={'version':0,'windows':windows}, headers=headers)
    assert response.status_code == 200, response.json
    return doctor_id, referral, headers, windows


def payload(window, day=None):
    return dict(window_id=window['id'], appointment_date=(day or today()+timedelta(days=1)).isoformat(), request_id=str(uuid4()))


@pytest.mark.parametrize('module', ['child','adult','women'])
def test_connected_profile_booking_capacity_full_next_window_and_date(app, client, module):
    doctor_id, referral, dh, windows = setup(app, client)
    ph = patient(app, client)
    profile = create_profile(client, ph, module=module, referral_id=referral, date_of_birth='2018-01-01' if module=='child' else '1990-01-01')
    path = '/api/v1/patients/profiles/'+profile
    value = payload(windows[0])
    result = client.post(path+'/appointments', json=value, headers=ph)
    assert result.status_code == 201, result.json
    booking = result.json['appointment']
    assert booking['status']=='BOOKED' and booking['email_status']=='PENDING'
    assert client.post(path+'/appointments', json=value, headers=ph).status_code==200
    assert client.post(path+'/appointments', json=payload(windows[0]), headers=ph).status_code==409
    availability = client.get(path+'/appointment-availability?date='+value['appointment_date'], headers=ph).json
    assert availability['doctor']['id']==doctor_id
    assert availability['items'][0]['status']=='FULL'
    assert availability['items'][0]['remaining']==0
    assert availability['items'][1]['remaining']==2
    following = (today()+timedelta(days=2)).isoformat()
    assert client.get(path+'/appointment-availability?date='+following,headers=ph).json['items'][0]['remaining']==1
    other = patient(app, client, 'second-family@example.com')
    other_profile = create_profile(client,other,module=module,referral_id=referral,date_of_birth='2018-01-01' if module=='child' else '1990-01-01')
    other_path='/api/v1/patients/profiles/'+other_profile
    full=client.post(other_path+'/appointments',json=payload(windows[0]),headers=other)
    assert full.status_code==409 and full.json['error']['code']=='window_full'
    assert client.post(other_path+'/appointments',json=payload(windows[1]),headers=other).status_code==201
    assert client.get('/api/v1/doctors/booked-appointments?date='+value['appointment_date'],headers=dh).json['items'][0]['patient_name']
    assert client.get(path+'/appointments',headers=other).status_code in (403,404)
    assert client.patch(path+'/appointments/'+booking['id']+'/status',json={'status':'CANCELLED'},headers=ph).status_code==200
    assert client.post(other_path+'/appointments',json=payload(windows[0]),headers=other).status_code==201
    with app.app_context():
        assert db().scalar(select(func.count()).select_from(CapacityAppointment))==3
        assert db().scalar(select(func.count()).select_from(EmailNotification).where(EmailNotification.template=='appointment_booked'))==3


def test_schedule_validation_version_and_preserving_booked_windows(app,client):
    _,referral,dh,windows=setup(app,client,capacity=2)
    ph=patient(app,client)
    profile=create_profile(client,ph,module='women',referral_id=referral,date_of_birth='1990-01-01')
    assert client.post('/api/v1/patients/profiles/'+profile+'/appointments',json=payload(windows[0]),headers=ph).status_code==201
    endpoint='/api/v1/doctors/appointment-schedule'
    assert client.put(endpoint,json={'version':0,'windows':windows},headers=dh).status_code==409
    assert client.put(endpoint,json={'version':1,'windows':windows[1:]},headers=dh).status_code==409
    overlapping=[dict(windows[0]),dict(windows[1],start='11:00')]
    assert client.put(endpoint,json={'version':1,'windows':overlapping},headers=dh).status_code==422
    for changes in [dict(capacity=True),dict(capacity=0),dict(start='12:00',end='10:00'),dict(days=[True]),dict(days=[])]:
        assert client.put(endpoint,json={'version':1,'windows':[dict(windows[0],**changes)]},headers=dh).status_code==422
    same=[dict(windows[0],capacity=1),windows[1]]
    assert client.put(endpoint,json={'version':1,'windows':same},headers=dh).status_code==200
    assert client.get(endpoint,headers=dh).json['version']==2


def test_connection_required_and_no_arbitrary_doctor_booking(app,client):
    _,referral,dh,windows=setup(app,client)
    _,other_referral=doctor(app,'other-doctor@example.com','D000002')
    ph=patient(app,client)
    profile=create_profile(client,ph,module='women',date_of_birth='1990-01-01')
    path='/api/v1/patients/profiles/'+profile
    assert client.get(path+'/appointment-availability',headers=ph).json['doctor'] is None
    assert client.post(path+'/appointments',json=payload(windows[0]),headers=ph).status_code==409
    other=create_profile(client,ph,module='women',date_of_birth='1989-01-01',referral_id=other_referral)
    assert client.post('/api/v1/patients/profiles/'+other+'/appointments',json=payload(windows[0]),headers=ph).status_code==409
    assert client.get('/api/v1/doctors/appointment-schedule',headers=ph).status_code==403
    assert client.get(path+'/appointment-availability?date=invalid',headers=ph).status_code==422
    assert client.get(path+'/appointments').status_code==401


def test_email_outbox_delivery_retry_and_no_duplicate_message(app,client,monkeypatch):
    _,referral,dh,windows=setup(app,client)
    ph=patient(app,client)
    profile=create_profile(client,ph,module='adult',date_of_birth='1990-01-01',referral_id=referral)
    path='/api/v1/patients/profiles/'+profile+'/appointments'
    value=payload(windows[0])
    booking=client.post(path,json=value,headers=ph)
    assert booking.status_code==201
    assert client.post(path,json=value,headers=ph).status_code==200
    with app.app_context():
        notifications=db().scalars(select(EmailNotification).where(EmailNotification.template=='appointment_booked')).all()
        assert len(notifications)==1
        mail=notifications[0]
        context=json.loads(mail.context_json)
        assert context['appointment_date']==value['appointment_date'] and context['start']=='10:00'
        def fail(*args):raise RuntimeError('Synthetic SMTP unavailable')
        monkeypatch.setattr('services.email.send_mail',fail)
        assert process_one(templates=['appointment_booked'])
        db().refresh(mail)
        assert mail.status=='PENDING' and mail.attempts==1
        from core.models import now
        mail.available_at=now();db().commit()
        sent=[]
        monkeypatch.setattr('services.email.send_mail',lambda *args:sent.append(args))
        assert process_one(templates=['appointment_booked'])
        db().refresh(mail)
        assert mail.status=='SENT' and len(sent)==1
        assert sent[0][0]=='rahul@example.com'
        assert '10:00 - 12:00' in sent[0][2] and 'Asia/Kolkata' in sent[0][2]
        assert not process_one(templates=['appointment_booked'])

def test_fifty_places_fill_only_after_fiftieth_booking(app, client):
    _, referral, dh, windows = setup(app, client, capacity=50)
    windows[0].update(start='08:17', end='10:42')
    assert client.put('/api/v1/doctors/appointment-schedule', json={'version':1,'windows':windows}, headers=dh).status_code == 200
    ph = patient(app, client)
    for index in range(51):
        profile = create_profile(client, ph, module='child', referral_id=referral, date_of_birth='2018-01-01')
        path = '/api/v1/patients/profiles/'+profile
        result = client.post(path+'/appointments', json=payload(windows[0]), headers=ph)
        if index < 50:
            assert result.status_code == 201, result.json
            last_booking = (path, result.json['appointment']['id'])
        else:
            assert result.status_code == 409 and result.json['error']['code'] == 'window_full'
        if index in (48,49):
            availability=client.get(path+'/appointment-availability?date='+payload(windows[0])['appointment_date'],headers=ph).json['items'][0]
            assert availability['remaining'] == 49-index
            assert availability['status'] == ('FULL' if index==49 else 'AVAILABLE')
    path, booking = last_booking
    assert client.patch(path+'/appointments/'+booking+'/status',json={'status':'CANCELLED'},headers=ph).status_code==200
    assert client.get(path+'/appointment-availability?date='+payload(windows[0])['appointment_date'],headers=ph).json['items'][0]['remaining']==1


def test_custom_capacity_above_five_hundred(app, client):
    _, _, dh, _ = setup(app, client, capacity=1000)
    assert client.get('/api/v1/doctors/appointment-schedule',headers=dh).json['windows'][0]['capacity']==1000


def test_consultation_modes_fees_notes_and_attachment_scope(app, client):
    from core.models import CareReport
    doctor_id, referral, dh, windows = setup(app, client)
    settings = '/api/v1/doctors/consultation-settings'
    options = dict(physical_enabled=True, video_enabled=True, physical_fee_paise=50000, video_fee_paise=35000)
    assert client.put(settings, headers=dh, json=options).status_code == 200
    ph = patient(app, client)
    profile = create_profile(client, ph, kind='self', module='adult', date_of_birth='1990-01-01')
    path = '/api/v1/patients/profiles/'+profile
    day = (today()+timedelta(days=1)).isoformat()
    available = client.get(path+'/appointment-availability?date='+day+'&doctor_id='+doctor_id, headers=ph)
    assert available.status_code == 200
    assert available.json['doctor']['consultation_options']['video_fee_paise'] == 35000
    assert 'email' not in available.json['doctor']
    request = {**payload(windows[0]), 'doctor_id':doctor_id, 'mode':'video', 'notes':'Questions for consultation'}
    with app.app_context():
        report=CareReport(profile_id=profile,name='demo.pdf',content_type='application/pdf',size_bytes=5,storage_provider='database',content=b'%PDF-')
        db().add(report);db().commit();report_id=report.id
    request['report_ids']=[report_id]
    changed=client.post(path+'/appointments',headers=ph,json={**request,'expected_fee_paise':1})
    assert changed.status_code==409 and changed.json['error']['code']=='consultation_fee_changed'
    result=client.post(path+'/appointments', headers=ph, json=request)
    assert result.status_code==201,result.json
    booking=result.json['appointment']
    assert booking['details']['fee_paise']==35000
    assert booking['details']['notes']=='Questions for consultation'
    assert booking['documents'][0]['id']==report_id
    assert client.post(path+'/appointments',headers=ph,json=request).status_code==200
    assert client.get('/api/v1/doctors/booked-appointments/'+booking['id']+'/documents/'+report_id,headers=dh).data==b'%PDF-'
    assert client.put(settings,headers=dh,json={**options,'video_enabled':False}).status_code==200
    rejected=client.post(path+'/appointments', headers=ph, json={**payload(windows[1]),'doctor_id':doctor_id,'mode':'video'})
    assert rejected.status_code==422
    assert client.put(settings,headers=dh,json={**options,'video_fee_paise':-1}).status_code==422
    assert client.put(settings,headers=dh,json={**options,'physical_enabled':False,'video_enabled':False}).status_code==422
    foreign=patient(app,client,'foreign@example.com')
    foreign_profile=create_profile(client,foreign,module='adult',date_of_birth='1990-01-01')
    rejected=client.post('/api/v1/patients/profiles/'+foreign_profile+'/appointments',headers=foreign,json={**payload(windows[1]),'doctor_id':doctor_id,'mode':'physical','report_ids':[report_id]})
    assert rejected.status_code==422
    assert client.patch(path+'/appointments/'+booking['id']+'/status',headers=ph,json={'status':'CANCELLED'}).status_code==200
