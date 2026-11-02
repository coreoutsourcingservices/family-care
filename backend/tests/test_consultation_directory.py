from datetime import timedelta
from sqlalchemy import select
from core.database import db
from core.models import User,DoctorReview,now
from test_care import patient,create_profile
from test_referrals import doctor
from test_workflows import bearer,PASSWORD


def test_directory_request_completion_real_rating_and_isolation(app,client):
    owner=patient(app,client);profile=create_profile(client,owner,kind='self',module='adult',date_of_birth='1990-01-01')
    first,_=doctor(app);second,_=doctor(app,'second@example.com','D000002');doctor(app,'pending@example.com','D000003',approved=False)
    listing=client.get('/api/v1/patients/doctor-directory',headers=owner)
    assert listing.status_code==200,listing.json
    assert listing.json['total']==2
    assert all(row['rating'] is None and row['review_count']==0 for row in listing.json['items'])
    endpoint='/api/v1/patients/profiles/'+profile+'/consultations'
    response=client.post(endpoint,headers=owner,json={'doctor_id':second,'concern':'General health','requested_at':(now()+timedelta(days=1)).isoformat()+'Z'})
    assert response.status_code==201,response.json
    visit=response.json['consultation']['id']
    review='/api/v1/patients/doctor-directory/'+second+'/review'
    payload={'consultation_id':visit,'rating':5,'comment':'Synthetic consultation review'}
    assert client.put(review,headers=owner,json=payload).status_code==403
    clinician=bearer(client.post('/api/v1/doctors/login',json={'email':'second@example.com','password':PASSWORD}))
    other_clinician=bearer(client.post('/api/v1/doctors/login',json={'email':'rahul@example.com','password':PASSWORD}))
    status='/api/v1/doctors/consultation-visits/'+visit+'/status'
    assert client.patch(status,headers=other_clinician,json={'status':'CONFIRMED'}).status_code==404
    assert client.patch(status,headers=clinician,json={'status':'COMPLETED'}).status_code==409
    assert client.patch(status,headers=clinician,json={'status':'CONFIRMED'}).status_code==200
    assert client.patch(status,headers=clinician,json={'status':'COMPLETED'}).status_code==200
    outsider=patient(app,client,'outsider@example.com')
    assert client.put(review,headers=outsider,json=payload).status_code==403
    assert client.get(endpoint,headers=outsider).status_code==404
    assert client.put(review,headers=owner,json={**payload,'rating':6}).status_code==422
    assert client.put(review,headers=owner,json=payload).status_code==200
    assert client.put(review,headers=owner,json={**payload,'rating':4}).status_code==200
    listing=client.get('/api/v1/patients/doctor-directory',headers=owner).json['items']
    assert listing[0]['id']==second and listing[0]['rating']==4 and listing[0]['review_count']==1
    with app.app_context():assert len(db().scalars(select(DoctorReview)).all())==1
