"""Owner-confirmed imports from saved OCR; never auto-verifies a medical fact."""
from typing import Literal
from uuid import UUID, uuid5, NAMESPACE_URL
from flask import g, jsonify, request
from pydantic import Field
from sqlalchemy import select
from core.schemas import Schema, parse
from core.database import db
from core.errors import APIError
from core.models import ReportText, ChildRecord, uid, now
from core.http import pagination
from services.care import accessible_report, accessible_profile
from services.repository import audit
from services.approvals import paginate
from patient.child_routes import RecordInput, validate_record, record_data

class ImportInput(Schema):
    kind: Literal['growth','history','vaccination','nutrition']
    reviewed: Literal[True]
    record: RecordInput

def import_report(profile_id,report_id):
    profile=accessible_profile(g.user,str(profile_id),lock=True)
    report=accessible_report(g.user,str(profile_id),str(report_id))
    extraction=db().get(ReportText,report.id)
    if not extraction or extraction.status not in ('COMPLETED','PARTIAL') or not (extraction.result or {}).get('original_text'):
        raise APIError(409,'extraction_required','Extract readable report text before importing a record')
    value=parse(ImportInput)
    source_id=str(uuid5(NAMESPACE_URL,report.id+':'+value.kind))
    existing=db().scalar(select(ChildRecord).where(ChildRecord.profile_id==profile.id,ChildRecord.deleted_at.is_(None),ChildRecord.data['source_id'].as_string()==source_id))
    if existing:return jsonify(record=record_data(existing),already_imported=True)
    payload=value.record.model_copy(update={'source_id':source_id,'certificate_id':UUID(report.id) if value.kind=='vaccination' else None})
    data=validate_record(payload,value.kind,profile)
    data['source_report_id']=report.id
    data['source']='OWNER_REVIEWED_OCR'
    entry=ChildRecord(id=uid(),profile_id=profile.id,kind=value.kind,data=data)
    db().add(entry)
    audit('report_record_imported',g.user.id,g.user.id)
    db().commit()
    return jsonify(record=record_data(entry),already_imported=False),201

def imported_records(profile_id):
    profile=accessible_profile(g.user,str(profile_id))
    page,per_page=pagination()
    query=select(ChildRecord).where(ChildRecord.profile_id==profile.id,ChildRecord.deleted_at.is_(None),ChildRecord.data['source'].as_string()=='OWNER_REVIEWED_OCR').order_by(ChildRecord.created_at.desc(),ChildRecord.id)
    rows,total=paginate(query,page,per_page)
    return jsonify(items=[record_data(row) for row in rows],total=total,page=page,per_page=per_page)
