"""Add labelled samples to an explicitly selected women's profile; existing entries stay intact."""
import argparse
import io
from datetime import date, timedelta
from pathlib import Path
from uuid import uuid5, NAMESPACE_URL
from flask import g
from sqlalchemy import select
from app import create_app
from core.database import db
from core.models import CareProfile, User, WomenDiaryRecord, CareReport, ReportText, uid, now
from services.women_workspace import primary_id, put_record, reports


def seed(profile_id):
    app = create_app()
    with app.app_context():
        profile = db().get(CareProfile, profile_id)
        if not profile or profile.deleted_at or profile.module != 'women':
            raise RuntimeError('Choose an active women profile')
        actor = db().get(User, primary_id(profile))
        if not actor or actor.role != 'PATIENT' or actor.account_status != 'ACTIVE':
            raise RuntimeError('Profile primary account is unavailable')
        actor_id, name = actor.id, profile.name
        day = lambda offset: (date.today() + timedelta(days=offset)).isoformat()
        items = [
            ('health', dict(title='DEMO - General health note', category='General health', notes='DEMO ONLY: synthetic workspace preview; no diagnosis.')),
            ('cycle', dict(title='DEMO - Example cycle', date=day(-32), end=day(-28), flow='Medium', symptoms='Mild cramps', notes='DEMO ONLY: not an actual recorded period.')),
            ('cycle', dict(title='DEMO - Recent example cycle', date=day(-4), end=day(0), flow='Light', notes='DEMO ONLY: not an actual recorded period.')),
            ('pcos', dict(title='DEMO - Questions for clinician', category='Symptoms', severity='Mild', notes='DEMO ONLY: example questions about cycle history; no diagnosis.')),
            ('fertility', dict(title='DEMO - Consultation questions', category='Question for doctor', notes='DEMO ONLY: sample question list.')),
            ('symptoms', dict(title='DEMO - Wellbeing journal', severity='Mild', notes='DEMO ONLY: example diary about a busy day.')),
            ('nutrition', dict(title='DEMO - Meal journal', category='Meals', notes='DEMO ONLY: rice, dal, vegetables and fruit.')),
            ('nutrition', dict(title='DEMO - Movement journal', category='Movement', notes='DEMO ONLY: example evening walk.')),
            ('screening', dict(title='DEMO - Screening questions', category='Other screening', status='Planned', next=day(14), notes='DEMO ONLY: ask a clinician about an appropriate screening schedule.')),
            ('reminder', dict(title='DEMO - Prepare questions for visit', date=day(2), status='Planned')),
        ]
        added = skipped = 0
        for index, (section, values) in enumerate(items):
            identifier = str(uuid5(NAMESPACE_URL, f'familycare:women-demo:{profile_id}:{index}'))
            if db().get(WomenDiaryRecord, identifier):
                skipped += 1
                continue
            values = dict(date=day(0)) | values
            if section == 'cycle':
                existing = db().scalars(select(WomenDiaryRecord).where(WomenDiaryRecord.profile_id == profile_id, WomenDiaryRecord.section == 'cycle', WomenDiaryRecord.deleted_at.is_(None))).all()
                if any(values['date'] <= (row.data.get('end') or row.data['date']) and values['end'] >= row.data['date'] for row in existing):
                    skipped += 1
                    continue
            with app.test_request_context(method='PUT', json=dict(section=section, data=values, version=0)):
                g.user = db().get(User, actor_id)
                put_record(profile_id, identifier)
            added += 1
        report = db().scalar(select(CareReport).where(CareReport.profile_id == profile_id, CareReport.name == 'demo-women-lab-report.pdf', CareReport.deleted_at.is_(None)))
        if not report:
            source = Path(__file__).resolve().parents[2] / 'app/public/demo/women/demo-women-lab-report.pdf'
            with app.test_request_context(method='POST', data={'file': (io.BytesIO(source.read_bytes()), source.name), 'title': 'DEMO - Sample OCR laboratory report', 'category': 'Lab tests', 'source_language': 'en', 'auto_read': 'false'}):
                g.user = db().get(User, actor_id)
                response, status = reports(profile_id)
                if status != 201:
                    raise RuntimeError('Sample report upload failed')
                identifier = response.get_json()['report']['id']
            report = db().get(CareReport, identifier)
        identifier = report.id
        job = db().get(ReportText, identifier)
        if not job or job.status not in ('COMPLETED', 'PROCESSING'):
            from services.report_text import Options, run_processor
            options = Options(source_language='en', auto_import=False).model_dump(mode='json')
            if not job:
                job = ReportText(report_id=identifier, requested_by=actor_id, options=options)
                db().add(job)
            lease = uid()
            job.status, job.options, job.lease_id, job.started_at, job.error_code = 'PROCESSING', options, lease, now(), None
            db().commit()
            try:
                result = run_processor(db().get(CareReport, identifier), options)
                db().expire_all()
                job = db().get(ReportText, identifier)
                if job.lease_id == lease:
                    job.result, job.status, job.error_code = result, 'COMPLETED', None
                    db().commit()
            except Exception:
                db().rollback()
                job = db().get(ReportText, identifier)
                if job.lease_id == lease:
                    job.status, job.error_code = 'FAILED', 'processing_failed'
                    db().commit()
                raise RuntimeError('Report saved, but OCR failed; retry reading from Medical records') from None
        job = db().get(ReportText, identifier)
        print(dict(profile=name, profile_id=profile_id, demo_entries_added=added, entries_skipped=skipped, report_id=identifier, report_text_status=job.status, expected_values_read=all(value in (job.result or {}).get('original_text', '') for value in ['12.4', '2.1', '89'])))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--profile-id', required=True)
    seed(parser.parse_args().profile_id)
