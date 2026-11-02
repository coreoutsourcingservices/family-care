from test_care import patient


def test_private_notes_crud_and_owner_isolation(app,client):
    owner=patient(app,client)
    other=patient(app,client,'other@example.com')
    response=client.post('/api/v1/patients/notes',headers=owner,json={'title':'Ask at next visit','body':'Synthetic personal reminder'})
    assert response.status_code==201,response.json
    note=response.json['note'];path='/api/v1/patients/notes/'+note['id']
    assert client.get('/api/v1/patients/notes',headers=owner).json['items'][0]['body']=='Synthetic personal reminder'
    assert client.get('/api/v1/patients/notes',headers=other).json['items']==[]
    assert client.put(path,headers=other,json={'title':'Blocked','body':'Blocked'}).status_code==404
    assert client.delete(path,headers=other).status_code==404
    assert client.put(path,headers=owner,json={'title':'Updated','body':'Updated personal reminder'}).status_code==200
    assert client.post('/api/v1/patients/notes',headers=owner,json={'title':' ','body':'x'}).status_code==422
    assert client.delete(path,headers=owner).status_code==200
    assert client.get('/api/v1/patients/notes',headers=owner).json['items']==[]
    assert client.get('/api/v1/patients/notes?page=0',headers=owner).status_code==422
