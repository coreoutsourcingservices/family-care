from datetime import datetime, timedelta, timezone
from conftest import create_account
from core.database import db
from core.models import CareProfile
from test_care import patient, create_profile
from test_referrals import doctor
from test_workflows import bearer, PASSWORD


def admin(app, client):
    create_account(app, 'ADMIN', 'articles-admin@example.com')
    return bearer(client.post('/api/v1/admin/login', json={'email':'articles-admin@example.com','password':PASSWORD}))


def article(client, headers, **extra):
    value=dict(title='Month three guidance', audience='women', category='pregnancy', stage_month=3,
               content='Guidance written and reviewed by your care team.', time_label='Daily care', status='PUBLISHED')
    value.update(extra)
    r=client.post('/api/v1/admin/health-articles',json=value,headers=headers)
    assert r.status_code==201,r.json
    return r.json['article']['id']


def test_month_publication_and_inactive_filters(app,client):
    ah=admin(app,client)
    target=article(client,ah)
    general=article(client,ah,stage_month=None)
    article(client,ah,stage_month=4)
    article(client,ah,status='DRAFT')
    article(client,ah,published_at=(datetime.now(timezone.utc)+timedelta(days=1)).isoformat())
    ph=patient(app,client)
    profile=create_profile(client,ph,module='women',date_of_birth='1990-01-01')
    path=f'/api/v1/women/profiles/{profile}/health-articles?category=pregnancy'
    assert [r['id'] for r in client.get(path,headers=ph).json['items']]==[general]
    assert client.put(f'/api/v1/women/profiles/{profile}/pregnancy-care',json={'month':3},headers=ph).status_code==200
    response=client.get(path,headers=ph)
    assert response.json['stage_month']==3
    assert {r['id'] for r in response.json['items']}=={target,general}
    assert client.get(path).status_code==401
    other=patient(app,client,'other@example.com')
    assert client.get(path,headers=other).status_code==403
    invalid=client.post('/api/v1/admin/health-articles',headers=ah,json=dict(title='Invalid stage',audience='women',category='pcos',stage_month=3,content='A sufficiently long article description.'))
    assert invalid.status_code==422


def test_doctor_content_and_overrides_are_connection_scoped(app,client):
    ah=admin(app,client)
    shared=article(client,ah,category='nutrition',stage_month=None)
    d1,ref1=doctor(app)
    d2,ref2=doctor(app,'second@example.com','D000002')
    dh=bearer(client.post('/api/v1/doctors/login',json={'email':'rahul@example.com','password':PASSWORD}))
    value=dict(title='Doctor guidance',audience='women',category='nutrition',content='Doctor-authored guidance for connected patients.',status='PUBLISHED')
    created=client.post('/api/v1/doctor/women-health-articles',json=value,headers=dh)
    assert created.status_code==201,created.json
    own=created.json['article']['id']
    assert client.put('/api/v1/doctor/women-health-articles/'+shared,json=value,headers=dh).status_code==404
    listing=client.get('/api/v1/doctor/women-health-articles?category=nutrition',headers=dh).json['items']
    assert {r['id'] for r in listing}=={shared,own}
    assert own not in {r['id'] for r in client.get('/api/v1/health-articles?audience=women').json['items']}
    ph=patient(app,client)
    profile=create_profile(client,ph,module='women',date_of_birth='1990-01-01',referral_id=ref1)
    path=f'/api/v1/women/profiles/{profile}/health-articles?category=nutrition'
    assert {r['id'] for r in client.get(path,headers=ph).json['items']}=={shared,own}
    endpoint='/api/v1/doctor/women-health-articles/'+shared+'/visibility'
    assert client.put(endpoint,json={'active':False},headers=dh).status_code==200
    assert {r['id'] for r in client.get(path,headers=ph).json['items']}=={own}
    assert client.get('/api/v1/admin/health-articles/'+shared,headers=ah).json['article']['status']=='PUBLISHED'
    with app.app_context():
        db().get(CareProfile,profile).referred_doctor_id=d2
        db().commit()
    assert {r['id'] for r in client.get(path,headers=ph).json['items']}=={shared}
    assert client.put(endpoint,json={'active':'false'},headers=dh).status_code==422
    assert client.put(endpoint,json={'active':False},headers=ph).status_code==403


def test_admin_defaults_for_unconnected_and_connected_women_and_seed(app,client):
    from scripts.seed_women_articles import seed
    from core.models import HealthArticle, AuditLog, User
    from sqlalchemy import select
    ah=admin(app,client)
    with app.app_context():
        assert seed()['added']==10
        assert seed()['added']==0
        samples=db().scalars(select(HealthArticle)).all()
        assert len(samples)==10
        assert all(row.status=='PUBLISHED' for row in samples)
        assert len({row.category for row in samples})==7
        assert all(db().get(User, row.target_id) is not None for row in db().scalars(select(AuditLog)))
    ph=patient(app,client)
    profile=create_profile(client,ph,module='women',date_of_birth='1990-01-01')
    path=f'/api/v1/women/profiles/{profile}/health-articles?category=nutrition'
    unconnected=client.get(path,headers=ph).json['items']
    assert len(unconnected)==2
    _,referral=doctor(app)
    connected=create_profile(client,ph,module='women',date_of_birth='1989-01-01',referral_id=referral)
    connected_path=f'/api/v1/women/profiles/{connected}/health-articles?category=nutrition'
    assert {row['id'] for row in client.get(connected_path,headers=ph).json['items']}=={row['id'] for row in unconnected}
