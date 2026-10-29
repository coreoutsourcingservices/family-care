"""Parent-owned child diary APIs. Clinical schedules are unavailable until reviewed data exists."""
from datetime import date, datetime
from uuid import UUID
from calendar import monthrange
from flask import Blueprint, g, jsonify, request
from sqlalchemy import select, func
from pydantic import Field, field_validator, model_validator
from core.schemas import Schema, parse
from core.routing import route
from core.database import db
from core.errors import APIError
from core.models import ChildRecord, ChildRecordRevision, ChildPreferences, CareProfile, now
from core.http import pagination
from services.care import accessible_profile, profile_data
from services.repository import audit
from services.approvals import paginate

bp = Blueprint('children', __name__, url_prefix='/api/v1')
KINDS = {'vaccinations/history':'vaccination', 'medical-history':'history', 'growth':'growth',
         'nutrition':'nutrition', 'consultations':'consultation', 'care-notes':'care',
         'consultation-requests':'consultation_request'}


def today():
    # Indian product calendar; timestamps remain UTC.
    from zoneinfo import ZoneInfo
    return datetime.now(ZoneInfo('Asia/Kolkata')).date()


class RecordInput(Schema):
    source_id: str | None = Field(default=None, pattern=r'^[a-fA-F0-9-]{36}$')
    title: str = Field(min_length=1, max_length=160)
    date: date
    status: str = Field(default='', max_length=32)
    nextDate: str = Field(default='', max_length=10)
    provider: str = Field(default='', max_length=160)
    notes: str = Field(default='', max_length=2000)
    category: str = Field(default='', max_length=160)
    weight: str = Field(default='', max_length=12)
    height: str = Field(default='', max_length=12)
    # Optional nutrition form fields, retained without clinical interpretation.
    meal: str = Field(default='', max_length=160)
    vaccine_id: UUID | None = None
    schedule_id: UUID | None = None
    dose_code: str = Field(default='',max_length=40)
    schedule_type: str = Field(default='',max_length=8)
    vaccinator: str = Field(default='',max_length=160)
    batch_number: str = Field(default='',max_length=100)
    certificate_id: UUID | None = None

    @field_validator('title')
    @classmethod
    def title_required(cls, value):
        if not value.strip():
            raise ValueError('Title required')
        return value.strip()

    @model_validator(mode='after')
    def dates_and_measurements(self):
        if self.nextDate:
            next_date = date.fromisoformat(self.nextDate)
            if next_date < self.date:
                raise ValueError('Next date must be on or after record date')
        for key, maximum in (('weight', 300), ('height', 250)):
            value = getattr(self, key)
            if value and not (0 < float(value) <= maximum):
                raise ValueError('Invalid measurement')
        return self


class PreferencesInput(Schema):
    in_app: bool


def child(child_id, lock=False):
    profile = accessible_profile(g.user, str(child_id), lock=lock)
    if profile.module != 'child':
        raise APIError(404, 'child_not_found', 'Child profile not found')
    return profile


def record_data(record):
    data = dict(record.data, id=record.id, kind=record.kind, verification_status='PARENT_REPORTED')
    if record.kind == 'vaccination':
        from services.vaccination import display_age_group
        profile = db().get(CareProfile, record.profile_id)
        data['age_group'] = display_age_group(profile.dob, date.fromisoformat(record.data['date']))
    return data


def child_age(profile):
    end = today()
    months = (end.year-profile.dob.year)*12 + end.month-profile.dob.month
    anchor_year, anchor_month = divmod(profile.dob.month-1+months, 12)
    anchor = date(profile.dob.year+anchor_year, anchor_month+1,
                  min(profile.dob.day, monthrange(profile.dob.year+anchor_year, anchor_month+1)[1]))
    if anchor > end:
        months -= 1
        anchor_year, anchor_month = divmod(profile.dob.month-1+months, 12)
        anchor = date(profile.dob.year+anchor_year, anchor_month+1,
                      min(profile.dob.day, monthrange(profile.dob.year+anchor_year, anchor_month+1)[1]))
    years, remaining = divmod(months, 12)
    category = 'NEWBORN' if (end-profile.dob).days < 28 else 'INFANT' if months < 12 else 'TODDLER' if months < 36 else 'PRESCHOOLER' if months < 72 else 'SCHOOL_AGE' if years < 13 else 'ADOLESCENT'
    return dict(completed_years=years, remaining_months=remaining, remaining_days=(end-anchor).days,
                total_completed_months=months, total_days=(end-profile.dob).days,
                display=f'{years} years {remaining} months {(end-anchor).days} days',
                primary_category=category, secondary_categories=[], in_child_module_scope=years < 13)


