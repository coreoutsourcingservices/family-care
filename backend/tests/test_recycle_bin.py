from datetime import timedelta
from sqlalchemy import select
from core.database import db
from core.models import CareReport, CustomerNote, RecycleItem, ChildRecord, now, uid
from conftest import create_account
from test_care import patient, create_profile
from test_workflows import bearer, PASSWORD
from services.recycle_bin import purge_one


def setup(app,client):
    create_account(app,'ADMIN','recycle-admin@example.com')
    admin=bearer(client.post('/api/v1/admin/login',json={'email':'recycle-admin@example.com','password':PASSWORD}))
    owner=patient(app,client)
    profile=create_profile(client,owner)
    return admin,owner,profile


def add_report(app,profile,cloud=False):
    with app.app_context():
        row=CareReport(profile_id=profile,name='Private medical filename.pdf',content_type='application/pdf',content=b'%PDF-synthetic',
            storage_provider='cloudinary' if cloud else 'database',cloudinary_public_id='test/private' if cloud else None,resource_type='raw' if cloud else None)
        db().add(row);db().flush();identifier=row.id
        db().add(ChildRecord(profile_id=profile,kind='history',data={'title':'Private test result','source_report_id':identifier}))
        db().commit();return identifier


def items(client,admin):
    result=client.get('/api/v1/admin/recycle-bin',headers=admin)
    assert result.status_code==200,result.json
    return result.json['items']


def test_report_is_hidden_retained_restored_with_linked_record_and_admin_privacy(app,client):
    admin,owner,profile=setup(app,client);report=add_report(app,profile)
    path=f'/api/v1/patients/profiles/{profile}/reports/{report}'
    assert client.delete(path,headers=owner).status_code==200
    assert client.get(path+'/download',headers=owner).status_code==404
    assert client.get(f'/api/v1/patients/profiles/{profile}/reports',headers=owner).json['items']==[]
    rows=items(client,admin)
    assert {row['type'] for row in rows}=={'report','child_record'}
    assert 'Private' not in str(rows) and 'test result' not in str(rows)
    assert client.get('/api/v1/admin/recycle-bin',headers=owner).status_code==403
    report_item=next(row for row in rows if row['type']=='report')
    assert client.post(f"/api/v1/admin/recycle-bin/{report_item['id']}/restore",headers=owner,json={}).status_code==403
    assert client.post(f"/api/v1/admin/recycle-bin/{report_item['id']}/restore",headers=admin,json={}).status_code==200
    assert client.get(path+'/download',headers=owner).status_code==200
    assert items(client,admin)==[]
    with app.app_context():
        assert db().get(CareReport,report).deleted_at is None
        assert db().scalar(select(ChildRecord).where(ChildRecord.profile_id==profile)).deleted_at is None


def test_expiration_and_cloud_failures_retry_without_deleting_early(app,client,monkeypatch):
    admin,owner,profile=setup(app,client);report=add_report(app,profile,cloud=True)
    assert client.delete(f'/api/v1/patients/profiles/{profile}/reports/{report}',headers=owner).status_code==200
    report_item=next(row for row in items(client,admin) if row['type']=='report')
    with app.app_context():
        item=db().get(RecycleItem,report_item['id'])
        assert item.expires_at-item.deleted_at==timedelta(days=30)
        assert not purge_one()
        item.expires_at=now()-timedelta(seconds=1);db().commit()
    assert client.post(f"/api/v1/admin/recycle-bin/{report_item['id']}/restore",headers=admin,json={}).status_code==409
    monkeypatch.setattr('services.recycle_bin.destroy_asset',lambda *args: (_ for _ in ()).throw(RuntimeError('storage down')))
    with app.app_context():
        assert purge_one()
        assert db().get(CareReport,report) is not None
        assert db().get(RecycleItem,report_item['id']).retry_after>now()
        db().get(RecycleItem,report_item['id']).retry_after=None;db().commit()
    destroyed=[];monkeypatch.setattr('services.recycle_bin.destroy_asset',lambda *args:destroyed.append(args))
    with app.app_context():
        assert purge_one()
        assert db().get(CareReport,report) is None
        assert db().get(RecycleItem,report_item['id']) is None
    assert destroyed==[('test/private','raw')]


