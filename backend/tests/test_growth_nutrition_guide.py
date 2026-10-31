from datetime import date
from sqlalchemy import select
from core.database import db
from core.models import CareProfile
from test_care import patient,create_profile
from test_vaccination_management import setup_staff


def test_default_active_all_month_and_year_bands(app,client,monkeypatch):
    monkeypatch.setattr('patient.child_routes.today',lambda:date(2026,10,31))
    owner=patient(app,client)
    for month in range(12):
        from services.vaccination import age_date
        dob=age_date(date(2026,10,1),-month,'months')
        child=create_profile(client,owner,date_of_birth=dob.isoformat())
        result=client.get(f'/api/v1/children/{child}/growth-nutrition-guide',headers=owner)
        assert result.status_code==200,result.json
        assert result.json['active'] is True and result.json['status']=='AVAILABLE'
        assert result.json['age_band']['id']==f'month-{month}'
        assert result.json['guide']['nutrition']['foods']
        if month<6:assert 'khichdi' not in str(result.json['guide']['nutrition']).lower()
    for year in range(1,13):
        child=create_profile(client,owner,date_of_birth=f'{2026-year}-10-31')
        result=client.get(f'/api/v1/children/{child}/growth-nutrition-guide',headers=owner)
        assert result.status_code==200,result.json
        assert result.json['age_band']['id']==f'year-{year}'
        assert result.json['guide']['nutrition']['blocks']
    monkeypatch.setattr('patient.child_routes.today',lambda:date(2027,10,31))
    result=client.get(f'/api/v1/children/{child}/growth-nutrition-guide',headers=owner)
    assert result.json['status']=='OUT_OF_SCOPE' and result.json['guide'] is None


def test_connected_doctor_can_toggle_only_the_selected_child(app,client,monkeypatch):
    monkeypatch.setattr('patient.child_routes.today',lambda:date(2026,10,31))
    admin,doctor,doctor_id=setup_staff(app,client)
    owner=patient(app,client);child=create_profile(client,owner);other=create_profile(client,owner)
    with app.app_context():db().get(CareProfile,child).referred_doctor_id=doctor_id;db().commit()
    family=f'/api/v1/children/{child}/growth-nutrition-guide'
    base=f'/api/v1/doctors/care-profiles/{child}/growth-nutrition-guide'
    assert client.get(base,headers=doctor).json['guide']==client.get(family,headers=owner).json['guide']
    assert client.patch(base+'/visibility',headers=owner,json={'active':False}).status_code==403
    assert client.patch(base+'/visibility',headers=admin,json={'active':False}).status_code==403
    assert client.patch(base+'/visibility',headers=doctor,json={'active':'false'}).status_code==422
    assert client.get(f'/api/v1/doctors/care-profiles/{other}/growth-nutrition-guide',headers=doctor).status_code==404
    for active in (False,True,False,True):
        result=client.patch(base+'/visibility',headers=doctor,json={'active':active})
        assert result.status_code==200,result.json
        response=client.get(family,headers=owner).json
        assert response['active']==active and bool(response['guide'])==active
        assert client.get(f'/api/v1/children/{other}/growth-nutrition-guide',headers=owner).json['active'] is True
    # Existing measurement endpoints remain available while the educational guide is disabled.
    client.patch(base+'/visibility',headers=doctor,json={'active':False})
    assert client.get(f'/api/v1/children/{child}/growth',headers=owner).status_code==200
    stranger=patient(app,client,'stranger@example.com')
    assert client.get(family,headers=stranger).status_code==404
    with app.app_context():db().get(CareProfile,child).referred_doctor_id=None;db().commit()
    assert client.patch(base+'/visibility',headers=doctor,json={'active':True}).status_code==404
