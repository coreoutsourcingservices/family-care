from unittest.mock import patch
from sqlalchemy import select
from test_care import patient, create_profile
from conftest import create_account
from test_workflows import bearer, PASSWORD
from core.database import db
from core.models import CareReport, ReportText


def report(app, profile):
    with app.app_context():
        row=CareReport(profile_id=profile,name='Synthetic report.pdf',content_type='application/pdf',storage_provider='database',content=b'%PDF-1.7\nSynthetic',size_bytes=20)
        db().add(row);db().commit();return row.id


def result(translation='NOT_REQUESTED'):
    return dict(engine='PaddleOCR',source_language='hi',original_text='Synthetic extracted text',english_text=None,translation_status=translation,page_count=1,pages=[],warnings=[])


def test_private_report_text_queue_and_cached_results(app,client,monkeypatch):
    import sys
    monkeypatch.setitem(app.config,'OCR_PYTHON',sys.executable)
    owner=patient(app,client);profile=create_profile(client,owner);identifier=report(app,profile);base=f'/api/v1/patients/profiles/{profile}/reports/{identifier}/text'
    assert client.get(base,headers=owner).json['analysis']['status']=='NOT_REQUESTED'
    assert client.post(base,headers=owner,json={'source_language':'hi','translate_to_english':True}).status_code==422
    assert client.post(base,headers=owner,json={'source_language':'unsupported'}).status_code==422
    assert client.post(base,headers=owner,json={'source_language':'hi'}).status_code==202
    assert client.post(base,headers=owner,json={'source_language':'hi'}).status_code==202
    with app.app_context():
        assert len(db().scalars(select(ReportText)).all())==1
        from services.report_text import process_one
        with patch('services.report_text.run_processor',return_value=result()) as runner:
            assert process_one() is True
            assert runner.call_args.args[1]['external_translation_consent'] is False
    done=client.get(base,headers=owner).json['analysis']
    assert done['status']=='COMPLETED' and done['result']['original_text']=='Synthetic extracted text'
    assert client.post(base,headers=owner,json={'source_language':'hi'}).status_code==200
    assert client.post(base,headers=owner,json={'source_language':'hi','translate_to_english':True,'external_translation_consent':True}).status_code==202
    with app.app_context():
        with patch('services.report_text.run_processor',return_value=result('FAILED')):assert process_one() is True
    assert client.get(base,headers=owner).json['analysis']['status']=='PARTIAL'
    assert client.get(base,headers=owner).json['analysis']['result']['original_text']
    stranger=patient(app,client,'another@example.com')
    assert client.get(base,headers=stranger).status_code==404
    assert client.post(base,headers=stranger,json={}).status_code==404
    assert client.get(base).status_code==401
    create_account(app,'ADMIN','admin@example.com')
    admin=bearer(client.post('/api/v1/admin/login',json={'email':'admin@example.com','password':PASSWORD}))
    assert client.get(base,headers=admin).status_code==403


def test_report_text_failure_and_processor_configuration(app,client,monkeypatch):
    owner=patient(app,client);profile=create_profile(client,owner);identifier=report(app,profile);base=f'/api/v1/patients/profiles/{profile}/reports/{identifier}/text'
    monkeypatch.setitem(app.config,'OCR_PYTHON','missing-ocr-runtime')
    assert client.post(base,headers=owner,json={}).status_code==503
    assert client.get('/api/v1/patients/report-text/options',headers=owner).json['configured'] is False
    import sys
    monkeypatch.setitem(app.config,'OCR_PYTHON',sys.executable)
    assert client.post(base,headers=owner,json={}).status_code==202
    with app.app_context():
        from services.report_text import process_one
        with patch('services.report_text.run_processor',side_effect=ValueError('processor_timeout')):assert process_one()
    failure=client.get(base,headers=owner).json['analysis']
    assert failure['status']=='FAILED' and failure['error']['code']=='processor_timeout'


def test_report_download_rejects_untrusted_urls(app,client):
    import pytest
    owner=patient(app,client);profile=create_profile(client,owner);identifier=report(app,profile)
    with app.app_context():
        from services.report_text import report_bytes
        row=db().get(CareReport,identifier)
        assert report_bytes(row).startswith(b'%PDF-')
        row.storage_provider='cloudinary'
        for url in ['http://127.0.0.1/private','https://evil.example/report','https://res.cloudinary.com/another-cloud/report']:
            with patch('services.care_uploads.credentials',return_value={'cloud_name':'test-cloud'}),patch('services.care_uploads.report_data',return_value={'url':url}):
                with pytest.raises(ValueError,match='report_download_failed'):report_bytes(row)


def test_translation_rate_limit_preserves_original_and_allows_local_only(app,client,monkeypatch):
    import sys
    monkeypatch.setitem(app.config,'OCR_PYTHON',sys.executable)
    owner=patient(app,client);profile=create_profile(client,owner);identifier=report(app,profile)
    url=f'/api/v1/patients/profiles/{profile}/reports/{identifier}/text'
    options=dict(source_language='hi',translate_to_english=True,external_translation_consent=True)
    assert client.post(url,headers=owner,json=options).status_code==202
    limited={**result('FAILED'),'translation_error':{'code':'translation_rate_limited','message':'Temporarily unavailable'}}
    with app.app_context():
        from services.report_text import process_one
        with patch('services.report_text.run_processor',return_value=limited):assert process_one()
    assert client.post(url,headers=owner,json=options).status_code==429
    assert client.get(url,headers=owner).json['analysis']['result']['original_text']
    assert client.post(url,headers=owner,json={'source_language':'hi'}).status_code==202
