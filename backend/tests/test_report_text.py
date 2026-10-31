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


def test_imaging_skips_ocr_and_selected_translation_needs_consent(app,client,monkeypatch):
    import sys
    monkeypatch.setitem(app.config,'OCR_PYTHON',sys.executable)
    owner=patient(app,client);profile=create_profile(client,owner);identifier=report(app,profile)
    base=f'/api/v1/patients/profiles/{profile}/reports/{identifier}'
    assert client.patch(base+'/category',headers=owner,json={'category':'Scans'}).status_code==200
    assert client.post(base+'/text',headers=owner,json={}).json['error']['code']=='imaging_ocr_skipped'
    assert client.patch(base+'/category',headers=owner,json={'category':'Lab tests'}).status_code==200
    options={'source_language':'en','target_language':'hi','translate':True}
    assert client.post(base+'/text',headers=owner,json=options).status_code==422
    assert client.post(base+'/text',headers=owner,json={**options,'external_translation_consent':True}).status_code==202
    with app.app_context():
        assert db().get(ReportText,identifier).options['target_language']=='hi'


def test_report_delete_removes_extraction_and_only_linked_imports(app,client):
    from core.models import ChildRecord
    owner=patient(app,client);profile=create_profile(client,owner);identifier=report(app,profile)
    with app.app_context():
        from core.models import CareProfile
        db().add(ReportText(report_id=identifier,requested_by=db().get(CareProfile,profile).owner_id,options={},status='COMPLETED',result=result()))
        linked=ChildRecord(profile_id=profile,kind='growth',data={'source_report_id':identifier,'title':'Imported'})
        manual=ChildRecord(profile_id=profile,kind='growth',data={'title':'Manual'})
        db().add_all([linked,manual]);db().commit();linked_id=linked.id;manual_id=manual.id
    base=f'/api/v1/patients/profiles/{profile}/reports/{identifier}'
    stranger=patient(app,client,'delete-stranger@example.com')
    assert client.delete(base,headers=stranger).status_code==404
    assert client.delete(base,headers=owner).status_code==200
    assert client.get(base+'/text',headers=owner).status_code==404
    assert client.get(base+'/download',headers=owner).status_code==404
    with app.app_context():
        assert db().get(CareReport,identifier) is None
        assert db().get(ReportText,identifier) is None
        assert db().get(ChildRecord,linked_id).deleted_at is not None
        assert db().get(ChildRecord,manual_id).deleted_at is None


def test_delete_cloud_failure_keeps_report(app,client):
    owner=patient(app,client);profile=create_profile(client,owner);identifier=report(app,profile)
    with app.app_context():
        row=db().get(CareReport,identifier);row.storage_provider='cloudinary';row.cloudinary_public_id='synthetic';row.resource_type='image';db().commit()
    base=f'/api/v1/patients/profiles/{profile}/reports/{identifier}'
    with patch('services.care_uploads.credentials',return_value={}),patch('cloudinary.uploader.destroy',side_effect=RuntimeError()):
        assert client.delete(base,headers=owner).status_code==502
    with app.app_context():assert db().get(CareReport,identifier) is not None


def test_processor_translates_to_selected_language(monkeypatch,tmp_path):
    from scripts import ocr_processor
    monkeypatch.setattr(ocr_processor,'extract',lambda *_:[{'text':'Synthetic report'}])
    with patch.object(ocr_processor,'translate',return_value='Synthetic Hindi translation') as translated:
        data=ocr_processor.process(tmp_path/'synthetic.png','en',True,'hi')
        translated.assert_called_once_with('Synthetic report','en','hi')
    assert data['target_language']=='hi'
    assert data['translated_text']=='Synthetic Hindi translation'
    assert data['english_text'] is None


def test_cookie_report_download_and_delete_use_patient_portal(app,client):
    from test_public_portal_sessions import headers
    create_account(app,'PATIENT','cookie-report@example.com')
    response=client.post('/api/v1/patients/login',headers=headers('patient'),json={'email':'cookie-report@example.com','password':PASSWORD})
    ph=headers('patient',response.json['csrf_token'])
    profile=create_profile(client,ph);identifier=report(app,profile)
    base=f'/api/v1/patients/profiles/{profile}/reports/{identifier}'
    assert client.get(base+'/download',headers=ph).status_code==200
    assert client.delete(base,headers={**ph,'X-CSRF-Token':'stale'}).status_code==403
    assert client.get(base+'/download',headers=ph).status_code==200
    assert client.delete(base,headers=ph).status_code==200


def test_report_history_and_prescription_imports_are_separate_and_idempotent(app,client):
    from core.models import CareProfile,ChildRecord
    owner=patient(app,client);profile=create_profile(client,owner);identifier=report(app,profile)
    base=f'/api/v1/patients/profiles/{profile}/reports/{identifier}'
    payload={'kind':'prescription','reviewed':True,'record':{'title':'Synthetic prescription','date':'2026-01-01','notes':'Synthetic medicine text from report'}}
    assert client.post(base+'/import',headers=owner,json=payload).status_code==409
    with app.app_context():
        db().add(ReportText(report_id=identifier,requested_by=db().get(CareProfile,profile).owner_id,options={},status='COMPLETED',result=result()));db().commit()
    rx=client.post(base+'/import',headers=owner,json=payload)
    assert rx.status_code==201
    assert rx.json['record']['kind']=='history'
    assert rx.json['record']['category']=='Medicine'
    assert rx.json['record']['source_role']=='PATIENT'
    assert client.post(base+'/import',headers=owner,json=payload).json['already_imported'] is True
    history=client.post(base+'/import',headers=owner,json={**payload,'kind':'history'})
    assert history.status_code==201 and history.json['record']['id']!=rx.json['record']['id']
    assert client.delete(base,headers=owner).status_code==200
    with app.app_context():
        assert db().get(ChildRecord,rx.json['record']['id']).deleted_at is not None
        assert db().get(ChildRecord,history.json['record']['id']).deleted_at is not None
