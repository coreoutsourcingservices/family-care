from test_vaccination_management import setup_staff
from services.vaccination_starters import UIP,IAP


def test_starters_roles_idempotency_and_unpublished_boundary(app,client):
    admin,doctor,doctor_id=setup_staff(app,client)
    assert len(UIP)==26 and len(IAP)==18
    assert client.post('/api/v1/admin/vaccination/import-uip',headers=doctor,json={}).status_code==403
    assert client.post('/api/v1/doctors/vaccination/import-iap',headers=admin,json={}).status_code==403
    result=client.post('/api/v1/admin/vaccination/import-uip',headers=admin,json={})
    assert result.status_code==200,result.json
    assert result.json['created']==26
    assert client.post('/api/v1/admin/vaccination/import-uip',headers=admin,json={}).json['skipped']==26
    result=client.post('/api/v1/doctors/vaccination/import-iap',headers=doctor,json={})
    assert result.status_code==200,result.json
    assert result.json['created']==18
    assert client.post('/api/v1/doctors/vaccination/import-iap',headers=doctor,json={}).json['skipped']==18
    rows=client.get('/api/v1/doctors/vaccination/schedules?per_page=100',headers=doctor).json['items']
    assert len(rows)==18 and all(r['status']=='DRAFT' and r['schedule_type']=='IAP' for r in rows)
    assert client.get('/api/v1/vaccination-schedules?schedule_type=UIP').json['total']==0
    assert client.get('/api/v1/vaccination-schedules?schedule_type=IAP').json['total']==0
    own=rows[0]
    assert client.post('/api/v1/doctors/vaccination/schedules/'+own['id']+'/submit-review',headers=doctor,json={'reviewer_id':doctor_id}).status_code in (403,422)
    uip=client.get('/api/v1/admin/vaccination/schedules?per_page=100',headers=admin).json['items']
    uip=next(r for r in uip if r['schedule_type']=='UIP')
    assert client.put('/api/v1/doctors/vaccination/schedules/'+uip['id'],headers=doctor,json={}).status_code==403


def test_child_review_is_connected_scoped_and_invalidated(app,client,monkeypatch):
    from datetime import date
    from core.database import db
    from core.models import CareProfile
    from test_vaccination_management import draft,approve
    from test_care import patient,create_profile
    monkeypatch.setattr('services.vaccination.today',lambda:date(2026,10,28))
    admin,doctor,doctor_id=setup_staff(app,client)
    row,_=draft(client,admin,eligibility={'requires_clinical_review':True},age_unit='days',age_start=7,age_end=7,reminders={'before_days':[7,1],'overdue_days':[1,7],'language':'hi'})
    approve(client,admin,doctor,doctor_id,row)
    owner=patient(app,client);child=create_profile(client,owner,date_of_birth='2026-10-28')
    base='/api/v1/children/'+child
    path='/api/v1/doctors/care-profiles/'+child+'/vaccination-plan'
    context={'country':'IN','history_status':'PARENT_REPORTED'}
    client.put(base+'/vaccination-context',headers=owner,json=context)
    assert client.get(path,headers=doctor).status_code==404
    with app.app_context():
        db().get(CareProfile,child).referred_doctor_id=doctor_id;db().commit()
    assert client.get(path,headers=doctor).status_code==200
    assert client.get(base+'/vaccinations',headers=owner).json['items'][0]['display_status']=='Doctor Review'
    assert client.get(base+'/reminders',headers=owner).json['total']==0
    payload={'schedule_id':row['id'],'decision':'CONFIRM','notes':'Synthetic applicability assessment only.','attestation':True}
    assert client.post(path,headers=owner,json=payload).status_code==403
    assert client.post(path,headers=doctor,json={**payload,'attestation':False}).status_code==422
    assert client.post(path,headers=doctor,json=payload).status_code==200
    dose=client.get(base+'/vaccinations',headers=owner).json['items'][0]
    assert dose['display_status']=='Upcoming' and dose['due_now'] is False
    reminder=client.get(base+'/reminders',headers=owner).json['items'][0]
    assert reminder['days_until_due']==7 and '7' in reminder['message']
    monkeypatch.setattr('services.vaccination.today',lambda:date(2026,11,4))
    assert client.get(base+'/vaccinations',headers=owner).json['items'][0]['due_now'] is True
    monkeypatch.setattr('services.vaccination.today',lambda:date(2026,11,5))
    assert client.get(base+'/vaccinations',headers=owner).json['items'][0]['display_status']=='Overdue'
    assert client.post(path,headers=doctor,json={**payload,'decision':'NOT_APPLICABLE'}).status_code==200
    assert client.get(base+'/vaccinations',headers=owner).json['items'][0]['display_status']=='Not Applicable'
    assert client.get(base+'/reminders',headers=owner).json['total']==0
    client.put(base+'/vaccination-context',headers=owner,json={**context,'state':'Bihar'})
    assert client.get(base+'/vaccinations',headers=owner).json['items'][0]['display_status']=='Doctor Review'
    with app.app_context():
        db().get(CareProfile,child).referred_doctor_id=None;db().commit()
    assert client.get(path,headers=doctor).status_code==404
