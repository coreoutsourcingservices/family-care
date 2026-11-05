import io
import sys
from unittest.mock import patch
from sqlalchemy import select
from core.database import db
from core.models import ChildRecord,ReportText
from test_care import cloud,patient,create_profile


def test_upload_extracts_and_requires_explicit_review_without_duplicates(app,client,cloud,monkeypatch):
    monkeypatch.setitem(app.config,'OCR_PYTHON',sys.executable)
    owner=patient(app,client);profile=create_profile(client,owner)
    response=client.post(f'/api/v1/patients/profiles/{profile}/reports',headers=owner,data={
        'file':(io.BytesIO(b'%PDF-1.7 synthetic'),'synthetic.pdf'),'category':'Doctor report','auto_read':'true','source_language':'en'})
    assert response.status_code==201
    identifier=response.json['report']['id'];base=f'/api/v1/patients/profiles/{profile}/reports/{identifier}'
    assert client.get(base+'/text',headers=owner).json['analysis']['status']=='QUEUED'
    result=dict(original_text='Report date: 2026-01-01\nDiagnosis: Synthetic example\nRx\nTab Example - test only\nWeight: 18 kg\nHeight: 110 cm\nDiet: Example nutrition\nVaccination: Example dose',english_text=None,translation_status='NOT_REQUESTED',page_count=1,warnings=[])
    with app.app_context():
        from services.report_text import process_one
        with patch('services.report_text.run_processor',return_value=result):assert process_one()
        rows=db().scalars(select(ChildRecord).where(ChildRecord.profile_id==profile)).all()
        assert rows==[]
        job=db().get(ReportText,identifier);job.status='QUEUED';db().commit()
        with patch('services.report_text.run_processor',return_value=result):assert process_one()
        assert db().scalars(select(ChildRecord).where(ChildRecord.profile_id==profile)).all()==[]
    reviewed=client.post(base+'/import',headers=owner,json={'kind':'history','reviewed':True,'record':{'title':'Reviewed report','date':'2026-01-01','notes':'Owner correction'}})
    assert reviewed.status_code==201 and reviewed.json['record']['reviewed'] is True
    with patch('cloudinary.uploader.destroy',return_value={'result':'ok'}):
        assert client.delete(base,headers=owner).status_code==200
    assert client.get(f'/api/v1/children/{profile}/records',headers=owner).json['items']==[]


def test_imaging_upload_never_queues_reading(app,client,cloud):
    owner=patient(app,client);profile=create_profile(client,owner)
    response=client.post(f'/api/v1/patients/profiles/{profile}/reports',headers=owner,data={
        'file':(io.BytesIO(b'%PDF-1.7 synthetic'),'synthetic.pdf'),'category':'Scans','auto_read':'true'})
    assert response.status_code==201
    with app.app_context():assert db().get(ReportText,response.json['report']['id']) is None
