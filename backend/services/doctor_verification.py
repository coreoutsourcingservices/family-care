"""Admin-triggered reference checks; providers never approve an account."""
import hashlib
import json
import re
import threading
import time
from datetime import datetime, timedelta
from urllib.parse import urlencode, urlparse
from urllib.request import Request, urlopen
from flask import current_app, jsonify
from sqlalchemy import select
from core.database import db
from core.errors import APIError
from core.models import User, DoctorProfile, ApprovalRequest, now
from services.repository import user_by_id, audit

NMC_URL = 'https://www.nmc.org.in/information-desk/indian-medical-register/'
HFR_URL = 'https://facility.abdm.gov.in/searchV2'
GEOCODER_POLICY = 'https://operations.osmfoundation.org/policies/nominatim/'
_geo_lock = threading.Lock()
_geo_last = 0.0


def fetch_json(url):
    request = Request(url, headers={'User-Agent': current_app.config['VERIFICATION_USER_AGENT'], 'Accept': 'application/json'})
    with urlopen(request, timeout=current_app.config['DOCTOR_CHECK_TIMEOUT']) as response:
        data = response.read(1024 * 1024 + 1)
        if len(data) > 1024 * 1024:
            raise ValueError('Provider response too large')
        return json.loads(data)


def normalized(value):
    return re.sub(r'[^a-z0-9]', '', str(value or '').lower())


def clean_name(value):
    return normalized(re.sub(r'^\s*(?:dr\.?|doctor)\s+', '', str(value or ''), flags=re.I))


def clean_council(value):
    return normalized(re.sub(r'\b(?:state|medical|council|of)\b', '', str(value or ''), flags=re.I))


def candidates(payload, depth=0):
    if depth > 5:
        return []
    if isinstance(payload, list):
        return [row for child in payload[:50] for row in candidates(child, depth + 1)]
    if not isinstance(payload, dict):
        return []
    aliases = {
        'name': ('name', 'doctorname', 'fullname', 'drname'),
        'registration': ('regnumber', 'registrationnumber', 'registrationno', 'registration', 'regno', 'medicalregistrationnumber'),
        'council': ('statecouncil', 'registeringcouncil', 'medicalcouncil', 'council', 'smcname', 'stateofregistration'),
    }
    fields = {normalized(key): value for key, value in payload.items()}
    row = {key: next((str(fields[alias])[:300] for alias in names if isinstance(fields.get(alias), (str, int))), '')
           for key, names in aliases.items()}
    found = [row] if row['registration'] and row['name'] else []
    for key in ('data', 'results', 'doctors', 'records', 'result', 'doctor', 'matches'):
        found.extend(candidates(payload.get(key), depth + 1))
    return found[:50]


def registration_check(values):
    result = dict(provider='AskMyDoc (third party)', source_url='https://api.askmydoc.in/',
                  official_search_url=NMC_URL, status='unavailable',
                  message='Registry service unavailable. Check the official register manually.')
    try:
        payload = fetch_json('https://api.askmydoc.in/api/verify?' + urlencode({
            'reg_number': values['medical_registration_number'], 'state_council': values['registering_council']}))
        if not isinstance(payload, dict) or payload.get('success') is False:
            return result
        rows = candidates(payload)
        result['records'] = rows[:10]
        matching = [row for row in rows if normalized(row['registration']) == normalized(values['medical_registration_number'])]
        if not matching:
            result.update(status='manual_review', message='No comparable registration record returned. Check NMC/council manually.')
            return result
        checks = [dict(registration=True, name=clean_name(row['name']) == clean_name(values['full_name']),
                       council=clean_council(row['council']) == clean_council(values['registering_council']) if row['council'] else None)
                  for row in matching]
        full = next((check for check in checks if check['name'] and check['council'] is True), None)
        if full:
            result.update(status='match', comparisons=full,
                          message='Name, registration and council match a third-party record. Admin must confirm against official records.')
        else:
            result.update(status='manual_review' if any(check['council'] is None for check in checks) else 'mismatch',
                          comparisons=checks[0], message='Returned identity details need manual review; do not treat registration lookup alone as verification.')
    except Exception:
        # Provider failures do not reject the doctor or expose response bodies/addresses in logs.
        pass
    return result


def postal_check(address):
    pins = re.findall(r'(?<!\d)[1-9]\d{5}(?!\d)', address or '')
    result = dict(provider='India Postal PIN API', status='manual_review',
                  message='Provide one six-digit PIN in the address for a postal-area lookup.')
    if len(set(pins)) != 1:
        return result
    pin = pins[0]
    result['pincode'] = pin
    try:
        payload = fetch_json('https://api.postalpincode.in/pincode/' + pin)
        offices = payload[0].get('PostOffice') if isinstance(payload, list) and payload and isinstance(payload[0], dict) else None
        if not isinstance(offices, list) or not offices:
            result.update(status='not_found', message='No postal area returned for this PIN. Check the address manually.')
            return result
        areas = [dict(state=str(row.get('State', ''))[:100], district=str(row.get('District', ''))[:100],
                      post_office=str(row.get('Name', ''))[:100]) for row in offices[:50] if isinstance(row, dict)]
        state_match = any(normalized(area['state']) in normalized(address) for area in areas if area['state'])
        result.update(status='area_match' if state_match else 'manual_review', areas=areas,
                      state_in_address=state_match,
                      message='PIN area found; state text matches.' if state_match else 'PIN area found; confirm the state against the entered address.')
        result['limitation'] = 'Postal area lookup does not verify the building, street, ownership or doctor identity.'
    except Exception:
        result.update(status='unavailable', message='Postal service unavailable; verify PIN and state manually.')
    return result


