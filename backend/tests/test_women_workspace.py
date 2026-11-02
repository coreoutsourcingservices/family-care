from datetime import timedelta
import io
import uuid
import pytest
from sqlalchemy import select
from core.database import db
from core.models import User, FamilyInvitation, WomenAccessGrant, WomenDiaryRecord, CareReport, AuditLog, now
from test_care import patient, create_profile, cloud
from test_referrals import doctor
from test_workflows import bearer, PASSWORD


@pytest.fixture
def family(app, client):
    owner = patient(app, client)
    profile = create_profile(client, owner, kind='self', module='women', date_of_birth='1990-01-01')
    member = patient(app, client, 'member@example.com')
    member_profile = create_profile(client, member, module='adult', date_of_birth='1991-01-01')
    with app.app_context():
        owner_id = db().scalar(select(User.id).where(User.email == 'family@example.com'))
        member_id = db().scalar(select(User.id).where(User.email == 'member@example.com'))
        db().add(FamilyInvitation(owner_id=owner_id, member_id=member_id, profile_id=member_profile,
            token_hash='test-women-member', full_name='Member', email='member@example.com', module='adult',
            relationship='Partner', accepted_at=now(), expires_at=now()+timedelta(days=1)))
        db().commit()
    return owner, profile, member, member_id


def grant(client, owner, profile, recipient, permissions, **extra):
    return client.put(f'/api/v1/women/profiles/{profile}/sharing', headers=owner,
        json=dict(recipient_id=recipient, permissions=permissions,
            expires_at=(now()+timedelta(days=7)).isoformat()+'Z', **extra))


def entry(client, headers, profile, section='cycle', **extra):
    record_id = str(uuid.uuid4())
    response = client.put(f'/api/v1/women/profiles/{profile}/diary/{record_id}', headers=headers,
        json=dict(section=section, data=dict(title='Period entry', date='2026-10-01', **extra)))
    return record_id, response


def test_family_view_edit_tabs_and_owner_only_sharing(app, client, family):
    owner, profile, member, mid = family
    base = f'/api/v1/women/profiles/{profile}'
    _, saved = entry(client, owner, profile)
    assert saved.status_code == 200, saved.json
    entry(client, owner, profile, 'pcos', notes='Private PCOS note')
    assert client.get(base+'/workspace', headers=member).status_code == 403
    response = grant(client, owner, profile, mid, {'cycle':'view', 'nutrition':'edit'})
    assert response.status_code == 200, response.json
    shared = client.get(base+'/workspace', headers=member).json
    assert shared['owner'] is False
    assert shared['permissions'] == {'cycle':'view', 'nutrition':'edit'}
    assert [r['section'] for r in shared['records']] == ['cycle']
    assert 'Private PCOS' not in str(shared)
    assert entry(client, member, profile)[1].status_code == 403
    assert entry(client, member, profile, 'nutrition')[1].status_code == 200
    assert entry(client, member, profile, 'pcos')[1].status_code == 403
    assert entry(client, member, profile, 'reminder')[1].status_code == 403
    assert client.get(base+'/sharing', headers=member).status_code == 403
    assert grant(client, member, profile, mid, {'cycle':'edit'}).status_code == 403
    assert client.get('/api/v1/women/shared', headers=member).json['items'][0]['id'] == profile
    # Generic routes must not bypass tab permissions, even for family accounts.
    assert client.get(f'/api/v1/patients/profiles/{profile}/reports', headers=member).status_code == 403


def test_owner_updates_recipient_edits_conflicts_and_delete(app, client, family):
    owner, profile, member, mid = family
    assert grant(client, owner, profile, mid, {'health':'edit'}).status_code == 200
    rid, response = entry(client, member, profile, 'health')
    record = response.json['record']
    path = f'/api/v1/women/profiles/{profile}/diary/{rid}'
    update = dict(section='health', data={'title':'Updated by owner', 'date':'2026-10-02'}, version=int(record['version']))
    assert client.put(path, headers=owner, json=update).status_code == 200
    assert client.put(path, headers=member, json=update).status_code == 409
    assert client.delete(path+'?version=1', headers=member).status_code == 409
    assert client.delete(path+'?version=2', headers=member).status_code == 200
    assert client.get(f'/api/v1/women/profiles/{profile}/workspace', headers=owner).json['records'] == []
    assert client.put(path, headers=member, json=update).status_code == 409