def schedule_type():
    value = request.args.get('schedule_type', 'UIP')
    if value not in ('UIP', 'IAP'):
        raise APIError(422, 'invalid_schedule', 'Choose UIP or IAP')
    return value


def clinical_state():
    return dict(schedule_type=schedule_type(), schedule_version_id=None,
                status='NOT_AVAILABLE', history_status='PARENT_REPORTED',
                completed_count=None, upcoming_count=None, potentially_overdue_count=None,
                message='No medically reviewed schedule is published. Recorded dates are parent-provided; confirm them with your doctor.')


def children():
    page, per_page = pagination()
    rows, total = paginate(select(CareProfile).where(CareProfile.owner_id == g.user.id,
                            CareProfile.module == 'child').order_by(CareProfile.created_at, CareProfile.id), page, per_page)
    return jsonify(items=[dict(profile_data(row), age=child_age(row)) for row in rows], total=total, page=page, per_page=per_page)


def detail(child_id):
    profile = child(child_id)
    return jsonify(child=dict(profile_data(profile), age=child_age(profile)))


def age(child_id):
    return jsonify(age=child_age(child(child_id)), as_of_date=today().isoformat())


def query_records(profile_id, kind=None):
    query = select(ChildRecord).where(ChildRecord.profile_id == profile_id, ChildRecord.deleted_at.is_(None))
    return query.where(ChildRecord.kind == kind) if kind else query


def validate_record(payload, kind, profile):
    if payload.date < profile.dob:
        raise APIError(422, 'invalid_date', 'Record date cannot be before birth')
    if kind in ('growth', 'history', 'nutrition') and payload.date > today():
        raise APIError(422, 'invalid_date', 'This record cannot be dated in the future')
    if kind == 'growth' and not (payload.weight or payload.height):
        raise APIError(422, 'missing_measurements', 'Enter weight in kg or height in cm')
    if kind == 'vaccination' and payload.status not in ('Completed', 'Planned','Missed'):
        raise APIError(422, 'invalid_status', 'Choose Completed, Planned or Missed')
    if kind == 'vaccination' and payload.status == 'Completed' and payload.date > today():
        raise APIError(422, 'invalid_date', 'Completed vaccination cannot be in the future')
    if kind == 'consultation_request' and not profile.referred_doctor_id:
        raise APIError(409, 'doctor_required', 'Connect a doctor to this child before requesting a consultation')
    data = payload.model_dump(mode='json')
    if kind=='vaccination':
        from services.vaccination import validate_record as validate_vaccination
        validate_vaccination(data,profile)
    if kind == 'consultation_request':
        data['status'] = 'REQUESTED'
        data['doctor_id'] = profile.referred_doctor_id
    return data


def records(child_id, resource):
    profile = child(child_id, lock=request.method != 'GET')
    kind = KINDS[resource]
    if request.method == 'GET':
        page, per_page = pagination()
        rows, total = paginate(query_records(profile.id, kind).order_by(ChildRecord.created_at.desc(), ChildRecord.id), page, per_page)
        return jsonify(items=[record_data(row) for row in rows], total=total, page=page, per_page=per_page)
    data = validate_record(parse(RecordInput), kind, profile)
    if data.get('source_id'):
        existing = db().scalar(select(ChildRecord).where(ChildRecord.profile_id == profile.id, ChildRecord.data['source_id'].as_string() == data['source_id']))
        if existing:
            if existing.deleted_at or existing.kind != kind:
                raise APIError(409, 'duplicate_record', 'This record was already imported or removed')
            return jsonify(record=record_data(existing))
    row = ChildRecord(profile_id=profile.id, kind=kind, data=data)
    db().add(row)
    db().flush()
    db().add(ChildRecordRevision(record_id=row.id, actor_id=g.user.id, action='created', data=data))
    audit('child_record_created', profile.owner_id, g.user.id)
    db().commit()
    return jsonify(record=record_data(row)), 201


