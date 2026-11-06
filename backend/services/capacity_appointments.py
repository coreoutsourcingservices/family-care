"""Connected-doctor bookings. All appointment windows use Asia/Kolkata."""
import json
from datetime import date, datetime, timedelta, timezone
from uuid import UUID
from typing import Literal
from flask import Blueprint, g, jsonify, request
from pydantic import Field, StrictInt, field_validator, model_validator
from sqlalchemy import select, func, or_
from core.database import db
from core.errors import APIError
from core.models import DoctorAppointmentSchedule, CapacityAppointment, CareProfile, FamilyInvitation, EmailNotification, User, now, uid
from core.routing import route
from core.schemas import Schema, parse
from services.appointment_slots import lock_doctor
from services.consultation_directory import approved, primary
from services.repository import audit

bp = Blueprint('capacity_appointments', __name__, url_prefix='/api/v1')
IST = timezone(timedelta(hours=5, minutes=30))


def today():
    return datetime.now(IST).date()


def instant(day, clock):
    return datetime.fromisoformat(day.isoformat()+'T'+clock).replace(tzinfo=IST).astimezone(timezone.utc).replace(tzinfo=None)


class WindowInput(Schema):
    id: UUID
    start: str = Field(pattern=r'^(?:[01][0-9]|2[0-3]):[0-5][0-9]$')
    end: str = Field(pattern=r'^(?:[01][0-9]|2[0-3]):[0-5][0-9]$')
    capacity: int = Field(ge=1, le=500, strict=True)
    days: list[StrictInt] = Field(min_length=1, max_length=7)

    @field_validator('days')
    @classmethod
    def valid_days(cls, values):
        if any(type(v) is not int or not 0 <= v <= 6 for v in values) or len(set(values)) != len(values):
            raise ValueError('Choose unique weekdays from Monday (0) to Sunday (6)')
        return sorted(values)

    @model_validator(mode='after')
    def valid_range(self):
        if self.start >= self.end:
            raise ValueError('End time must be later than start time on the same day')
        return self


class ScheduleInput(Schema):
    version: int = Field(ge=0, strict=True)
    windows: list[WindowInput] = Field(max_length=20)

    @model_validator(mode='after')
    def no_overlaps(self):
        if len({w.id for w in self.windows}) != len(self.windows):
            raise ValueError('Each window must have a unique ID')
        for i, first in enumerate(self.windows):
            for second in self.windows[i+1:]:
                if set(first.days) & set(second.days) and first.start < second.end and second.start < first.end:
                    raise ValueError('Appointment windows cannot overlap on the same weekday')
        return self


def schedule_data(row):
    return dict(windows=row.windows if row else [], version=row.version if row else 0, timezone='Asia/Kolkata')


def read_schedule():
    return jsonify(schedule_data(db().get(DoctorAppointmentSchedule, g.user.id)))


def save_schedule():
    value = parse(ScheduleInput)
    lock_doctor(g.user.id)
    row = db().get(DoctorAppointmentSchedule, g.user.id)
    if value.version != (row.version if row else 0):
        raise APIError(409, 'schedule_changed', 'Schedule changed. Reload before saving')
    windows = [w.model_dump(mode='json') for w in value.windows]
    by_id = {w['id']: w for w in windows}
    old = {w['id']: w for w in row.windows} if row else {}
    bookings = db().scalars(select(CapacityAppointment).where(CapacityAppointment.doctor_id == g.user.id,
        CapacityAppointment.appointment_date >= today(), CapacityAppointment.status.in_(['BOOKED', 'COMPLETED']))).all()
    counts = {}
    for booking in bookings:
        window = by_id.get(booking.window_id)
        if not window or window['start'] != booking.start_time or window['end'] != booking.end_time or booking.appointment_date.weekday() not in window['days']:
            raise APIError(409, 'window_has_bookings', 'A booked window cannot be removed or moved. Cancel its appointments first')
        key = (booking.window_id, booking.appointment_date)
        counts[key] = counts.get(key, 0)+1
        if counts[key] > window['capacity']:
            raise APIError(409, 'capacity_below_bookings', 'Capacity cannot be lower than existing bookings')
    # IDs stay attached to their time range so a changed window cannot reopen an occupied range.
    for window in windows:
        previous = old.get(window['id'])
        if previous and (previous['start'], previous['end']) != (window['start'], window['end']):
            if any(b.window_id == window['id'] for b in bookings):
                raise APIError(409, 'window_has_bookings', 'Booked window times cannot be changed')
    if not row:
        row = DoctorAppointmentSchedule(doctor_id=g.user.id, version=1)
        db().add(row)
    else:
        row.version += 1
    row.windows = windows
    audit('appointment_schedule_saved', actor_id=g.user.id)
    db().commit()
    return jsonify(schedule_data(row))


