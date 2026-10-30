"""Explicitly reviewed OCR imports; no extraction is silently treated as clinical truth."""
from typing import Literal
from flask import g, jsonify
from pydantic import Field
from sqlalchemy import select
from core.database import db
from core.models import ChildRecord, ChildRecordRevision, ReportText, CareReport
from core.schemas import Schema, parse
from core.errors import APIError
from core.http import pagination
from services.care import accessible_profile, accessible_report
from services.approvals import paginate
from patient.child_routes import RecordInput, validate_record, record_data

class ImportInput(Schema):
    kind: Literal['history','growth','vaccination','nutrition']
    reviewed: Literal[True]
    record: RecordInput

def imported(profile_id):
    profile=accessible_profile(g.user,str(profile_id))
    query=select(ChildRecord).where(ChildRecord.profile_id==profile.id,ChildRecord.deleted_at.is_(None),ChildRecord.data['source_report_id'].as_string().is_not(None))
    page,size=pagination()
    rows,total=paginate(query.order_by(ChildRecord.created_at.desc(),ChildRecord.id),page,size)
    return jsonify(items=[record_data(row) for row in rows],total=total,page=page,per_page=size)

def import_record(profile_id,report_id):
    profile=accessible_profile(g.user,str(profile_id),lock=True)
    report=accessible_report(g.user,profile.id,str(report_id))
    # This lock makes repeated submissions idempotent, including concurrent imports.
    db().scalar(select(CareReport).where(CareReport.id==report.id).with_for_update())
    payload=parse(ImportInput)
    result=db().get(ReportText,report.id)
    if not result or result.status not in ('COMPLETED','PARTIAL') or not (result.result or {}).get('original_text'):
        raise APIError(409,'extraction_required','Extract and review this report before importing a record')
    existing=db().scalar(select(ChildRecord).where(ChildRecord.profile_id==profile.id,ChildRecord.kind==payload.kind,ChildRecord.data['source_report_id'].as_string()==report.id))
    if existing:
        if existing.deleted_at:raise APIError(409,'record_removed','This report record was already removed; add a new manual correction if needed')
        return jsonify(record=record_data(existing),already_imported=True)
    data=validate_record(payload.record,payload.kind,profile)
    data.update(source_report_id=report.id,source_role='PATIENT',reviewed=True)
    row=ChildRecord(profile_id=profile.id,kind=payload.kind,data=data)
    report.category={'growth':'Lab tests','vaccination':'Vaccination','nutrition':'Others','history':report.category}.get(payload.kind,'Others')
    report.category_reviewed=True
    db().add(row);db().flush()
    db().add(ChildRecordRevision(record_id=row.id,actor_id=g.user.id,action='created',data=data))
    db().commit()
    return jsonify(record=record_data(row),already_imported=False),201


class CategoryInput(Schema):
    category: Literal['Lab tests','Prescriptions','Scans','Vaccination','Others']

def set_category(profile_id,report_id):
    report=accessible_report(g.user,str(profile_id),str(report_id))
    value=parse(CategoryInput)
    report.category=value.category;report.category_reviewed=True
    db().commit()
    return jsonify(category=report.category,category_reviewed=True)

def infer_category(text):
    import re
    if re.search(r'vaccin|immuni[sz]|\u091f\u0940\u0915\u093e',text,re.I):return 'Vaccination'
    if re.search(r'prescription|(?:^|\n)\s*rx\b|\u0926\u0935\u093e\u0908',text,re.I):return 'Prescriptions'
    if re.search(r'x[ -]?ray|ultrasound|radiology|\bmri\b|ct scan',text,re.I):return 'Scans'
    if re.search(r'laboratory|lab(?:oratory)? report|blood test|haemoglobin|hemoglobin|\bcbc\b|\bweight\s*[:=]|\bheight\s*[:=]',text,re.I):return 'Lab tests'
    return 'Others'
