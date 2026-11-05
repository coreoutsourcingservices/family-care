import io
import sys
from sqlalchemy import select
from core.database import db
from core.models import CareReport, ReportText
from test_care import cloud, patient, create_profile


def test_report_is_saved_when_optional_ocr_is_unavailable(app, client, cloud, monkeypatch, tmp_path):
    monkeypatch.setitem(app.config, 'OCR_PYTHON', str(tmp_path / 'missing-python.exe'))
    owner = patient(app, client)
    profile = create_profile(client, owner)
    response = client.post(f'/api/v1/patients/profiles/{profile}/reports', headers=owner, data={
        'file': (io.BytesIO(b'%PDF-1.7 synthetic report'), 'first.pdf'),
        'category': 'Doctor report', 'auto_read': 'true', 'source_language': 'en'})
    assert response.status_code == 201, response.json
    assert response.json['text_extraction']['status'] == 'UNAVAILABLE'
    identifier = response.json['report']['id']
    with app.app_context():
        assert db().get(CareReport, identifier) is not None
        assert db().get(ReportText, identifier) is None
    # The existing reading endpoint can be used later, after OCR is available.
    monkeypatch.setitem(app.config, 'OCR_PYTHON', sys.executable)
    retry = client.post(f'/api/v1/patients/profiles/{profile}/reports/{identifier}/text',
                        headers=owner, json={'source_language': 'en'})
    assert retry.status_code == 202
    with app.app_context():
        assert db().get(ReportText, identifier).status == 'QUEUED'


def test_many_independent_reports_keep_earlier_files_after_one_fails(app, client, cloud):
    owner = patient(app, client)
    profile = create_profile(client, owner)
    path = f'/api/v1/patients/profiles/{profile}/reports'
    identifiers = []
    for index in range(15):
        content = b'invalid document' if index == 6 else b'%PDF-1.7 synthetic report'
        response = client.post(path, headers=owner, data={
            'file': (io.BytesIO(content), f'report-{index}.pdf'), 'category': 'Lab tests'})
        if index == 6:
            assert response.status_code == 422
        else:
            assert response.status_code == 201, response.json
            identifiers.append(response.json['report']['id'])
    assert len(set(identifiers)) == 14
    # Lists remain paginated; a multi-file UI sends one request per private report.
    first = client.get(path+'?page=1&per_page=10', headers=owner).json
    second = client.get(path+'?page=2&per_page=10', headers=owner).json
    assert first['total'] == second['total'] == 14
    assert len(first['items']) == 10 and len(second['items']) == 4
    assert {row['id'] for row in first['items'] + second['items']} == set(identifiers)
    with app.app_context():
        assert len(db().scalars(select(CareReport).where(CareReport.profile_id == profile)).all()) == 14