def chosen_date():
    try:
        day = date.fromisoformat(request.args.get('date', today().isoformat()))
    except ValueError:
        raise APIError(422, 'invalid_date', 'Choose a valid appointment date')
    validate_date(day)
    return day


def validate_date(day):
    if not today() <= day <= today()+timedelta(days=90):
        raise APIError(422, 'invalid_date', 'Choose a date within the next 90 days')


def connected(profile_id):
    profile = primary(profile_id)
    if not profile.referred_doctor_id:
        return profile, None
    return profile, approved(profile.referred_doctor_id)


def window_count(doctor_id, window_id, day):
    return db().scalar(select(func.count()).select_from(CapacityAppointment).where(
        CapacityAppointment.doctor_id == doctor_id, CapacityAppointment.window_id == window_id,
        CapacityAppointment.appointment_date == day, CapacityAppointment.status.in_(['BOOKED', 'COMPLETED'])))


def availability(profile_id):
    profile, doctor = connected(profile_id)
    day = chosen_date()
    result = dict(profile_id=profile.id, date=day.isoformat(), timezone='Asia/Kolkata', doctor=None, items=[])
    if not doctor:
        return jsonify(result)
    result['doctor'] = dict(id=doctor.id, name=doctor.full_name)
    schedule = db().get(DoctorAppointmentSchedule, doctor.id)
    for window in schedule.windows if schedule else []:
        if day.weekday() not in window['days']:
            continue
        booked = window_count(doctor.id, window['id'], day)
        remaining = max(0, window['capacity']-booked)
        closed = instant(day, window['start']) <= now()
        result['items'].append(dict(id=window['id'], start=window['start'], end=window['end'], capacity=window['capacity'],
            booked=booked, remaining=remaining, status='CLOSED' if closed else 'FULL' if not remaining else 'AVAILABLE'))
    result['items'].sort(key=lambda w: w['start'])
    return jsonify(result)


class BookingInput(Schema):
    window_id: UUID
    appointment_date: date
    request_id: UUID


def booking_data(row):
    doctor = db().get(User, row.doctor_id)
    profile = db().get(CareProfile, row.profile_id)
    email = db().get(EmailNotification, row.email_id) if row.email_id else None
    return dict(id=row.id, profile_id=row.profile_id, patient_name=profile.name, doctor_id=row.doctor_id,
        doctor_name=doctor.full_name, appointment_date=row.appointment_date.isoformat(), start=row.start_time,
        end=row.end_time, status=row.status, timezone='Asia/Kolkata', email_status=email.status if email else None)


def book(profile_id):
    value = parse(BookingInput)
    # Lock the current doctor and re-read the connection to serialize all capacity-consuming writes.
    profile, doctor = connected(profile_id)
    if not doctor:
        raise APIError(409, 'doctor_not_connected', 'Connect a doctor before booking an appointment')
    lock_doctor(doctor.id)
    db().refresh(profile, with_for_update=True)
    if profile.deleted_at or profile.referred_doctor_id != doctor.id:
        raise APIError(409, 'doctor_connection_changed', 'Doctor connection changed. Refresh available times')
    primary(profile.id)
    existing = db().scalar(select(CapacityAppointment).where(CapacityAppointment.patient_id == g.user.id,
        CapacityAppointment.request_id == str(value.request_id)))
    if existing:
        if existing.profile_id != profile.id or existing.window_id != str(value.window_id) or existing.appointment_date != value.appointment_date:
            raise APIError(409, 'booking_key_reused', 'Use a new request ID for a different booking')
        return jsonify(appointment=booking_data(existing)), 200
    validate_date(value.appointment_date)
    schedule = db().get(DoctorAppointmentSchedule, doctor.id)
    window = next((w for w in schedule.windows if w['id'] == str(value.window_id)), None) if schedule else None
    if not window or value.appointment_date.weekday() not in window['days']:
        raise APIError(409, 'window_unavailable', 'This time is no longer available. Refresh the schedule')
    if instant(value.appointment_date, window['start']) <= now():
        raise APIError(409, 'window_closed', 'This appointment window has already started')
    duplicate = db().scalar(select(CapacityAppointment.id).where(CapacityAppointment.profile_id == profile.id,
        CapacityAppointment.doctor_id == doctor.id, CapacityAppointment.appointment_date == value.appointment_date,
        CapacityAppointment.window_id == str(value.window_id), CapacityAppointment.status.in_(['BOOKED', 'COMPLETED'])))
    if duplicate:
        raise APIError(409, 'already_booked', 'This profile already has an appointment in this window')
    if window_count(doctor.id, window['id'], value.appointment_date) >= window['capacity']:
        raise APIError(409, 'window_full', 'This time is full. Please choose another available time')
    email = EmailNotification(user_id=doctor.id, template='appointment_booked', context_json=json.dumps(dict(
        patient_name=profile.name, booked_by=g.user.full_name, appointment_date=value.appointment_date.isoformat(),
        start=window['start'], end=window['end'])))
    db().add(email)
    db().flush()
    row = CapacityAppointment(doctor_id=doctor.id, patient_id=g.user.id, profile_id=profile.id,
        window_id=window['id'], request_id=str(value.request_id), appointment_date=value.appointment_date,
        start_time=window['start'], end_time=window['end'], status='BOOKED', email_id=email.id)
    db().add(row)
    db().flush()
    from doctor.notifications import queue_notification
    queue_notification(doctor.id, 'appointment_booked', 'appointment:'+row.id)
    audit('appointment_booked', doctor.id, g.user.id)
    db().commit()
    return jsonify(appointment=booking_data(row)), 201