def test_doctor_expiry_revoke_and_legacy_bypass(app, client, family):
    owner, profile, _, _ = family
    did, referral = doctor(app)
    dh = bearer(client.post('/api/v1/doctors/login', json={'email':'rahul@example.com','password':PASSWORD}))
    assert client.post(f'/api/v1/patients/profiles/{profile}/connect-doctor', headers=owner, json={'referral_id':referral}).status_code == 200
    base = f'/api/v1/women/profiles/{profile}'
    # Connecting alone never grants Women diary access.
    assert client.get(base+'/workspace', headers=dh).status_code == 403
    response = grant(client, owner, profile, did, {'pregnancy':'edit', 'records':'view'})
    gid = response.json['grant']['id']
    assert entry(client, dh, profile, 'pregnancy', week='12')[1].status_code == 200
    assert entry(client, dh, profile, 'cycle')[1].status_code == 403
    assert client.get(f'/api/v1/doctors/care-profiles/{profile}', headers=dh).status_code == 403
    with app.app_context():
        db().get(WomenAccessGrant, gid).expires_at = now()-timedelta(seconds=1)
        db().commit()
    assert client.get(base+'/workspace', headers=dh).status_code == 403
    assert client.get('/api/v1/women/shared', headers=dh).json['items'] == []
    assert entry(client, dh, profile, 'pregnancy')[1].status_code == 403
    assert grant(client, owner, profile, did, {'pregnancy':'view'}).status_code == 200
    assert client.delete(base+'/sharing/'+gid, headers=owner).status_code == 200
    assert client.get(base+'/workspace', headers=dh).status_code == 403


def test_reports_enforce_view_edit_and_expiry(app, client, family):
    owner, profile, member, mid = family
    with app.app_context():
        report = CareReport(profile_id=profile, name='private.pdf', content_type='application/pdf',
            content=b'%PDF-1.7\nprivate', storage_provider='database')
        db().add(report);db().commit();rid=report.id
    base = f'/api/v1/women/profiles/{profile}/reports'
    grant(client, owner, profile, mid, {'cycle':'view'})
    assert client.get(base, headers=member).status_code == 403
    assert client.get(base+'/'+rid+'/download', headers=member).status_code == 403
    response = grant(client, owner, profile, mid, {'records':'view'})
    assert client.get(base, headers=member).json['items'][0]['url'] is None
    assert client.get(base+'/'+rid+'/download', headers=member).data == b'%PDF-1.7\nprivate'
    assert client.delete(base+'/'+rid, headers=member).status_code == 403
    assert client.post(base, headers=member, data={'file':(io.BytesIO(b'%PDF-1.7'), 'new.pdf')}).status_code == 403
    with app.app_context():
        db().get(WomenAccessGrant,response.json['grant']['id']).expires_at=now()-timedelta(seconds=1);db().commit()
    assert client.get(base+'/'+rid+'/download', headers=member).status_code == 403
    grant(client, owner, profile, mid, {'records':'edit'})
    assert client.delete(base+'/'+rid, headers=member).status_code == 200
    assert client.get(base, headers=owner).json['items'] == []


def test_invalid_recipients_dates_and_payloads(app, client, family):
    owner, profile, member, mid = family
    stranger = patient(app, client, 'stranger@example.com')
    with app.app_context():
        sid = db().scalar(select(User.id).where(User.email == 'stranger@example.com'))
    assert grant(client, owner, profile, sid, {'health':'edit'}).status_code == 422
    assert grant(client, owner, profile, mid, {'settings':'edit'}).status_code == 422
    assert grant(client, owner, profile, mid, {}).status_code == 422
    path = f'/api/v1/women/profiles/{profile}/sharing'
    for expiry in ['2020-01-01T00:00:00Z', '2026-12-01T00:00:00']:
        assert client.put(path, headers=owner, json={'recipient_id':mid,'permissions':{'cycle':'view'},'expires_at':expiry}).status_code == 422
    assert entry(client, owner, profile, 'pregnancy', week='46')[1].status_code == 422
    assert entry(client, owner, profile, end='2026-09-01')[1].status_code == 422
    assert client.get(f'/api/v1/women/profiles/{profile}/workspace', headers=stranger).status_code == 403
    another = create_profile(client, owner, module='women', date_of_birth='1991-01-01')
    grant(client, owner, profile, mid, {'health':'edit'})
    rid, _ = entry(client, owner, another, 'health')
    assert client.delete(f'/api/v1/women/profiles/{profile}/diary/{rid}?version=1', headers=member).status_code == 404


def test_invited_woman_controls_her_profile_not_inviting_family(app, client, family):
    owner, profile, member, mid = family
    with app.app_context():
        owner_id=db().scalar(select(User.id).where(User.email=='family@example.com'))
        invitation=db().scalar(select(FamilyInvitation).where(FamilyInvitation.member_id==mid))
        invitation.profile_id=profile
        invitation.module='women'
        db().commit()
    assert client.get(f'/api/v1/women/profiles/{profile}/sharing',headers=member).status_code==200
    assert client.get(f'/api/v1/women/profiles/{profile}/sharing',headers=owner).status_code==403
    assert grant(client,member,profile,owner_id,{'cycle':'view'}).status_code==200
    assert client.get(f'/api/v1/women/profiles/{profile}/workspace',headers=owner).status_code==200
    assert entry(client,owner,profile)[1].status_code==403