def test_notes_and_profiles_can_be_restored_but_not_after_expiry(app,client):
    admin,owner,profile=setup(app,client)
    note=client.post('/api/v1/patients/notes',headers=owner,json={'title':'Private title','body':'Private content'}).json['note']
    assert client.delete('/api/v1/patients/notes/'+note['id'],headers=owner).status_code==200
    assert client.get('/api/v1/patients/notes',headers=owner).json['items']==[]
    assert client.delete('/api/v1/patients/profiles/'+profile,headers=owner).status_code==200
    listing=items(client,admin)
    assert {row['type'] for row in listing}=={'customer_note','profile'}
    assert 'Private title' not in str(listing)
    profile_item=next(row for row in listing if row['type']=='profile')
    note_item=next(row for row in listing if row['type']=='customer_note')
    assert client.post('/api/v1/admin/recycle-bin/'+profile_item['id']+'/restore',headers=admin,json={}).status_code==200
    assert client.get('/api/v1/patients/profiles/'+profile,headers=owner).status_code==200
    assert client.post('/api/v1/admin/recycle-bin/'+note_item['id']+'/restore',headers=admin,json={}).status_code==200
    assert client.get('/api/v1/patients/notes',headers=owner).json['items'][0]['body']=='Private content'


def test_recent_activity_is_paginated_role_restricted_and_filters_sensitive_events(app,client):
    from core.models import AuditLog,User
    admin,owner,profile=setup(app,client)
    with app.app_context():
        user=db().scalar(select(User).where(User.role=='PATIENT'))
        db().add_all([AuditLog(action='registered',actor_id=user.id,target_id=user.id),AuditLog(action='women_diary_saved',actor_id=user.id,target_id=user.id)])
        db().commit()
    result=client.get('/api/v1/admin/recent-activity?per_page=1',headers=admin)
    assert result.status_code==200 and result.json['total']>=1 and len(result.json['items'])==1
    all_rows=client.get('/api/v1/admin/recent-activity?per_page=100',headers=admin).json['items']
    assert 'registered' in {row['action'] for row in all_rows}
    assert 'women_diary_saved' not in {row['action'] for row in all_rows}
    assert client.get('/api/v1/admin/recent-activity?action=women_diary_saved',headers=admin).status_code==400
    assert client.get('/api/v1/admin/recent-activity',headers=owner).status_code==403


def test_recent_activity_date_ranges_and_pagination(app,client,monkeypatch):
    from datetime import datetime,timezone
    from zoneinfo import ZoneInfo
    from sqlalchemy import delete
    from core.models import AuditLog,User
    import services.management_dashboard as dashboard
    admin,owner,profile=setup(app,client)
    fixed=datetime(2026,11,3,12,0,tzinfo=ZoneInfo('Asia/Kolkata'))
    class FrozenDateTime(datetime):
        @classmethod
        def now(cls,tz=None):
            return fixed.astimezone(tz) if tz else fixed.replace(tzinfo=None)
    monkeypatch.setattr(dashboard,'datetime',FrozenDateTime)
    with app.app_context():
        user=db().scalar(select(User).where(User.role=='PATIENT'))
        db().execute(delete(AuditLog))
        for days in (2,10,60,400):
            stamp=(fixed-timedelta(days=days)).astimezone(timezone.utc).replace(tzinfo=None)
            db().add(AuditLog(action='registered',actor_id=user.id,target_id=user.id,created_at=stamp))
        db().commit()
    base='/api/v1/admin/recent-activity'
    for period,count in [('7d',1),('1m',2),('1y',3),('all',4)]:
        response=client.get(base+'?period='+period+'&per_page=1',headers=admin)
        assert response.status_code==200 and response.json['total']==count and len(response.json['items'])==1
    custom=client.get(base+'?period=custom&start_date=2026-10-24&end_date=2026-11-01',headers=admin)
    assert custom.status_code==200 and custom.json['total']==2
    combined=client.get(base+'?period=1m&action=care_profile_created',headers=admin)
    assert combined.status_code==200 and combined.json['total']==0
    for query in ['period=custom','period=custom&start_date=2026-11-02&end_date=2026-11-01',
                  'period=custom&start_date=20261101&end_date=2026-11-03','period=unknown']:
        assert client.get(base+'?'+query,headers=admin).status_code==400
    with app.app_context():
        user=db().scalar(select(User).where(User.role=='PATIENT'))
        for stamp in (datetime(2026,10,31,18,30),datetime(2026,11,1,18,29,59),datetime(2026,11,1,18,30)):
            db().add(AuditLog(action='registered',actor_id=user.id,target_id=user.id,created_at=stamp))
        db().commit()
    day=client.get(base+'?period=custom&start_date=2026-11-01&end_date=2026-11-01',headers=admin)
    assert day.status_code==200 and day.json['total']==3


