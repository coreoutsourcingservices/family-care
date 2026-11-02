from datetime import timedelta
import pytest
from sqlalchemy import select
from core.database import db
from core.models import AppNotification, now
from test_care import patient, create_profile
from services.profile_planner import scan_tasks

@pytest.mark.parametrize('module',['adult','women'])
def test_notes_tasks_notifications(app,client,module):
    headers=patient(app,client)
    profile=create_profile(client,headers,module=module,date_of_birth='1995-02-10')
    root=f'/api/v1/patients/profiles/{profile}/planner'
    note=client.post(root,json={'kind':'note','title':'Question','body':'For my next visit'},headers=headers)
    assert note.status_code==201,note.json
    due=(now()-timedelta(minutes=1)).isoformat()+'Z'
    task=client.post(root,json={'kind':'task','title':'My task','due_at':due},headers=headers)
    assert task.status_code==201,task.json
    entry=task.json['entry']
    entry={k:v for k,v in entry.items() if k not in ('completed_at',)}
    entry_id=entry.pop('id')
    assert len(client.get(root,headers=headers).json['items'])==2
    with app.app_context():
        scan_tasks();scan_tasks()
        notices=db().scalars(select(AppNotification).where(AppNotification.kind=='task_due')).all()
        assert len(notices)==1
        assert notices[0].data['profile_id']==profile
        assert notices[0].data['module']==module
    complete=client.put(root+'/'+entry_id,json={**entry,'completed':True},headers=headers)
    assert complete.status_code==200,complete.json
    assert client.put(root+'/'+entry_id,json=entry,headers=headers).status_code==409
    with app.app_context():
        scan_tasks()
        notices=db().scalars(select(AppNotification).where(AppNotification.kind=='task_due')).all()
        assert len(notices)==1 and notices[0].read_at
        assert db().scalar(select(AppNotification).where(AppNotification.kind=='task_completed'))
    other=patient(app,client,email='other@example.com')
    assert client.get(root,headers=other).status_code==404
    assert client.put(root+'/'+entry_id,json=entry,headers=other).status_code==404
    assert client.delete(root+'/'+entry_id,headers=headers).status_code==200
    assert client.post(root,json={'kind':'task','title':'No time'},headers=headers).status_code==422
    assert client.post(root,json={'kind':'task','title':'No zone','due_at':'2026-11-05T10:00'},headers=headers).status_code==422

def test_future_and_deleted_tasks_do_not_notify(app,client):
    headers=patient(app,client)
    profile=create_profile(client,headers,module='adult',date_of_birth='1990-01-01')
    root=f'/api/v1/patients/profiles/{profile}/planner'
    client.post(root,json={'kind':'task','title':'Future','due_at':(now()+timedelta(days=1)).isoformat()+'Z'},headers=headers)
    entry=client.post(root,json={'kind':'task','title':'Removed','due_at':(now()-timedelta(minutes=1)).isoformat()+'Z'},headers=headers).json['entry']
    client.delete(root+'/'+entry['id'],headers=headers)
    with app.app_context():
        scan_tasks()
        assert not db().scalar(select(AppNotification).where(AppNotification.kind=='task_due'))
