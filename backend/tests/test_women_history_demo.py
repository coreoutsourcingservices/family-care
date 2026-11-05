from collections import Counter
from datetime import date
from unittest.mock import patch
from sqlalchemy import select
from core.database import db
from core.models import WomenDiaryRecord, ProfilePlanner, CareReport, ReportText
from services.women_workspace import WomenRecordInput
from scripts.women_demo_history import entries
from test_care import patient, create_profile, cloud


def test_history_examples_cover_all_diary_sections_and_validate(app):
    with app.app_context():
        rows = entries(date(2026, 11, 5))
        assert len(rows) == 93
        assert len({key for key, _, _ in rows}) == len(rows)
        assert set(section for _, section, _ in rows) == {'health','cycle','pcos','pregnancy','fertility','symptoms','nutrition','screening','consultation','checkin','reminder'}
        for _, section, data in rows:
            WomenRecordInput(section=section, data=data, version=0)
            assert data['title'].startswith('DEMO - ')
            assert 'SAMPLE ONLY' in data['notes']


def test_history_seed_preserves_existing_data_and_is_idempotent(app, client, cloud):
    from scripts import seed_women_history
    owner = patient(app, client)
    profile = create_profile(client, owner, module='women', date_of_birth='1990-01-01')
    original_id = 'cb000000-0000-4000-8000-000000000001'
    data = {'date':'2026-01-01','title':'Existing personal entry','notes':'Keep unchanged'}
    assert client.put(f'/api/v1/women/profiles/{profile}/diary/{original_id}', headers=owner, json={'section':'health','data':data,'version':0}).status_code == 200
    result = dict(original_text='DEMO history laboratory report 12.6 2.3 91', english_text=None, translation_status='NOT_REQUESTED', page_count=1, warnings=[])
    with patch.object(seed_women_history, 'create_app', return_value=app), patch('services.report_text.run_processor', return_value=result):
        seed_women_history.seed(profile)
        seed_women_history.seed(profile)
    with app.app_context():
        rows = db().scalars(select(WomenDiaryRecord).where(WomenDiaryRecord.profile_id == profile)).all()
        assert len(rows) == 94
        assert db().get(WomenDiaryRecord, original_id).data == data
        assert len(db().scalars(select(ProfilePlanner).where(ProfilePlanner.profile_id == profile)).all()) == 12
        reports = db().scalars(select(CareReport).where(CareReport.profile_id == profile)).all()
        assert len(reports) == 6
        scan = next(row for row in reports if row.category == 'Scans')
        assert db().get(ReportText, scan.id) is None
        lab = next(row for row in reports if row.category == 'Lab tests')
        assert db().get(ReportText, lab.id).status == 'COMPLETED'