def test_profile_purge_removes_storage_only_after_expiry_and_keeps_other_profiles(app,client,monkeypatch):
    from core.models import CareProfile
    admin,owner,profile=setup(app,client)
    other=create_profile(client,owner)
    report=add_report(app,profile,cloud=True)
    assert client.delete('/api/v1/patients/profiles/'+profile,headers=owner).status_code==200
    item=next(row for row in items(client,admin) if row['type']=='profile')
    removed=[];monkeypatch.setattr('services.recycle_bin.destroy_asset',lambda *args:removed.append(args))
    with app.extensions['database_engine'].connect() as conn:
        conn.exec_driver_sql('PRAGMA foreign_keys=ON')
    with app.app_context():
        assert not purge_one() and not removed
        db().get(RecycleItem,item['id']).expires_at=now()-timedelta(seconds=1);db().commit()
        assert purge_one()
        assert db().get(CareProfile,profile) is None
        assert db().get(CareReport,report) is None
        assert db().get(CareProfile,other) is not None
    assert removed==[('test/private','raw')]


def test_report_linked_item_requires_report_restore(app,client):
    admin,owner,profile=setup(app,client);report=add_report(app,profile)
    assert client.delete(f'/api/v1/patients/profiles/{profile}/reports/{report}',headers=owner).status_code==200
    linked=next(row for row in items(client,admin) if row['type']=='child_record')
    assert linked['requires_report'] is True
    response=client.post('/api/v1/admin/recycle-bin/'+linked['id']+'/restore',headers=admin,json={})
    assert response.status_code==409 and response.json['error']['code']=='restore_report_first'


def test_profile_cleanup_waits_for_each_nested_items_full_retention(app,client):
    from core.models import CareProfile
    admin,owner,profile=setup(app,client);report=add_report(app,profile)
    assert client.delete(f'/api/v1/patients/profiles/{profile}/reports/{report}',headers=owner).status_code==200
    assert client.delete('/api/v1/patients/profiles/'+profile,headers=owner).status_code==200
    profile_item=next(row for row in items(client,admin) if row['type']=='profile')
    with app.app_context():
        db().get(RecycleItem,profile_item['id']).expires_at=now()-timedelta(seconds=1);db().commit()
        assert purge_one()
        assert db().get(CareProfile,profile) is not None
        assert db().get(CareReport,report) is not None
        assert db().get(RecycleItem,profile_item['id']).retry_after>now()


def test_child_adult_women_and_planner_deletions_can_be_restored(app,client):
    from core.models import AdultRecord,WomenDiaryRecord,ProfilePlanner,User
    admin,owner,child=setup(app,client)
    adult=create_profile(client,owner,module='adult',date_of_birth='1990-01-01')
    women=create_profile(client,owner,module='women',date_of_birth='1990-01-01')
    with app.app_context():
        owner_id=db().scalar(select(User.id).where(User.role=='PATIENT'))
        child_row=ChildRecord(profile_id=child,kind='growth',data={'title':'Child record','date':'2026-01-01'})
        adult_row=AdultRecord(profile_id=adult,kind='history',data={'title':'Adult record','date':'2026-01-01'})
        women_row=WomenDiaryRecord(profile_id=women,section='health',data={'title':'Women record'},version=1,updated_by=owner_id)
        planner=ProfilePlanner(profile_id=women,user_id=owner_id,kind='note',title='Private note',body='Example',version=1)
        db().add_all([child_row,adult_row,women_row,planner]);db().flush()
        child_id,adult_id,women_id,planner_id=[row.id for row in [child_row,adult_row,women_row,planner]]
        db().commit()
    assert client.delete(f'/api/v1/children/{child}/growth/{child_id}',headers=owner).status_code==200
    assert client.delete(f'/api/v1/patients/adults/{adult}/records/{adult_id}',headers=owner).status_code==200
    assert client.delete(f'/api/v1/women/profiles/{women}/diary/{women_id}?version=1',headers=owner).status_code==200
    assert client.delete(f'/api/v1/patients/profiles/{women}/planner/{planner_id}',headers=owner).status_code==200
    listing=items(client,admin)
    assert {row['type'] for row in listing}=={'child_record','adult_record','women_diary','planner'}
    for row in listing:
        assert client.post('/api/v1/admin/recycle-bin/'+row['id']+'/restore',headers=admin,json={}).status_code==200
    with app.app_context():
        assert db().get(ChildRecord,child_id).deleted_at is None
        assert db().get(AdultRecord,adult_id).deleted_at is None
        assert db().get(WomenDiaryRecord,women_id).deleted_at is None and db().get(WomenDiaryRecord,women_id).version==2
        assert db().get(ProfilePlanner,planner_id).deleted_at is None and db().get(ProfilePlanner,planner_id).version==2