def all_records(child_id):
    profile = child(child_id)
    page, per_page = pagination()
    rows, total = paginate(query_records(profile.id).order_by(ChildRecord.created_at.desc(), ChildRecord.id), page, per_page)
    return jsonify(items=[record_data(row) for row in rows], total=total, page=page, per_page=per_page)


def remove_record(child_id, resource, record_id):
    profile = child(child_id, lock=True)
    row = db().scalar(query_records(profile.id, KINDS[resource]).where(ChildRecord.id == str(record_id)).with_for_update())
    if not row:
        raise APIError(404, 'record_not_found', 'Child record not found')
    db().add(ChildRecordRevision(record_id=row.id, actor_id=g.user.id, action='removed', data=row.data))
    row.deleted_at = now()
    audit('child_record_removed', profile.owner_id, g.user.id)
    db().commit()
    return jsonify(message='Record removed')


def edit_record(child_id, resource, record_id):
    profile = child(child_id, lock=True)
    row = db().scalar(query_records(profile.id, KINDS[resource]).where(ChildRecord.id == str(record_id)).with_for_update())
    if not row:
        raise APIError(404, 'record_not_found', 'Child record not found')
    patch = request.get_json()
    if not isinstance(patch, dict) or not patch:
        raise APIError(400, 'invalid_json', 'A non-empty JSON object is required')
    existing = {key:value for key,value in row.data.items() if key in RecordInput.model_fields}
    data = validate_record(RecordInput.model_validate(dict(existing, **patch)), row.kind, profile)
    db().add(ChildRecordRevision(record_id=row.id, actor_id=g.user.id, action='updated', data=row.data))
    row.data = data
    audit('child_record_updated', profile.owner_id, g.user.id)
    db().commit()
    return jsonify(record=record_data(row))


def reminders(child_id):
    profile = child(child_id)
    prefs = db().get(ChildPreferences, profile.id)
    enabled = prefs.in_app if prefs else True
    items = []
    if enabled:
        for row in db().scalars(query_records(profile.id)):
            data = row.data
            due = data.get('nextDate') or (data.get('date') if data.get('status') in ('Planned', 'REQUESTED') else None)
            if due and row.kind in ('vaccination', 'consultation', 'consultation_request'):
                items.append(dict(id=row.id, kind=row.kind, title=data['title'], date=due,
                                  status='OVERDUE' if due < today().isoformat() else 'UPCOMING',
                                  delivery_status='IN_APP_ONLY', source='PARENT_REPORTED'))
    from services.vaccination import scheduled_reminders
    items.extend(scheduled_reminders(profile))
    return jsonify(items=sorted(items, key=lambda item: item['date']), total=len(items), preferences={'in_app':enabled},
                   message='Recorded-date and published-schedule reminders. Schedule emails require explicit parent opt-in; SMS is not enabled.')


def preferences(child_id):
    profile = child(child_id, lock=True)
    value = parse(PreferencesInput)
    prefs = db().get(ChildPreferences, profile.id)
    if not prefs:
        prefs = ChildPreferences(profile_id=profile.id)
        db().add(prefs)
    prefs.in_app = value.in_app
    db().commit()
    return jsonify(in_app=prefs.in_app)


def dashboard(child_id):
    profile = child(child_id)
    rows = db().scalars(query_records(profile.id).order_by(ChildRecord.created_at.desc(), ChildRecord.id).limit(10)).all()
    counts = dict(db().execute(select(ChildRecord.kind, func.count()).where(
        ChildRecord.profile_id == profile.id, ChildRecord.deleted_at.is_(None)).group_by(ChildRecord.kind)).all())
    from services.vaccination import timeline
    state=timeline(profile,schedule_type())
    return jsonify(child=dict(profile_data(profile), age=child_age(profile)), as_of_date=today().isoformat(),
                   counts=counts, recent=[record_data(row) for row in rows], vaccination=state)


def health_guide(child_id):
    child(child_id)
    return jsonify(status='NOT_AVAILABLE', items=[], message='No medically reviewed health guide has been published for this child. Ask your doctor for guidance.')


