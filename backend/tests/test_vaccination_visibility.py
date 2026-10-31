from datetime import date
from core.database import db
from core.models import CareProfile, VaccineSchedule
from test_vaccination_management import setup_staff, draft, approve
from test_care import patient, create_profile


def test_both_programmes_visible_for_every_child_without_doctor_link(app,client,monkeypatch):
    monkeypatch.setattr('services.vaccination.today',lambda:date(2026,10,31))
    admin,_,_=setup_staff(app,client)
    uip,payload=draft(client,admin,age_unit='months',age_start=6,age_end=6,age_label='6 months')
    result=client.post('/api/v1/admin/vaccination/schedules',headers=admin,
        json={**payload,'schedule_type':'IAP'})
    assert result.status_code==201,result.json
    iap=result.json['schedule']
    owner=patient(app,client)
    for dob in ('2026-10-01','2024-02-29','2018-05-14','2014-11-01'):
        child=create_profile(client,owner,date_of_birth=dob)
        for programme,schedule in (('UIP',uip),('IAP',iap)):
            response=client.get(f'/api/v1/children/{child}/vaccinations?schedule_type={programme}&view=all',headers=owner)
            assert response.status_code==200,response.json
            assert response.json['child']['id']==child
            assert response.json['total']==1
            item=response.json['items'][0]
            assert item['id']==schedule['id']
            from services.vaccination import age_date
            assert item['recommended_date']==age_date(date.fromisoformat(dob),6,'months').isoformat()
            assert item['status']=='REVIEW_REQUIRED'
    outsider=patient(app,client,'outside-family@example.com')
    assert client.get(f'/api/v1/children/{child}/vaccinations',headers=outsider).status_code==404


def test_admin_age_plan_shared_with_connected_doctor_and_toggle(app,client):
    admin,reviewer,doctor_id=setup_staff(app,client)
    row,payload=draft(client,admin,age_unit='months',age_start=6,age_end=6,age_label='6 months')
    # Pre-existing imported entries have neither availability key.
    with app.app_context():
        legacy=db().get(VaccineSchedule,row['id'])
        legacy.data={k:v for k,v in legacy.data.items() if k not in ('active','child_visible')};db().commit()
    owner=patient(app,client)
    child=create_profile(client,owner,date_of_birth='2026-01-31')
    other=create_profile(client,owner,date_of_birth='2026-02-28')
    with app.app_context():
        db().get(CareProfile,child).referred_doctor_id=doctor_id;db().commit()
    base='/api/v1/children/'+child
    plan='/api/v1/doctors/care-profiles/'+child+'/vaccination-plan'
    item=client.get(base+'/vaccinations',headers=owner).json['items'][0]
    assert item['recommended_date']=='2026-07-31'
    assert item['status']=='REVIEW_REQUIRED' and item['publication_status']=='DRAFT'
    assert client.get(plan,headers=reviewer).json['UIP']['items']==[{k:v for k,v in item.items() if k!='views'}]
    assert client.get('/api/v1/children/'+other+'/vaccinations',headers=owner).json['items'][0]['recommended_date']=='2026-08-28'
    assert client.get('/api/v1/doctors/care-profiles/'+other+'/vaccination-plan',headers=reviewer).status_code==404
    assert client.get(base+'/reminders',headers=owner).json['total']==0
    decision={'schedule_id':row['id'],'decision':'NOT_APPLICABLE','notes':'Synthetic child-specific exclusion for testing.','attestation':True}
    assert client.post(plan,headers=reviewer,json=decision).status_code==200
    assert client.get(base+'/vaccinations',headers=owner).json['items'][0]['status']=='NOT_APPLICABLE'
    assert client.get('/api/v1/children/'+other+'/vaccinations',headers=owner).json['items'][0]['status']=='REVIEW_REQUIRED'
    path='/api/v1/admin/vaccination/schedules/'+row['id']+'/visibility'
    assert client.patch(path,headers=owner,json={'active':False}).status_code==403
    for active in (False,True,False,True):
        assert client.patch(path,headers=admin,json={'active':active}).status_code==200
        assert client.get(base+'/vaccinations',headers=owner).json['total']==int(active)
        assert client.get(plan,headers=reviewer).json['UIP']['total']==int(active)
    vaccine_path='/api/v1/admin/vaccination/vaccines/'+row['vaccine_id']
    catalog=dict(code='TEST',name_en='Synthetic vaccine',category='Government',protects_against='Test only',active=False)
    assert client.put(vaccine_path,headers=admin,json=catalog).status_code==200
    assert client.get(base+'/vaccinations',headers=owner).json['total']==0
    catalog['active']=True
    assert client.put(vaccine_path,headers=admin,json=catalog).status_code==200
    approve(client,admin,reviewer,doctor_id,row)
    assert client.patch(path,headers=admin,json={'active':False}).status_code==200
    assert client.get(base+'/vaccinations',headers=owner).json['total']==0
    assert client.patch(path,headers=admin,json={'active':True}).status_code==200
    assert client.get(base+'/vaccinations',headers=owner).json['total']==1