def test_doctor_photo_remove_and_restore_without_exposing_storage_key(app,client):
    from core.models import DoctorProfile
    from test_referrals import doctor
    admin,owner,profile=setup(app,client)
    did,_=doctor(app)
    auth=bearer(client.post('/api/v1/doctors/login',json={'email':'rahul@example.com','password':PASSWORD}))
    with app.app_context():
        db().get(DoctorProfile,did).onboarding_images={'profile_photo':{'public_id':'private/photo','format':'png','name':'profile.png'}}
        db().commit()
    assert client.delete('/api/v1/doctors/profile-photo',headers=auth).status_code==200
    listing=items(client,admin);item=next(row for row in listing if row['type']=='doctor_photo')
    assert 'private/photo' not in str(listing)
    assert client.post('/api/v1/admin/recycle-bin/'+item['id']+'/restore',headers=admin,json={}).status_code==200
    with app.app_context():
        assert db().get(DoctorProfile,did).onboarding_images['profile_photo']['public_id']=='private/photo'


def test_admin_bulk_activity_delete_snapshot_restore_and_expiry(app,client):
    from core.models import AuditLog,User
    admin,owner,profile=setup(app,client)
    with app.app_context():
        user=db().scalar(select(User).where(User.email=='family@example.com'))
        # Use the owner attached to this synthetic profile.
        from core.models import CareProfile
        owner_id=db().get(CareProfile,profile).owner_id
        recent=AuditLog(actor_id=owner_id,action='registered',created_at=now()-timedelta(days=1))
        old=AuditLog(actor_id=owner_id,action='registered',created_at=now()-timedelta(days=90))
        db().add_all([recent,old]);db().commit();recent_id=recent.id;old_id=old.id
    path='/api/v1/admin/recent-activity'
    selected=client.get(path+'?period=7d&action=registered&per_page=1',headers=admin).json
    assert selected['total']>=1
    body={'token':selected['delete_token'],'confirmed':True}
    assert client.post(path+'/delete',headers=owner,json=body).status_code==403
    assert client.post(path+'/delete',headers=admin,json={'token':body['token'],'confirmed':False}).status_code==422
    result=client.post(path+'/delete',headers=admin,json=body)
    assert result.status_code==200,result.json
    assert result.json['deleted']==selected['total']
    assert client.get(path+'?period=7d&action=registered',headers=admin).json['total']==0
    assert client.post(path+'/delete',headers=admin,json=body).status_code==409
    with app.app_context():
        assert db().get(AuditLog,recent_id).deleted_at
        assert db().get(AuditLog,old_id).deleted_at is None
    marker=next(r for r in items(client,admin) if r['type']=='activity_log')
    assert client.post(f"/api/v1/admin/recycle-bin/{marker['id']}/restore",headers=admin,json={}).status_code==200
    with app.app_context():
        remaining=db().scalars(select(RecycleItem).where(RecycleItem.entity_type=='activity_log')).all()
        for row in remaining:row.expires_at=now()-timedelta(seconds=1)
        db().commit()
        while purge_one():pass
        assert db().get(AuditLog,old_id) is not None


def test_empty_bin_deletes_all_pages_and_rejects_stale_selection(app,client):
    admin,owner,profile=setup(app,client)
    from core.models import CareProfile
    from services.recycle_bin import retain
    for index in range(23):
        with app.app_context():
            row=CustomerNote(owner_id=db().get(CareProfile,profile).owner_id,title='Synthetic note',body='Test',deleted_at=now())
            db().add(row);db().flush()
            from services.recycle_bin import retain
            from core.models import CareProfile
            retain('customer_note',row,actor_id=db().get(CareProfile,profile).owner_id)
            db().commit()
    path='/api/v1/admin/recycle-bin'
    listing=client.get(path+'?per_page=1',headers=admin).json
    assert listing['total']==23 and len(listing['items'])==1
    body={'token':listing['delete_token'],'confirmed':True}
    assert client.post(path+'/empty',headers=owner,json=body).status_code==403
    assert client.post(path+'/empty',headers=admin,json={'token':body['token'],'confirmed':False}).status_code==422
    result=client.post(path+'/empty',headers=admin,json=body)
    assert result.status_code==200,result.json
    assert result.json['deleted']==23 and result.json['failed']==0
    assert client.get(path,headers=admin).json['total']==0
    assert client.post(path+'/empty',headers=admin,json=body).status_code==409


