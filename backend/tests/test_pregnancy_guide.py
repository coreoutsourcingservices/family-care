from datetime import date,timedelta
import pytest
from sqlalchemy import select
from core.database import db
from core.models import AppNotification,PregnancyCare
from services.pregnancy_guide import scan_guides
from test_care import patient,create_profile

@pytest.mark.parametrize('stage',[{'month':0},{'month':10},{'week':0},{'week':43},{'month':2,'week':5},{},{'month':True},{'month':'5'},{'week':15,'as_of_date':(date.today()+timedelta(days=1)).isoformat()}])
def test_stage_validation(app,client,stage):
    headers=patient(app,client)
    assert client.post('/api/v1/women/pregnancy-guide',json=stage,headers=headers).status_code==422

def test_all_months_and_trimester_boundaries(app,client):
    headers=patient(app,client)
    for month in range(1,10):
        result=client.post('/api/v1/women/pregnancy-guide',json={'month':month},headers=headers)
        assert result.status_code==200
        guide=result.json['guide']
        assert guide['month']==month and guide['approximate']
        assert guide['food'] and guide['urgent']['signs'] and len(guide['sources'])==5
    for week,trimester in [(1,1),(13,1),(14,2),(27,2),(28,3),(42,3)]:
        guide=client.post('/api/v1/women/pregnancy-guide',json={'week':week},headers=headers).json['guide']
        assert guide['trimester']==trimester and not guide['approximate']

def test_saved_stage_notifications_and_privacy(app,client):
    headers=patient(app,client)
    profile=create_profile(client,headers,module='women',date_of_birth='1990-01-01')
    path=f'/api/v1/women/profiles/{profile}/pregnancy-care'
    assert client.get(path,headers=headers).json['settings'] is None
    result=client.put(path,json={'week':16,'as_of_date':(date.today()-timedelta(days=7)).isoformat()},headers=headers)
    assert result.status_code==200,result.json
    assert result.json['guide']['week']==17
    with app.app_context():
        scan_guides();scan_guides()
        notices=db().scalars(select(AppNotification).where(AppNotification.kind=='pregnancy_guide')).all()
        assert len(notices)==1 and notices[0].title=='Pregnancy Care Guide'
        assert notices[0].data['profile_id']==profile
        row=db().get(PregnancyCare,profile);row.as_of_date-=timedelta(days=7);db().commit()
        scan_guides()
        assert len(db().scalars(select(AppNotification).where(AppNotification.kind=='pregnancy_guide')).all())==2
    assert client.put(path,json={'week':18,'version':0},headers=headers).status_code==409
    off=client.put(path,json={'week':18,'version':1,'active':False},headers=headers)
    assert off.status_code==200 and off.json['guide'] is None
    with app.app_context():
        scan_guides()
        assert len(db().scalars(select(AppNotification).where(AppNotification.kind=='pregnancy_guide')).all())==2
    other=patient(app,client,email='other@example.com')
    assert client.get(path,headers=other).status_code==403
    assert client.put(path,json={'week':10},headers=other).status_code==403

def test_stale_stage_requires_review(app,client):
    headers=patient(app,client)
    profile=create_profile(client,headers,module='women',date_of_birth='1990-01-01')
    path=f'/api/v1/women/profiles/{profile}/pregnancy-care'
    result=client.put(path,json={'week':40,'as_of_date':(date.today()-timedelta(days=28)).isoformat()},headers=headers)
    assert result.status_code==200
    assert result.json['guide']['needs_stage_review']
    with app.app_context():
        scan_guides()
        assert not db().scalar(select(AppNotification).where(AppNotification.kind=='pregnancy_guide'))
