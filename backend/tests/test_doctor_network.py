import pytest
from core.database import db
from core.models import CareProfile, CareReport, now
from test_care import patient, create_profile
from test_referrals import doctor
from test_patient_directory import staff

@pytest.mark.parametrize('role', ['ADMIN','SUPERADMIN'])
def test_doctor_network_scope_and_private_data(app,client,role):
    first,referral=doctor(app)
    other,_=doctor(app,'other-doctor@example.com','D000002')
    owner=patient(app,client)
    account=client.get('/api/v1/patients/me',headers=owner).json['user']
    linked=create_profile(client,owner,full_name='Connected Child',referral_id=referral)
    unlinked=create_profile(client,owner,full_name='Private Sibling')
    other_family=patient(app,client,'other-family@example.com')
    other_id=client.get('/api/v1/patients/me',headers=other_family).json['user']['id']
    with app.app_context():
        db().add(CareReport(profile_id=linked,name='Sensitive report',content_type='application/pdf',content=b'private'))
        db().commit()
    prefix,headers=staff(app,client,role)
    base=f'/api/v1/{prefix}/doctors/{first}'
    result=client.get(base,headers=headers)
    assert result.status_code==200
    assert result.json['dashboard']['connected_profiles']==1
    assert result.json['dashboard']['families']==1
    families=client.get(base+'/families',headers=headers).json
    assert families['total']==1 and families['items'][0]['id']==account['id']
    assert families['items'][0]['connected_profiles']==1
    family_path=base+'/families/'+account['id']
    result=client.get(family_path,headers=headers)
    assert result.status_code==200
    assert [p['id'] for p in result.json['items']]==[linked]
    member_path=family_path+'/profiles/'+linked
    result=client.get(member_path,headers=headers)
    assert result.status_code==200
    assert result.json['items'][0]['family_name']==account['full_name']
    assert not any(word in result.get_data(as_text=True) for word in ('Sensitive report','content_type','guardian_contact','emergency_contacts'))
    for path in (family_path+'/profiles/'+unlinked,base+'/families/'+other_id,base+'/families/not-a-real-family',family_path+'/profiles/not-a-uuid',member_path.replace(first,other)):
        assert client.get(path,headers=headers).status_code==404,path
    assert client.get(member_path,headers=owner).status_code==403
    assert client.get(member_path).status_code==401
    assert client.get(base+'/profiles?module=adult',headers=headers).json['total']==0
    assert client.get(base+'/profiles?search=Connected',headers=headers).json['total']==1
    assert client.get(base+'/profiles?search=Sibling',headers=headers).json['total']==0
    assert client.get(base+'/families?search=unmatched',headers=headers).json['total']==0
    assert client.get(base+'/profiles?module=invalid',headers=headers).status_code==422
    assert client.get(base+'/families?per_page=101',headers=headers).status_code==400
    with app.app_context():
        db().get(CareProfile,linked).referred_doctor_id=None
        db().commit()
    assert client.get(member_path,headers=headers).status_code==404
    assert client.get(base+'/families',headers=headers).json['total']==0


def test_deleted_profiles_excluded_from_network(app,client):
    identifier,referral=doctor(app)
    owner=patient(app,client)
    linked=create_profile(client,owner,referral_id=referral)
    with app.app_context():
        db().get(CareProfile,linked).deleted_at=now()
        db().commit()
    prefix,headers=staff(app,client)
    base=f'/api/v1/{prefix}/doctors/{identifier}'
    assert client.get(base,headers=headers).json['dashboard']['connected_profiles']==0
    assert client.get(base+'/profiles',headers=headers).json['total']==0
    assert client.get(base+'/families',headers=headers).json['total']==0
