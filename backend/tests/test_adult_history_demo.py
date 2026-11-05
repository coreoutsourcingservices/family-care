from datetime import date
from unittest.mock import patch
from sqlalchemy import select
from core.database import db
from core.models import AdultRecord,AdultRecordRevision,ProfilePlanner,CareReport,ReportText
from patient.adult_routes import AdultInput
from scripts.adult_demo_history import entries
from test_care import patient,create_profile,cloud


def test_adult_samples_cover_valid_record_kinds(app):
    with app.app_context():
        rows=entries(date(2026,11,5))
        assert len(rows)==101 and len({key for key,_ in rows})==101
        assert {row['kind'] for _,row in rows}=={'bp','glucose','lipids','medicine','lifestyle','screening','history','reminder'}
        for _,row in rows:
            AdultInput(**row)
            assert row['title'].startswith('DEMO - ') and 'SAMPLE ONLY' in row['notes']


def test_adult_seed_keeps_existing_records_and_skips_duplicates(app,client,cloud):
    from scripts import seed_adult_history
    owner=patient(app,client)
    profile=create_profile(client,owner,module='adult',date_of_birth='1990-01-01')
    saved=client.post(f'/api/v1/patients/adults/{profile}/records',headers=owner,json={'kind':'history','date':'2026-01-01','title':'Existing personal note','notes':'Keep unchanged'})
    assert saved.status_code==201,saved.json
    original=saved.json['record']['id']
    result=dict(original_text='DEMO ADULT Fasting glucose 94 Total cholesterol 182 LDL 102 HDL 54 Triglycerides 126',english_text=None,translation_status='NOT_REQUESTED',page_count=1,warnings=[])
    with patch.object(seed_adult_history,'create_app',return_value=app),patch('services.report_text.run_processor',return_value=result):
        seed_adult_history.seed(profile)
        seed_adult_history.seed(profile)
    with app.app_context():
        records=db().scalars(select(AdultRecord).where(AdultRecord.profile_id==profile)).all()
        assert len(records)==102
        assert db().get(AdultRecord,original).data['notes']=='Keep unchanged'
        assert len(db().scalars(select(AdultRecordRevision).where(AdultRecordRevision.record_id.in_([r.id for r in records]))).all())==102
        assert len(db().scalars(select(ProfilePlanner).where(ProfilePlanner.profile_id==profile)).all())==12
        reports=db().scalars(select(CareReport).where(CareReport.profile_id==profile)).all()
        assert len(reports)==6
        scan=next(r for r in reports if r.category=='Scans')
        assert db().get(ReportText,scan.id) is None
        lab=next(r for r in reports if r.category=='Lab tests')
        assert db().get(ReportText,lab.id).status=='COMPLETED'
    listing=client.get(f'/api/v1/patients/adults/{profile}/records',headers=owner)
    assert listing.status_code==200 and len(listing.json['items'])==102