@pytest.mark.parametrize('section',['health','cycle','pcos','pregnancy','fertility','symptoms','nutrition','screening','consultation'])
def test_each_diary_tab_has_independent_view_and_edit(app,client,family,section):
    owner,profile,member,mid=family
    rid,response=entry(client,owner,profile,section)
    assert response.status_code==200
    grant(client,owner,profile,mid,{section:'view'})
    assert [r['section'] for r in client.get(f'/api/v1/women/profiles/{profile}/workspace',headers=member).json['records']]==[section]
    assert entry(client,member,profile,section)[1].status_code==403
    assert client.delete(f'/api/v1/women/profiles/{profile}/diary/{rid}?version=1',headers=member).status_code==403
    grant(client,owner,profile,mid,{section:'edit'})
    assert entry(client,member,profile,section)[1].status_code==200
    with app.app_context():
        owner_id=db().scalar(select(User.id).where(User.email=='family@example.com'))
        logs=db().scalars(select(AuditLog).where(AuditLog.action=='women_diary_saved')).all()
        assert logs and all(log.target_id==owner_id for log in logs)
        assert all(db().get(User,log.target_id) is not None for log in logs)


def test_report_upload_permission_and_doctor_disconnect(app,client,family,cloud):
    owner,profile,member,mid=family
    grant(client,owner,profile,mid,{'records':'edit'})
    response=client.post(f'/api/v1/women/profiles/{profile}/reports',headers=member,
        data={'file':(io.BytesIO(b'%PDF-1.7\nSynthetic report'),'shared.pdf')})
    assert response.status_code==201,response.json
    assert response.json['report']['url'] is None
    assert response.json['report']['secure_url'] is None
    did,referral=doctor(app)
    dh=bearer(client.post('/api/v1/doctors/login',json={'email':'rahul@example.com','password':PASSWORD}))
    connection=f'/api/v1/patients/profiles/{profile}/connect-doctor'
    client.post(connection,headers=owner,json={'referral_id':referral})
    grant(client,owner,profile,did,{'cycle':'view'})
    assert client.get(f'/api/v1/women/profiles/{profile}/workspace',headers=dh).status_code==200
    assert client.delete(f'/api/v1/patients/profiles/{profile}/doctor',headers=owner).status_code==200
    assert client.get(f'/api/v1/women/profiles/{profile}/workspace',headers=dh).status_code==403

    client.post(connection,headers=owner,json={'referral_id':referral})
    assert client.get(f'/api/v1/women/profiles/{profile}/workspace',headers=dh).status_code==403


def test_no_expiry_access_can_be_changed_to_timed_and_revoked(app,client,family):
    owner,profile,member,mid=family
    base=f'/api/v1/women/profiles/{profile}'
    body={'recipient_id':mid,'permissions':{'cycle':'edit'},'expires_at':None}
    response=client.put(base+'/sharing',headers=owner,json=body)
    assert response.status_code==200,response.json
    grant_id=response.json['grant']['id']
    assert response.json['grant']['active'] is True
    assert response.json['grant']['expires_at'] is None
    assert client.get(base+'/workspace',headers=member).json['access_expires_at'] is None
    assert client.get('/api/v1/women/shared',headers=member).json['items'][0]['id']==profile
    assert entry(client,member,profile)[1].status_code==200
    body['expires_at']=(now()+timedelta(days=1)).isoformat()+'Z'
    assert client.put(base+'/sharing',headers=owner,json=body).json['grant']['expires_at'] is not None
    body['expires_at']=None
    assert client.put(base+'/sharing',headers=owner,json=body).json['grant']['active'] is True
    assert client.delete(base+'/sharing/'+grant_id,headers=owner).status_code==200
    assert client.get(base+'/workspace',headers=member).status_code==403
    assert client.get('/api/v1/women/shared',headers=member).json['items']==[]


def test_diary_save_delete_with_foreign_keys_enforced(app,client,family):
    owner,profile,_,_=family
    engine=app.extensions['database_engine']
    sqlite=engine.dialect.name=='sqlite'
    if sqlite:
        with engine.connect() as connection:
            connection.exec_driver_sql('PRAGMA foreign_keys=ON')
    try:
        for section in ('health','cycle','pcos','pregnancy','fertility','symptoms','nutrition','screening','consultation'):
            rid,response=entry(client,owner,profile,section)
            assert response.status_code==200,response.json
            deleted=client.delete(f'/api/v1/women/profiles/{profile}/diary/{rid}?version=1',headers=owner)
            assert deleted.status_code==200,deleted.json
        with app.app_context():
            logs=db().scalars(select(AuditLog).where(AuditLog.action.in_(['women_diary_saved','women_diary_removed']))).all()
            assert len(logs)==18
            assert all(db().get(User,log.target_id) is not None for log in logs)
    finally:
        if sqlite:
            with engine.connect() as connection:
                connection.exec_driver_sql('PRAGMA foreign_keys=OFF')
