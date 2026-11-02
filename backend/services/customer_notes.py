from flask import g, jsonify, request
from sqlalchemy import select
from pydantic import Field, field_validator
from core.schemas import Schema, parse
from core.database import db
from core.models import CustomerNote, uid
from core.errors import APIError
from services.care import member_profile
from services.repository import audit
from services.approvals import paginate


class NoteInput(Schema):
    title: str = Field(min_length=1, max_length=160)
    body: str = Field(min_length=1, max_length=5000)

    @field_validator('title', 'body')
    @classmethod
    def nonblank(cls, value):
        if not value.strip():raise ValueError('Must not be blank')
        return value.strip()


def main_customer():
    if member_profile(g.user):raise APIError(403,'main_customer_only','Personal notes are only available to the main customer account')


def data(row):
    return dict(id=row.id,title=row.title,body=row.body,created_at=row.created_at.isoformat()+'Z',updated_at=row.updated_at.isoformat()+'Z')


def list_notes():
    main_customer()
    try:page=int(request.args.get('page',1));per_page=int(request.args.get('per_page',25))
    except (ValueError,TypeError):raise APIError(422,'invalid_pagination','Use integer page and per_page')
    if page<1 or not 1<=per_page<=100:raise APIError(422,'invalid_pagination','Invalid pagination')
    rows,total=paginate(select(CustomerNote).where(CustomerNote.owner_id==g.user.id).order_by(CustomerNote.updated_at.desc(),CustomerNote.id),page,per_page)
    return jsonify(items=[data(row) for row in rows],total=total,page=page,per_page=per_page)


def create_note():
    main_customer();value=parse(NoteInput)
    row=CustomerNote(id=uid(),owner_id=g.user.id,title=value.title,body=value.body)
    db().add(row);audit('customer_note_created',g.user.id,g.user.id);db().commit()
    return jsonify(note=data(row)),201


def owned(note_id):
    main_customer()
    row=db().scalar(select(CustomerNote).where(CustomerNote.id==str(note_id),CustomerNote.owner_id==g.user.id))
    if not row:raise APIError(404,'note_not_found','Note not found')
    return row


def update_note(note_id):
    row=owned(note_id);value=parse(NoteInput);row.title=value.title;row.body=value.body
    audit('customer_note_updated',g.user.id,g.user.id);db().commit()
    return jsonify(note=data(row))


def delete_note(note_id):
    row=owned(note_id);db().delete(row);audit('customer_note_deleted',g.user.id,g.user.id);db().commit()
    return jsonify(message='Note deleted')
