"""Populate full labelled demo history on an explicitly selected women's profile."""
import argparse
import io
from collections import Counter
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
from pathlib import Path
from uuid import uuid5, NAMESPACE_URL
from flask import g
from sqlalchemy import select
from app import create_app
from core.database import db
from core.models import CareProfile, User, WomenDiaryRecord, ProfilePlanner, CareReport, ReportText, uid, now
from services.women_workspace import primary_id, WomenRecordInput, reports
from services.repository import audit
from scripts.women_demo_history import entries


def seed(profile_id):
    app = create_app()
    anchor = datetime.now(ZoneInfo('Asia/Kolkata')).date()
    with app.app_context():
        profile = db().get(CareProfile, profile_id)
        if not profile or profile.deleted_at or profile.module != 'women':
            raise RuntimeError('Select an active women profile')
        actor = db().get(User, primary_id(profile))
        if not actor or actor.role != 'PATIENT' or actor.account_status != 'ACTIVE':
            raise RuntimeError('Profile primary account is unavailable')
        actor_id, owner_id, name = actor.id, profile.owner_id, profile.name
        existing = db().scalars(select(WomenDiaryRecord).where(WomenDiaryRecord.profile_id == profile_id)).all()
        identifiers = {row.id for row in existing}
        periods = [row.data for row in existing if row.section == 'cycle' and not row.deleted_at]
        added, skipped = Counter(), Counter()
        for key, section, data in entries(anchor):
            identifier = str(uuid5(NAMESPACE_URL, f'familycare:women-history-v2:{profile_id}:{key}'))
            if identifier in identifiers:
                skipped['existing'] += 1
                continue
            value = WomenRecordInput(section=section, data=data, version=0)
            if data['date'] < profile.dob.isoformat():
                skipped['before_birth'] += 1
                continue
            if section == 'cycle':
                if any(data['date'] <= (row.get('end') or row['date']) and data['end'] >= row['date'] for row in periods):
                    skipped['overlap'] += 1
                    continue
                periods.append(data)
            db().add(WomenDiaryRecord(id=identifier, profile_id=profile_id, section=section, data=value.data, version=1, updated_by=actor_id))
            audit('women_diary_saved', owner_id, actor_id)
            added[section] += 1
        db().commit()
        print({'profile': name, 'history_added': dict(added), 'skipped': dict(skipped)}, flush=True)

        # Only this account's private planner is populated. No sharing grants or real bookings.
        previous = db().scalars(select(ProfilePlanner).where(ProfilePlanner.profile_id == profile_id, ProfilePlanner.user_id == actor_id)).all()
        titles = {row.title for row in previous}
        planner_added = 0
        for i in range(6):
            for kind in ('note', 'task'):
                title = f'DEMO - Historical {kind} {i+1}'
                if title in titles:
                    continue
                created = datetime.combine(anchor-timedelta(days=120-i*18), datetime.min.time())
                due = datetime.combine(anchor+timedelta(days=i+2), datetime.min.time()) if i>=4 else created+timedelta(days=2)
                row = ProfilePlanner(profile_id=profile_id, user_id=actor_id, kind=kind, title=title,
                    body='DEMO / SAMPLE ONLY. '+('Fictional previous diary summary and questions for a future visit.' if kind=='note' else 'Example private task: organize sample records and prepare questions.'),
                    due_at=due if kind=='task' else None, completed_at=due if kind=='task' and i<4 else None,
                    version=1, created_at=created, updated_at=created)
                db().add(row)
                audit('planner_created', actor_id, actor_id)
                planner_added += 1
        db().commit()
        print({'planner_added': planner_added}, flush=True)

        categories = [('history-lab','Lab tests'),('history-doctor','Doctor report'),('history-prescription','Prescriptions'),('history-scan','Scans'),('history-vaccination','Vaccination'),('history-other','Others')]
        for index, (filename, category) in enumerate(categories):
            filename += '.pdf'
            report = db().scalar(select(CareReport).where(CareReport.profile_id == profile_id, CareReport.name == filename, CareReport.deleted_at.is_(None)))
            if not report:
                source = Path(__file__).resolve().parents[2]/'app/public/demo/women'/filename
                with app.test_request_context(method='POST', data={'file': (io.BytesIO(source.read_bytes()), filename), 'title': 'DEMO - Historical '+category, 'category': category, 'source_language': 'en', 'auto_read': 'false'}):
                    g.user = db().get(User, actor_id)
                    response, status = reports(profile_id)
                    if status != 201:
                        raise RuntimeError('Sample report upload failed')
                    report_id = response.get_json()['report']['id']
                report = db().get(CareReport, report_id)
                report.created_at = datetime.combine(anchor-timedelta(days=150-index*20), datetime.min.time())
                db().commit()
            report_id = report.id
            # Read the lab example through real private storage and OCR; scans stay unprocessed.
            if category == 'Lab tests':
                job = db().get(ReportText, report_id)
                if not job or job.status not in ('COMPLETED', 'PROCESSING'):
                    from services.report_text import Options, run_processor
                    options = Options(source_language='en', auto_import=False).model_dump(mode='json')
                    if not job:
                        job = ReportText(report_id=report_id, requested_by=actor_id, options=options)
                        db().add(job)
                    lease = uid()
                    job.status, job.lease_id, job.started_at, job.error_code = 'PROCESSING', lease, now(), None
                    audit('report_text_requested', actor_id, actor_id)
                    db().commit()
                    try:
                        result = run_processor(db().get(CareReport, report_id), options)
                        db().expire_all()
                        job = db().get(ReportText, report_id)
                        if job.lease_id == lease:
                            job.result, job.status = result, 'COMPLETED'
                            db().commit()
                    except Exception:
                        db().rollback()
                        job = db().get(ReportText, report_id)
                        if job.lease_id == lease:
                            job.status, job.error_code = 'FAILED', 'processing_failed'
                            db().commit()
                        raise RuntimeError('Historical lab report saved; OCR must be retried') from None
            print({'report': filename, 'category': category, 'saved': True}, flush=True)
        print({'complete': True, 'profile': name, 'profile_id': profile_id}, flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--profile-id', required=True)
    seed(parser.parse_args().profile_id)
