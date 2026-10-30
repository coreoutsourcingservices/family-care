import io
from unittest.mock import patch
from sqlalchemy import select
from core.database import db
from core.models import DoctorProfile,User
from test_vaccination_management import setup_staff
from test_care import patient,create_profile

def test_photo_crud_private_storage_and_connected_response(app,client):
    admin,doctor,doctor_id=setup_staff(app,client)
    owner=patient(app,client)
    app.config.update(CLOUDINARY_CLOUD_NAME='test',CLOUDINARY_API_KEY='test',CLOUDINARY_API_SECRET='test')
    path='/api/v1/doctors/profile-photo'
    assert client.get(path,headers=owner).status_code==403
    assert client.get(path,headers=doctor).json['photo'] is None
    def upload(*args,**kw):return dict(public_id=kw['public_id'],type='authenticated',resource_type='image',format='png')
    with patch('doctor.onboarding_images.cloudinary.uploader.upload',side_effect=upload),patch('doctor.onboarding_images.cloudinary.uploader.destroy'):
        for method in ('post','put'):
            response=getattr(client,method)(path,headers=doctor,data={'file':(io.BytesIO(b'\x89PNG\r\n\x1a\nimage'),'doctor.png')})
            assert response.status_code==201,response.json
            assert 'profile_photo' in response.json['images']
        assert client.put(path,headers=doctor,data={'file':(io.BytesIO(b'bad'),'bad.png')}).status_code==422
        with app.app_context():
            doc=db().get(User,doctor_id);public=doc.public_id
            referral=db().get(DoctorProfile,doctor_id).referral_id
            assert doc.approval_status=='APPROVED'
        response=client.get('/api/v1/admin/doctors/'+public,headers=admin)
        assert response.status_code==200 and response.json['user']['doctor']['images']['profile_photo']['url']
        child=create_profile(client,owner,referral_id=referral)
        assert client.get('/api/v1/patients/profiles/'+child,headers=owner).json['profile']['doctor']['photo']['url']
        assert client.delete(path,headers=doctor).status_code==200
        assert client.get(path,headers=doctor).json['photo'] is None

def test_single_records_and_disconnect_revoke_doctor_access(app,client):
    admin,doctor,doctor_id=setup_staff(app,client)
    owner=patient(app,client);other=patient(app,client,'other@example.com')
    with app.app_context():referral=db().get(DoctorProfile,doctor_id).referral_id;public=db().get(User,doctor_id).public_id
    child=create_profile(client,owner,referral_id=referral)
    basics='/api/v1/patients/profiles/'+child
    assert client.put(basics,headers=other,json={'full_name':'Wrong owner'}).status_code==404
    assert client.put(basics,headers=owner,json={'full_name':'Updated child','guardian_contact':'+919876543210'}).json['profile']['full_name']=='Updated child'
    assert client.put(basics,headers=owner,json={'full_name':' ','guardian_contact':''}).status_code==422
    path='/api/v1/children/'+child+'/care-notes'
    record=client.post(path,headers=owner,json={'title':'Example note','date':'2026-10-01'}).json['record']
    assert client.get(path+'/'+record['id'],headers=owner).json['record']['title']=='Example note'
    assert client.get(path+'/'+record['id'],headers=other).status_code==404
    assert client.get('/api/v1/admin/doctors/'+public+'/profiles',headers=admin).json['total']==1
    assert client.get('/api/v1/doctors/care-profiles/'+child,headers=doctor).status_code==200
    assert client.delete('/api/v1/patients/profiles/'+child+'/doctor',headers=other).status_code==404
    assert client.delete('/api/v1/patients/profiles/'+child+'/doctor',headers=owner).json['profile']['doctor'] is None
    assert client.get('/api/v1/doctors/care-profiles/'+child,headers=doctor).status_code==404
    adult=create_profile(client,owner,module='adult',date_of_birth='1995-01-01')
    path='/api/v1/patients/adults/'+adult+'/records'
    payload={'kind':'history','title':'Example history','date':'2026-10-01'}
    created=client.post(path,headers=owner,json=payload)
    assert created.status_code==201,created.json
    item=path+'/'+created.json['record']['id']
    assert client.get(item,headers=owner).status_code==200
    assert client.patch(item,headers=owner,json={**payload,'title':'Updated history'}).json['record']['title']=='Updated history'
    assert client.delete(item,headers=owner).status_code==200
    assert client.get(item,headers=owner).status_code==404

def test_openapi_covers_registered_verbs_and_upload_contract(app,client):
    spec=client.get('/api/openapi.json')
    assert spec.status_code==200,spec.json
    paths=spec.json['paths']
    for rule in app.url_map.iter_rules():
        if not rule.rule.startswith('/api/v1'):continue
        import re
        key=re.sub(r'<(?:\w+:)?(\w+)>',r'{\1}',rule.rule)
        assert rule.methods-{'HEAD','OPTIONS'} <= {m.upper() for m in paths[key]}
    photo=paths['/api/v1/doctors/profile-photo']
    assert set(photo)=={'get','post','put','delete'}
    assert 'multipart/form-data' in photo['put']['requestBody']['content']
    assert paths['/api/v1/patients/adults/{profile_id}/records/{record_id}']['patch']['requestBody']['content']['application/json']['schema']