def patient_bookings(profile_id):
    profile = primary(profile_id)
    rows = db().scalars(select(CapacityAppointment).where(CapacityAppointment.profile_id == profile.id,
        CapacityAppointment.patient_id == g.user.id).order_by(CapacityAppointment.appointment_date.desc(), CapacityAppointment.created_at.desc()).limit(200))
    return jsonify(items=[booking_data(row) for row in rows])


def doctor_bookings():
    day = chosen_date()
    rows = db().scalars(select(CapacityAppointment).where(CapacityAppointment.doctor_id == g.user.id,
        CapacityAppointment.appointment_date == day).order_by(CapacityAppointment.start_time, CapacityAppointment.created_at))
    return jsonify(items=[booking_data(row) for row in rows], date=day.isoformat())


class BookingStatusInput(Schema):
    status: Literal['CANCELLED', 'COMPLETED']


def change_status(booking_id, profile_id=None):
    value = parse(BookingStatusInput)
    if profile_id:
        primary(profile_id)
        if value.status != 'CANCELLED':
            raise APIError(403, 'forbidden', 'Patients can only cancel their appointments')
    row = db().get(CapacityAppointment, str(booking_id))
    if not row or (profile_id and (row.profile_id != str(profile_id) or row.patient_id != g.user.id)) or (not profile_id and row.doctor_id != g.user.id):
        raise APIError(404, 'appointment_not_found', 'Appointment not found')
    lock_doctor(row.doctor_id)
    db().refresh(row, with_for_update=True)
    if row.status != 'BOOKED':
        raise APIError(409, 'appointment_changed', 'This appointment is no longer booked')
    if value.status == 'COMPLETED' and instant(row.appointment_date, row.start_time) > now():
        raise APIError(409, 'appointment_not_started', 'The appointment window has not started')
    if profile_id and instant(row.appointment_date, row.start_time) <= now():
        raise APIError(409, 'appointment_started', 'Contact your doctor to change an appointment that has started')
    row.status = value.status
    if value.status == 'CANCELLED' and row.email_id:
        email = db().get(EmailNotification, row.email_id)
        if email and email.status == 'PENDING':
            email.status = 'CANCELLED'
    audit('appointment_'+value.status.lower(), row.doctor_id, g.user.id)
    db().commit()
    return jsonify(appointment=booking_data(row))


def appointment_profiles():
    from services.women_workspace import primary_id
    invited = select(FamilyInvitation.profile_id).where(FamilyInvitation.member_id == g.user.id,
        FamilyInvitation.accepted_at.is_not(None), FamilyInvitation.revoked_at.is_(None))
    rows = db().scalars(select(CareProfile).where(CareProfile.deleted_at.is_(None),
        or_(CareProfile.owner_id == g.user.id, CareProfile.id.in_(invited))).order_by(CareProfile.name))
    return jsonify(items=[dict(id=p.id, name=p.name, module=p.module) for p in rows if primary_id(p) == g.user.id])


def patient_change_status(profile_id, booking_id):
    return change_status(booking_id, profile_id)


route(bp, '/doctors/appointment-schedule', read_schedule, roles=('DOCTOR',))
route(bp, '/doctors/appointment-schedule', save_schedule, 'PUT', roles=('DOCTOR',), schema=ScheduleInput)
route(bp, '/doctors/booked-appointments', doctor_bookings, roles=('DOCTOR',))
route(bp, '/doctors/booked-appointments/<uuid:booking_id>/status', change_status, 'PATCH', roles=('DOCTOR',), schema=BookingStatusInput)
route(bp, '/patients/appointment-profiles', appointment_profiles, roles=('PATIENT',))
route(bp, '/patients/profiles/<uuid:profile_id>/appointment-availability', availability, roles=('PATIENT',))
route(bp, '/patients/profiles/<uuid:profile_id>/appointments', patient_bookings, roles=('PATIENT',))
route(bp, '/patients/profiles/<uuid:profile_id>/appointments', book, 'POST', roles=('PATIENT',), schema=BookingInput)
route(bp, '/patients/profiles/<uuid:profile_id>/appointments/<uuid:booking_id>/status', patient_change_status, 'PATCH', roles=('PATIENT',), schema=BookingStatusInput)