def geocoder_slot():
    global _geo_last
    uri = current_app.config['RATELIMIT_STORAGE_URI']
    if uri.startswith(('redis://', 'rediss://')):
        try:
            from redis import Redis
            return bool(Redis.from_url(uri).set('familycare:clinic-geocoder:slot', '1', nx=True, px=1100))
        except Exception:
            return False
    with _geo_lock:
        stamp = time.monotonic()
        if stamp - _geo_last < 1.1:
            return False
        _geo_last = stamp
        return True


def clinic_check(address):
    result = dict(provider='OpenStreetMap Nominatim', attribution='© OpenStreetMap contributors',
                  policy_url=GEOCODER_POLICY, status='manual_review',
                  message='Location search is supporting evidence only; confirm the clinic in HFR.', official_search_url=HFR_URL)
    endpoint = current_app.config['CLINIC_GEOCODER_URL']
    parsed = urlparse(endpoint)
    if not current_app.config['CLINIC_GEOCODING_ENABLED'] or parsed.scheme != 'https' or not parsed.hostname:
        return result
    if not geocoder_slot():
        result.update(status='rate_limited', message='Location lookup busy. Try later or check the clinic in HFR.')
        return result
    try:
        payload = fetch_json(endpoint + '?' + urlencode(dict(q=address, format='jsonv2', limit=3, countrycodes='in', addressdetails=1)))
        if not isinstance(payload, list):
            raise ValueError('Unexpected geocoder response')
        result['locations'] = [dict(display_name=str(row.get('display_name', ''))[:600],
                                    latitude=str(row.get('lat', ''))[:30], longitude=str(row.get('lon', ''))[:30])
                               for row in payload[:3] if isinstance(row, dict)]
        result.update(status='locations_found' if result['locations'] else 'not_found',
                      message='Possible locations found. This does not confirm clinic registration.' if result['locations']
                      else 'No location found. This does not prove the clinic is invalid; check HFR manually.')
    except Exception:
        result.update(status='unavailable', message='Location service unavailable; check HFR manually.')
    return result


def snapshot(user, profile):
    return dict(full_name=user.full_name, medical_registration_number=profile.medical_registration_number,
                registering_council=profile.registering_council, address=profile.address, clinic_address=profile.clinic_address)


def check_doctor(actor, identifier):
    if actor.role != 'ADMIN':
        raise APIError(403, 'forbidden', 'Only an admin can check doctor applications')
    user = user_by_id(identifier)
    if not user or user.role != 'DOCTOR':
        raise APIError(404, 'not_found', 'Doctor not found')
    application = db().scalar(select(ApprovalRequest).where(ApprovalRequest.applicant_id == user.id))
    if not application or application.status != 'PENDING' or user.approval_status != 'PENDING_APPROVAL':
        raise APIError(409, 'invalid_state', 'Submit a complete profile before verification')
    profile = db().get(DoctorProfile, user.id)
    values = snapshot(user, profile)
    if not all(values.values()):
        raise APIError(409, 'profile_incomplete', 'Professional details and both addresses are required before checking')
    fingerprint = hashlib.sha256(json.dumps(values, sort_keys=True).encode()).hexdigest()
    previous = profile.verification_check
    if previous and previous.get('fingerprint') == fingerprint:
        try:
            if datetime.fromisoformat(previous['checked_at'].removesuffix('Z')) > now() - timedelta(minutes=10):
                return jsonify(verification_check=previous, cached=True, doctor_status='pending')
        except (ValueError, KeyError):
            pass
    user_id, actor_id = user.id, actor.id
    db().rollback()  # Never keep a database lock/transaction open while waiting on providers.
    result = dict(checked_at=now().isoformat()+'Z', checked_by=actor_id, fingerprint=fingerprint,
                  registration=registration_check(values), address=postal_check(values['address']),
                  clinic_postal=postal_check(values['clinic_address']), clinic=clinic_check(values['clinic_address']),
                  official_registry=dict(status='manual_review', search_url=NMC_URL),
                  facility_registry=dict(status='manual_review', search_url=HFR_URL),
                  requires_admin_review=True, auto_approved=False)
    user = db().scalar(select(User).where(User.id == user_id).with_for_update())
    profile = db().get(DoctorProfile, user_id, populate_existing=True)
    if user.approval_status != 'PENDING_APPROVAL' or snapshot(user, profile) != values:
        raise APIError(409, 'application_changed', 'Application changed while checking. Refresh before reviewing.')
    profile.verification_check = result
    audit('doctor_reference_checked', user_id, actor_id)
    db().commit()
    return jsonify(verification_check=result, cached=False, doctor_status='pending')