def test_empty_bin_keeps_failed_cloud_report_and_its_marker(app,client,monkeypatch):
    admin,owner,profile=setup(app,client)
    report=add_report(app,profile,cloud=True)
    assert client.delete(f'/api/v1/patients/profiles/{profile}/reports/{report}',headers=owner).status_code==200
    token=client.get('/api/v1/admin/recycle-bin',headers=admin).json['delete_token']
    monkeypatch.setattr('services.recycle_bin.destroy_asset',lambda *args: (_ for _ in ()).throw(RuntimeError('storage down')))
    result=client.post('/api/v1/admin/recycle-bin/empty',headers=admin,json={'token':token,'confirmed':True})
    assert result.status_code==200 and result.json['failed']==1
    with app.app_context():
        assert db().get(CareReport,report) is not None
        assert db().scalar(select(RecycleItem).where(RecycleItem.entity_id==report)) is not None


def test_empty_bin_bulk_activity_uses_one_commit(app,client,monkeypatch):
    from core.models import AuditLog,CareProfile
    from services.recycle_bin import retain
    admin,owner,profile=setup(app,client)
    with app.app_context():
        owner_id=db().get(CareProfile,profile).owner_id
        for index in range(124):
            row=AuditLog(actor_id=owner_id,action='login_success',deleted_at=now())
            db().add(row);db().flush()
            retain('activity_log',row,actor_id=owner_id)
        db().commit()
    token=client.get('/api/v1/admin/recycle-bin',headers=admin).json['delete_token']
    from sqlalchemy.orm import Session
    original=Session.commit
    commits=[]
    def counted(session):
        commits.append(1)
        return original(session)
    monkeypatch.setattr(Session,'commit',counted)
    response=client.post('/api/v1/admin/recycle-bin/empty',headers=admin,json={'token':token,'confirmed':True})
    assert response.status_code==200,response.json
    assert response.json['deleted']==124 and response.json['failed']==0
    assert len(commits)<=2
    with app.app_context():
        assert not db().scalars(select(RecycleItem)).all()
        assert not db().scalars(select(AuditLog).where(AuditLog.deleted_at.is_not(None))).all()


def test_superadmin_activity_names_delete_restore_and_admin_isolation(app,client):
    from test_workflows import super_login
    from core.models import AuditLog,User
    admin,owner,profile=setup(app,client)
    superadmin=bearer(super_login(app,client))
    with app.app_context():
        actor=db().scalar(select(User).where(User.role=='SUPERADMIN'))
        target=db().scalar(select(User).where(User.role=='ADMIN'))
        actor.full_name='Organization Owner';target.full_name='Administrator Example'
        row=AuditLog(actor_id=actor.id,target_id=target.id,action='security_reviewed')
        db().add(row);db().commit();identifier=row.id
    path='/api/v1/superadmin/audit-logs'
    listing=client.get(path+'?period=7d&action=security_reviewed',headers=superadmin)
    assert listing.status_code==200,listing.json
    assert listing.json['total']==1
    entry=listing.json['items'][0]
    assert entry['actor_name']=='Organization Owner'
    assert entry['target_name']=='Administrator Example'
    assert client.get(path,headers=admin).status_code==403
    body={'token':listing.json['delete_token'],'confirmed':True}
    assert client.post('/api/v1/admin/recent-activity/delete',headers=admin,json=body).status_code==403
    assert client.post(path+'/delete',headers=superadmin,json=body).json['deleted']==1
    assert client.get(path+'?action=security_reviewed',headers=superadmin).json['total']==0
    assert not any(item['type']=='activity_log' for item in items(client,admin))
    bin_path='/api/v1/superadmin/recycle-bin'
    bin_data=client.get(bin_path,headers=superadmin).json
    marker=next(item for item in bin_data['items'] if item['type']=='activity_log')
    assert client.post(f"/api/v1/admin/recycle-bin/{marker['id']}/restore",headers=admin,json={}).status_code==404
    assert client.post(f"{bin_path}/{marker['id']}/restore",headers=superadmin,json={}).status_code==200
    assert client.get(path+'?action=security_reviewed',headers=superadmin).json['total']==1
    selection=client.get(path+'?action=security_reviewed',headers=superadmin).json
    client.post(path+'/delete',headers=superadmin,json={'token':selection['delete_token'],'confirmed':True})
    token=client.get(bin_path,headers=superadmin).json['delete_token']
    assert client.post(bin_path+'/empty',headers=superadmin,json={'token':token,'confirmed':True}).json['deleted']==1
    with app.app_context():assert db().get(AuditLog,identifier) is None
