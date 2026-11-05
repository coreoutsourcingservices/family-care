"""Save valid labelled demo history to one explicitly selected Adult profile."""
import argparse
import io
from collections import Counter
from datetime import datetime,timedelta
from zoneinfo import ZoneInfo
from pathlib import Path
from uuid import uuid5,NAMESPACE_URL
from flask import g
from sqlalchemy import select
from app import create_app
from core.database import db
from core.models import CareProfile,User,AdultRecord,AdultRecordRevision,ProfilePlanner,CareReport,ReportText,uid,now
from patient.adult_routes import AdultInput
from services.women_workspace import primary_id
from services.repository import audit
from scripts.adult_demo_history import entries


def seed(profile_id):
    app=create_app();anchor=datetime.now(ZoneInfo('Asia/Kolkata')).date()
    with app.app_context():
        profile=db().get(CareProfile,profile_id)
        if not profile or profile.module!='adult' or profile.deleted_at:raise RuntimeError('Select an active Adult profile')
        actor=db().get(User,primary_id(profile))
        if not actor or actor.role!='PATIENT' or actor.account_status!='ACTIVE':raise RuntimeError('Primary account unavailable')
        actor_id=actor.id;name=profile.name
        existing={row.id for row in db().scalars(select(AdultRecord).where(AdultRecord.profile_id==profile_id))}
        counts=Counter();skipped=0
        for key,payload in entries(anchor):
            identifier=str(uuid5(NAMESPACE_URL,f'familycare:adult-history-v1:{profile_id}:{key}'))
            if identifier in existing:skipped+=1;continue
            value=AdultInput(**payload)
            if value.date<profile.dob:skipped+=1;continue
            data=value.model_dump(mode='json',exclude={'version'})
            db().add(AdultRecord(id=identifier,profile_id=profile_id,kind=value.kind,data=data))
            db().flush()
            db().add(AdultRecordRevision(record_id=identifier,actor_id=actor_id,action='created',data=data))
            audit('adult_demo_record_created',actor_id,actor_id);counts[value.kind]+=1
        db().commit();print({'profile':name,'history_added':dict(counts),'skipped':skipped},flush=True)
        existing_titles={r.title for r in db().scalars(select(ProfilePlanner).where(ProfilePlanner.profile_id==profile_id,ProfilePlanner.user_id==actor_id))}
        planner=0
        for i in range(6):
            for kind in ('note','task'):
                title=f'DEMO - Adult historical {kind} {i+1}'
                if title in existing_titles:continue
                created=datetime.combine(anchor-timedelta(days=120-i*18),datetime.min.time())
                due=datetime.combine(anchor+timedelta(days=i+2),datetime.min.time()) if i>=4 else created+timedelta(days=2)
                db().add(ProfilePlanner(profile_id=profile_id,user_id=actor_id,kind=kind,title=title,body='DEMO / SAMPLE ONLY. Fictional '+('previous journal and review questions.' if kind=='note' else 'private task: organize example records.'),due_at=due if kind=='task' else None,completed_at=due if kind=='task' and i<4 else None,version=1,created_at=created,updated_at=created))
                audit('planner_created',actor_id,actor_id);planner+=1
        db().commit();print({'planner_added':planner},flush=True)
        for index,(key,category) in enumerate([('lab','Lab tests'),('doctor','Doctor report'),('prescription','Prescriptions'),('scan','Scans'),('vaccination','Vaccination'),('other','Others')]):
            filename=f'adult-history-{key}.pdf'
            report=db().scalar(select(CareReport).where(CareReport.profile_id==profile_id,CareReport.name==filename,CareReport.deleted_at.is_(None)))
            if not report:
                source=Path(__file__).resolve().parents[2]/'app/public/demo/adult'/filename
                with app.test_request_context(method='POST',data={'file':(io.BytesIO(source.read_bytes()),filename),'title':'DEMO - Adult historical '+category,'category':category,'source_language':'en','auto_read':'false'}):
                    from services.adult_workspace import report_list
                    g.user=db().get(User,actor_id);response,status=report_list(profile_id)
                    if status!=201:raise RuntimeError('Sample upload failed')
                    report_id=response.get_json()['report']['id']
                report=db().get(CareReport,report_id);report.created_at=datetime.combine(anchor-timedelta(days=150-index*20),datetime.min.time());db().commit()
            report_id=report.id
            if category=='Lab tests':
                job=db().get(ReportText,report_id)
                if not job or job.status not in ('COMPLETED','PROCESSING'):
                    from services.report_text import Options,run_processor
                    options=Options(source_language='en',auto_import=False).model_dump(mode='json')
                    if not job:job=ReportText(report_id=report_id,requested_by=actor_id,options=options);db().add(job)
                    lease=uid();job.status,job.lease_id,job.started_at,job.error_code='PROCESSING',lease,now(),None
                    audit('report_text_requested',actor_id,actor_id);db().commit()
                    try:
                        result=run_processor(db().get(CareReport,report_id),options)
                        db().expire_all();job=db().get(ReportText,report_id)
                        if job.lease_id==lease:job.result,job.status=result,'COMPLETED';db().commit()
                    except Exception:
                        db().rollback();job=db().get(ReportText,report_id)
                        if job.lease_id==lease:job.status,job.error_code='FAILED','processing_failed';db().commit()
                        raise RuntimeError('Report saved; OCR must be retried') from None
            print({'report':filename,'category':category,'saved':True},flush=True)
        print({'complete':True,'profile':name,'profile_id':profile_id},flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--profile-id',required=True);seed(parser.parse_args().profile_id)
