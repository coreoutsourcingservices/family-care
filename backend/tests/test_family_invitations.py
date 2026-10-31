from datetime import timedelta
from urllib.parse import unquote
import pytest
from sqlalchemy import select, func
from core.database import db
from core.models import FamilyInvitation, User, OTPChallenge, now
from services.otp import otp_code
from test_care import patient, create_profile
from test_workflows import bearer


@pytest.fixture
def mails(monkeypatch):
    messages=[]
    monkeypatch.setattr('services.family_invitations.send_mail',lambda destination,subject,body,message_id:messages.append((destination,subject,body)))
    return messages


def invite(client,owner,mails,module='adult',email='member@example.com'):
    response=client.post('/api/v1/patients/family-invitations',headers=owner,
        json=dict(full_name='Example Member',email=email,module=module))
    assert response.status_code==201,response.json
    token=unquote(mails[-1][2].split('#token=')[1].split('\n')[0])
    return response.json['invitation'],token


def setup_data(email='member@example.com'):
    return dict(full_name='Example Member',email=email,mobile_number='+919876543211',date_of_birth='1995-02-28',password='MemberPassword8!',confirm_password='MemberPassword8!')


@pytest.mark.parametrize('module',['adult','women'])
def test_family_member_join_login_shared_profile_and_own_reset(app,client,mails,module,monkeypatch):
    owner=patient(app,client)
    private=create_profile(client,owner)
    row,token=invite(client,owner,mails,module)
    assert mails[-1][0]=='member@example.com'
    assert row['relationship']=='Family member'
    assert 'token' not in str(row)
    base='/api/v1/family-invitations/'+token
    preview=client.get(base).json
    assert preview['form']['email']=='member@example.com'
    assert preview['family']['email']=='family@example.com'
    assert client.post(base+'/setup',json={**setup_data(),'email':'changed@example.com'}).status_code==422
    response=client.post(base+'/setup',json=setup_data())
    assert response.status_code==202,response.json
    assert mails[-1][0]=='family@example.com'
    with app.app_context():
        saved=db().get(FamilyInvitation,row['id'])
        assert saved.token_hash!=token and len(saved.token_hash)==64
        assert db().scalar(select(User).where(User.email=='member@example.com')) is None
        assert 'password' not in saved.pending and 'password_hash' in saved.pending
        code=otp_code(saved.pending['cid'])
    assert client.post(base+'/resend-otp',json={}).status_code==429
    assert client.post(base+'/verify-otp',json={'otp':'000000' if code!='000000' else '111111'}).status_code==400
    response=client.post(base+'/verify-otp',json={'otp':code})
    assert response.status_code==201,response.json
    profile=response.json['profile']['id']
    assert client.post(base+'/verify-otp',json={'otp':code}).status_code==410
    assert client.get(base).status_code==410
    login=client.post('/api/v1/patients/login',json={'email':'member@example.com','password':'MemberPassword8!'})
    assert login.status_code==200,login.json
    member=bearer(login)
    listing=client.get('/api/v1/patients/profiles',headers=member).json
    assert [p['id'] for p in listing['items']]==[profile]
    assert listing['items'][0]['member_email']=='member@example.com'
    assert client.get('/api/v1/patients/profiles/'+private,headers=member).status_code==404
    assert client.get('/api/v1/patients/profiles/'+profile,headers=owner).status_code==200
    outsider=patient(app,client,'other@example.com')
    assert client.get('/api/v1/patients/profiles/'+profile,headers=outsider).status_code==404
    if module=='adult':
        body=dict(kind='history',title='Shared member record',date='2026-01-01',notes='Synthetic test')
        assert client.post('/api/v1/patients/adults/'+profile+'/records',headers=member,json=body).status_code==201
        assert client.get('/api/v1/patients/adults/'+profile+'/records',headers=owner).json['items'][0]['title']==body['title']
    reset=client.post('/api/v1/auth/forgot-password',json={'email':'member@example.com'})
    assert reset.status_code==202,reset.json
    reset_mail=[]
    monkeypatch.setattr('services.email.send_mail',lambda destination,subject,body,message_id:reset_mail.append(destination))
    with app.app_context():
        from services.email import process_one
        assert process_one()
    assert reset_mail==['member@example.com']
    with app.app_context():
        user=db().scalar(select(User).where(User.email=='member@example.com'))
        challenge=db().scalar(select(OTPChallenge).where(OTPChallenge.user_id==user.id,OTPChallenge.purpose=='reset_password'))
        assert challenge is not None
        reset_code=otp_code(challenge.id)
    response=client.post('/api/v1/auth/reset-password',json=dict(challenge_token=reset.json['challenge_token'],otp=reset_code,new_password='ChangedPassword8!',confirm_password='ChangedPassword8!'))
    assert response.status_code==200,response.json
    assert client.post('/api/v1/patients/login',json={'email':'member@example.com','password':'ChangedPassword8!'}).status_code==200


def test_invitation_expiry_revocation_limits_and_delivery_failures(app,client,mails,monkeypatch):
    owner=patient(app,client)
    row,token=invite(client,owner,mails)
    assert client.post('/api/v1/patients/family-invitations',headers=owner,json=dict(full_name='Again',email='member@example.com',module='women')).status_code==409
    other=patient(app,client,'stranger@example.com')
    assert client.delete('/api/v1/patients/family-invitations/'+row['id'],headers=other).status_code==404
    assert client.post('/api/v1/family-invitations/'+token+'/setup',json={**setup_data(),'date_of_birth':'2020-01-01'}).status_code==422
    assert client.delete('/api/v1/patients/family-invitations/'+row['id'],headers=owner).status_code==200
    assert client.get('/api/v1/family-invitations/'+token).status_code==410
    row,token=invite(client,owner,mails)
    with app.app_context():
        db().get(FamilyInvitation,row['id']).expires_at=now()-timedelta(seconds=1);db().commit()
    assert client.get('/api/v1/family-invitations/'+token).status_code==410
    assert client.get('/api/v1/family-invitations/invalid').status_code==404
    def fail(*args):raise RuntimeError('SMTP unavailable')
    monkeypatch.setattr('services.family_invitations.send_mail',fail)
    assert client.post('/api/v1/patients/family-invitations',headers=owner,json=dict(full_name='Member',email='failure@example.com',module='adult')).status_code==503
    with app.app_context():assert db().scalar(select(func.count()).select_from(FamilyInvitation).where(FamilyInvitation.email=='failure@example.com'))==0


def test_invite_otp_attempt_limit_and_resend_invalidates_old_code(app,client,mails):
    owner=patient(app,client);row,token=invite(client,owner,mails)
    base='/api/v1/family-invitations/'+token
    assert client.post(base+'/setup',json=setup_data()).status_code==202
    with app.app_context():
        pending=db().get(FamilyInvitation,row['id']).pending
        old=otp_code(pending['cid'])
    for _ in range(5):
        assert client.post(base+'/verify-otp',json={'otp':'000000' if old!='000000' else '111111'}).status_code==400
    assert client.post(base+'/verify-otp',json={'otp':old}).status_code==400
    with app.app_context():
        row=db().get(FamilyInvitation,row['id']);row.pending={**row.pending,'sent_at':row.pending['sent_at']-61};db().commit()
    assert client.post(base+'/resend-otp',json={}).status_code==202
    with app.app_context():
        saved=db().scalar(select(FamilyInvitation).where(FamilyInvitation.email=='member@example.com'));code=otp_code(saved.pending['cid'])
    if old!=code:assert client.post(base+'/verify-otp',json={'otp':old}).status_code==400
    assert client.post(base+'/verify-otp',json={'otp':code}).status_code==201
