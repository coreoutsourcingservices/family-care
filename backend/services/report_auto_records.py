"""Save source-linked OCR observations, explicitly unreviewed and never a diagnosis."""
import re
from datetime import date
from sqlalchemy import select
from core.database import db
from core.models import CareProfile, ChildRecord, ChildRecordRevision


def save_extracted_records(report, result, actor_id):
    profile=db().get(CareProfile,report.profile_id)
    if not profile or profile.deleted_at or profile.module!='child':return []
    text=(result.get('original_text') or '').strip()
    if not text:return []
    lines=[line.strip() for line in text.splitlines() if line.strip()]
    dated=next((line for line in lines if re.match(r'^(?:report date|date|dated|collection date)\s*[:=-]',line,re.I)),'')
    match=re.search(r'\b(20\d{2})-(\d{2})-(\d{2})\b',dated)
    record_date=report.created_at.date()
    date_source='upload_date'
    if match:
        try:
            parsed=date.fromisoformat(match.group(0))
            if profile.dob<=parsed<=date.today():record_date=parsed;date_source='report_text'
        except ValueError:pass
    if record_date<profile.dob:return []
    common=dict(date=record_date.isoformat(),source_report_id=report.id,source_role='REPORT',reviewed=False,
                extraction_status='REVIEW_PENDING',date_source=date_source,provider='Uploaded report')
    drafts=[('history','history',dict(title=('Report: '+report.name)[:160],category='Medical report',notes=text[:2000]))]
    rx=next((i for i,line in enumerate(lines) if re.search(r'prescription|^rx\b|medications?|medicines?|\u0926\u0935\u093e',line,re.I)),None)
    medicines=[line for line in lines if re.search(r'\b(?:tab(?:let)?|cap(?:sule)?|syrup|ointment|drops?)\b',line,re.I)]
    prescription='\n'.join(lines[rx:] if rx is not None else medicines)
    if prescription:drafts.append(('history','prescription',dict(title=('Prescription: '+report.name)[:160],category='Medicine',notes=prescription[:2000])))
    weight=re.search(r'(?:weight|wt\.?|\u0935\u091c\u0928)\s*[:=-]?\s*(\d{1,3}(?:\.\d{1,2})?)\s*kg\b',text,re.I)
    height=re.search(r'(?:height|ht\.?|length)\s*[:=-]?\s*(\d{1,3}(?:\.\d{1,2})?)\s*cm\b',text,re.I)
    if weight and height and 0<float(weight[1])<=300 and 0<float(height[1])<=250:
        drafts.append(('growth','growth',dict(title=('Measurements: '+report.name)[:160],weight=weight[1],height=height[1],notes='Unreviewed measurements extracted from the uploaded report.')))
    nutrition='\n'.join(line for line in lines if re.search(r'nutrition|diet|feeding|meal|\u092a\u094b\u0937\u0923|\u0906\u0939\u093e\u0930',line,re.I))
    if nutrition:drafts.append(('nutrition','nutrition',dict(title=('Nutrition: '+report.name)[:160],notes=nutrition[:2000])))
    vaccine=next((line for line in lines if re.search(r'vaccine|vaccination|immuni[sz]ation|\u091f\u0940\u0915\u093e',line,re.I)),None)
    if vaccine and not re.search(r'\b(?:no|not|never|declined)\b',vaccine,re.I):drafts.append(('vaccination','vaccination',dict(title=vaccine[:160],status='Review pending',notes='Report mentions vaccination; administration is not confirmed. Review the original.\n'+vaccine)))
    saved=[]
    existing=db().scalars(select(ChildRecord).where(ChildRecord.profile_id==profile.id,ChildRecord.data['source_report_id'].as_string()==report.id)).all()
    for kind,section,fields in drafts:
        found=next((row for row in existing if row.kind==kind and row.data.get('source_report_section',row.kind)==section),None)
        if found:
            if not found.deleted_at:saved.append(dict(id=found.id,kind=kind,section=section))
            continue
        data=dict(common,**fields,source_report_section=section)
        row=ChildRecord(profile_id=profile.id,kind=kind,data=data)
        db().add(row);db().flush()
        db().add(ChildRecordRevision(record_id=row.id,actor_id=actor_id,action='created',data=data))
        saved.append(dict(id=row.id,kind=kind,section=section))
    return saved
