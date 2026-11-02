from datetime import timedelta
from sqlalchemy import select
from core.database import db
from core.models import User,FamilyInvitation,AdultTabGrant,now
from test_care import patient,create_profile


def test_adult_tab_view_edit_expiry_revoke_and_legacy_bypass(app,client):
    owner=patient(app,client);profile=create_profile(client,owner,kind='self',module='adult',date_of_birth='1990-01-01')
    member=patient(app,client,'member@example.com');member_profile=create_profile(client,member,module='adult',date_of_birth='1991-01-01')
    with app.app_context():
        owner_id=db().scalar(select(User.id).where(User.email=='family@example.com'))
        member_id=db().scalar(select(User.id).where(User.email=='member@example.com'))
        db().add(FamilyInvitation(owner_id=owner_id,member_id=member_id,profile_id=member_profile,token_hash='synthetic-tab-access',email='member@example.com',full_name='Example Member',module='adult',accepted_at=now(),expires_at=now()+timedelta(days=1)))
        db().commit()
    base='/api/v1/adult-access/profiles/'+profile
    response=client.put(base+'/sharing',headers=owner,json={'recipient_id':member_id,'permissions':{'history':'view','medicine':'edit'},'expires_at':None})
    assert response.status_code==200,response.json
    grant=response.json['grant']['id'];assert response.json['grant']['expires_at'] is None
    payload={'kind':'medicine','title':'Existing prescription','date':'2026-01-01','notes':'Synthetic note'}
    assert client.post(base+'/records',headers=member,json=payload).status_code==201
    assert client.post(base+'/records',headers=member,json={**payload,'kind':'history'}).status_code==403
    rows=client.get(base+'/workspace',headers=member).json
    assert len(rows['records'])==1 and rows['records'][0]['kind']=='medicine'
    assert client.get('/api/v1/patients/adults/'+profile+'/records',headers=member).status_code==403
    assert client.get(base+'/reports',headers=member).status_code==403
    assert client.put(base+'/sharing',headers=member,json={'recipient_id':owner_id,'permissions':{'history':'edit'}}).status_code==403
    assert client.get(base+'/history',headers=member).status_code==403
    assert len(client.get(base+'/history',headers=owner).json['items'])==1
    assert client.delete(base+'/sharing/'+grant,headers=owner).status_code==200
    assert client.get(base+'/workspace',headers=member).status_code==403
    assert len(client.get(base+'/history',headers=owner).json['items'])==2
    response=client.put(base+'/sharing',headers=owner,json={'recipient_id':member_id,'permissions':{'history':'view'},'starts_at':(now()+timedelta(days=1)).isoformat()+'Z','expires_at':(now()+timedelta(days=2)).isoformat()+'Z'})
    assert response.status_code==200,response.json
    assert client.get(base+'/workspace',headers=member).status_code==403
    with app.app_context():
        row=db().get(AdultTabGrant,grant);row.starts_at=now()-timedelta(days=2);row.expires_at=now()-timedelta(days=1);db().commit()
    assert client.get(base+'/workspace',headers=member).status_code==403
