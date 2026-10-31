from datetime import datetime,date
from sqlalchemy import select
from core.database import db
from core.models import User,CareProfile,ChildRecord,ChildGrowthNutritionSetting,ApprovalRequest
from conftest import create_account
from test_workflows import bearer,PASSWORD
from test_care import patient,create_profile
from test_referrals import doctor


def test_dashboard_aggregates_real_accounts_children_and_growth(app,client,monkeypatch):
    monkeypatch.setattr('patient.child_routes.today',lambda:date(2026,10,31))
    create_account(app,'SUPERADMIN','super@example.com');create_account(app,'ADMIN','admin@example.com')
    owner=patient(app,client);doctor_id,_=doctor(app)
    child=create_profile(client,owner,date_of_birth='2020-10-31')
    hidden=create_profile(client,owner,date_of_birth='2020-10-31')
    aged=create_profile(client,owner,date_of_birth='2013-10-31')
    with app.app_context():
        admin=db().scalar(select(User).where(User.role=='ADMIN'));admin.created_at=datetime(2025,1,1)
        db().add(ApprovalRequest(applicant_id=doctor_id,applicant_role='DOCTOR',status='APPROVED'))
        db().get(CareProfile,hidden).deleted_at=datetime(2026,10,30)
        db().add(ChildGrowthNutritionSetting(profile_id=child,active=False,updated_by=doctor_id))
        db().add(ChildRecord(profile_id=child,kind='growth',data={'title':'Synthetic measurement'}))
        db().commit()
    login=client.post('/api/v1/superadmin/login',json={'email':'super@example.com','password':PASSWORD})
    auth=bearer(login);response=client.get('/api/v1/superadmin/dashboard',headers=auth)
    assert response.status_code==200,response.json
    data=response.json
    assert data['metrics']['administrators']=={'total':1,'this_month':0}
    assert data['metrics']['patients']['total']==1
    assert data['metrics']['doctors']['total']==1
    assert data['metrics']['children']['total']==1
    assert data['child_care']['inactive_guides']==1 and data['child_care']['active_guides']==0
    assert data['child_care']['growth_records']==1
    assert len(data['monthly_growth'])==12
    assert data['monthly_growth'][0]['administrators']==1
    assert data['monthly_growth'][-1]['patients']==1
    assert len(data['recent_registrations'])==3
    assert 'counts' in data and 'recent_activities' in data
    assert client.get('/api/v1/superadmin/dashboard',headers=owner).status_code==403
    admin_auth=bearer(client.post('/api/v1/admin/login',json={'email':'admin@example.com','password':PASSWORD}))
    admin_data=client.get('/api/v1/admin/dashboard',headers=admin_auth).json
    assert admin_data['approved_doctors']==1
    assert admin_data['metrics']['administrators']['total']==0
    assert all(p['role'] in ('DOCTOR','PATIENT') for p in admin_data['recent_registrations'])
    assert client.get('/api/v1/admin/search?q=admin',headers=admin_auth).json['items']==[]
    assert client.get('/api/v1/admin/search?q=admin',headers=owner).status_code==403
    with app.app_context():
        account=db().scalar(select(User).where(User.role=='PATIENT'))
        # 30 September UTC, but already 1 October in the product's India calendar.
        account.created_at=datetime(2026,9,30,20,0);db().commit()
    refreshed=client.get('/api/v1/superadmin/dashboard',headers=auth).json
    assert refreshed['metrics']['patients']['this_month']==1
    assert refreshed['monthly_growth'][-2]['patients']==0
    assert refreshed['monthly_growth'][-1]['patients']==1


def test_dashboard_search_and_pending_role_boundaries(app,client):
    create_account(app,'SUPERADMIN','super@example.com')
    create_account(app,'ADMIN','pending@example.com')
    doctor_id,_=doctor(app)
    with app.app_context():
        admin=db().scalar(select(User).where(User.email=='pending@example.com'))
        admin.full_name='Example 100% Admin';admin.approval_status='PENDING_APPROVAL'
        db().add(ApprovalRequest(applicant_id=admin.id,applicant_role='ADMIN'))
        user=db().get(User,doctor_id);user.approval_status='PENDING_APPROVAL'
        db().add(ApprovalRequest(applicant_id=doctor_id,applicant_role='DOCTOR'))
        db().commit()
    auth=bearer(client.post('/api/v1/superadmin/login',json={'email':'super@example.com','password':PASSWORD}))
    data=client.get('/api/v1/superadmin/dashboard',headers=auth).json
    assert data['pending_requests']['total']==2
    assert {p['role']:p['can_review'] for p in data['pending_requests']['items']}=={'ADMIN':True,'DOCTOR':False}
    results=client.get('/api/v1/superadmin/search?q=100%25',headers=auth).json['items']
    assert len(results)==1 and results[0]['email']=='pending@example.com'
    assert client.get('/api/v1/superadmin/search?q=x',headers=auth).json['items']==[]
    assert client.get('/api/v1/superadmin/search?q=Example').status_code==401
    filtered=client.get('/api/v1/superadmin/admins?search=pending@example.com',headers=auth).json
    assert filtered['total']==1
    # Superadmin can review administrators, not doctor accounts.
    assert client.post(f'/api/v1/admin/doctors/{doctor_id}/approve',headers=auth,json={}).status_code==403


def test_admin_dashboard_only_reviews_doctors(app,client):
    create_account(app,'ADMIN','reviewer@example.com')
    create_account(app,'ADMIN','hidden@example.com')
    doctor_id,_=doctor(app)
    with app.app_context():
        user=db().get(User,doctor_id);user.approval_status='PENDING_APPROVAL'
        db().add(ApprovalRequest(applicant_id=doctor_id,applicant_role='DOCTOR'))
        db().commit()
    auth=bearer(client.post('/api/v1/admin/login',json={'email':'reviewer@example.com','password':PASSWORD}))
    data=client.get('/api/v1/admin/dashboard',headers=auth).json
    assert data['pending_requests']['total']==1
    assert all(p['role']=='DOCTOR' and p['can_review'] for p in data['pending_requests']['items'])
    assert all(c['role'] in ('DOCTOR','PATIENT') for c in data['counts'])
    assert client.get('/api/v1/admin/search?q=hidden',headers=auth).json['items']==[]
