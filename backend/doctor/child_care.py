"""Connected doctors can document only the child-care areas consented in the product."""
from flask import Blueprint, g, request, jsonify
from core.database import db
from core.models import ChildRecord, ChildRecordRevision
from core.errors import APIError
from core.routing import route
from core.schemas import parse
from patient.child_routes import child, query_records, record_data, RecordInput, validate_record

bp=Blueprint('doctor_child_care',__name__,url_prefix='/api/v1/doctors/care-profiles')
AREAS={'vaccination':'vaccination','growth':'growth','nutrition':'nutrition','care':'care','prescription':'care'}

def entries(profile_id,area):
    if area not in AREAS:raise APIError(404,'area_not_found','This care area is not available to doctors')
    profile=child(profile_id,lock=request.method!='GET')
    kind=AREAS[area]
    if request.method=='GET':
        from core.http import pagination
        from services.approvals import paginate
        page,size=pagination()
        query=query_records(profile.id,kind)
        if area=='prescription':query=query.where(ChildRecord.data['category'].as_string()=='Prescription')
        rows,total=paginate(query.order_by(ChildRecord.created_at.desc(),ChildRecord.id),page,size)
        return jsonify(items=[record_data(row) for row in rows],total=total,page=page,per_page=size)
    value=validate_record(parse(RecordInput),kind,profile)
    if area=='prescription':
        if not value['notes'].strip():raise APIError(422,'instructions_required','Enter the prescription instructions')
        value['category']='Prescription'
    value.update(source_role='DOCTOR',author_id=g.user.id,author_name=g.user.full_name)
    row=ChildRecord(profile_id=profile.id,kind=kind,data=value)
    db().add(row);db().flush()
    db().add(ChildRecordRevision(record_id=row.id,actor_id=g.user.id,action='created',data=value))
    from services.notifications import enqueue
    enqueue(profile.owner_id,'child_record_added','Your child care record was updated','Your connected doctor added a care entry. Open Child Care to review it.',{'profile_id':profile.id,'area':area},event_key='child-record:'+row.id)
    db().commit()
    return jsonify(record=record_data(row)),201

def add(profile_id,area):return entries(profile_id,area)
route(bp,'/<uuid:profile_id>/child-records/<area>',entries,roles=('DOCTOR',))
route(bp,'/<uuid:profile_id>/child-records/<area>',add,'POST',roles=('DOCTOR',),schema=RecordInput)