def vaccinations(child_id):
    from services.vaccination import child_vaccination_list
    return jsonify(**child_vaccination_list(child(child_id),schedule_type(),request.args.get('schedule_version_id'),request.args.get('view','all')))


def upcoming(child_id):
    from services.vaccination import timeline
    profile = child(child_id)
    state=timeline(profile,schedule_type(),request.args.get('schedule_version_id'))
    if state['total']:
        items=[item for item in state['items'] if item['status'] in ('UPCOMING','DUE','REVIEW_REQUIRED')]
        return jsonify(**dict(state,items=items,total=len(items)))
    items = [record_data(row) for row in db().scalars(query_records(profile.id, 'vaccination'))
             if (row.data.get('nextDate') or row.data.get('date','')) >= today().isoformat()
             and (row.data.get('status') == 'Planned' or row.data.get('nextDate'))]
    return jsonify(items=items, total=len(items), **clinical_state())


def catalog():
    from services.vaccination import public_catalog
    return public_catalog()


def doctor_requests():
    page, per_page = pagination()
    query = select(ChildRecord).join(CareProfile, ChildRecord.profile_id == CareProfile.id).where(
        CareProfile.referred_doctor_id == g.user.id, ChildRecord.kind == 'consultation_request',
        ChildRecord.deleted_at.is_(None))
    rows, total = paginate(query.order_by(ChildRecord.created_at.desc(), ChildRecord.id), page, per_page)
    return jsonify(items=[dict(record_data(row), child_id=row.profile_id) for row in rows],
                   total=total, page=page, per_page=per_page)


route(bp, '/children', children, roles=('PATIENT',))
route(bp, '/children/<uuid:child_id>', detail, roles=('PATIENT',))
route(bp, '/children/<uuid:child_id>/age', age, roles=('PATIENT',))
route(bp, '/children/<uuid:child_id>/records', all_records, roles=('PATIENT',))
route(bp, '/children/<uuid:child_id>/dashboard', dashboard, roles=('PATIENT',))
route(bp, '/children/<uuid:child_id>/health-guide', health_guide, roles=('PATIENT',))
route(bp, '/children/<uuid:child_id>/vaccinations', vaccinations, roles=('PATIENT',))
route(bp, '/children/<uuid:child_id>/vaccinations/upcoming', upcoming, roles=('PATIENT',))
route(bp, '/children/<uuid:child_id>/reminders', reminders, roles=('PATIENT',))
route(bp, '/children/<uuid:child_id>/reminder-preferences', preferences, 'PUT', roles=('PATIENT',))
route(bp, '/vaccines', catalog)
route(bp, '/doctors/consultation-requests', doctor_requests, roles=('DOCTOR',))
def schedule_catalog():
    from services.vaccination import public_schedules
    return public_schedules()


route(bp, '/vaccination-schedules', schedule_catalog)

# Distinct endpoint names prevent Flask collisions between resource handlers.
for resource in KINDS:
    def make_handler(resource):
        def handler(child_id):
            return records(child_id, resource)
        handler.__name__ = 'records_' + resource.replace('/', '_').replace('-', '_')
        return handler

    def make_remove(resource):
        def handler(child_id, record_id):
            return remove_record(child_id, resource, record_id)
        handler.__name__ = 'remove_' + resource.replace('/', '_').replace('-', '_')
        return handler

    handler = make_handler(resource)
    # Flask requires different names for the GET and POST views registered by route().
    route(bp, '/children/<uuid:child_id>/' + resource, handler,
          roles=('PATIENT','DOCTOR') if resource == 'consultation-requests' else ('PATIENT',))
    write_handler = make_handler(resource)
    write_handler.__name__ += '_create'
    route(bp, '/children/<uuid:child_id>/' + resource, write_handler, 'POST', roles=('PATIENT',))
    route(bp, '/children/<uuid:child_id>/' + resource + '/<uuid:record_id>', make_remove(resource), 'DELETE', roles=('PATIENT',))

    def make_edit(resource):
        def handler(child_id, record_id):
            return edit_record(child_id, resource, record_id)
        handler.__name__ = 'edit_' + resource.replace('/', '_').replace('-', '_')
        return handler

    route(bp, '/children/<uuid:child_id>/' + resource + '/<uuid:record_id>', make_edit(resource), 'PATCH', roles=('PATIENT',))
