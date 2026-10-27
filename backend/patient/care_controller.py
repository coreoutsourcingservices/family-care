from flask import g, request, jsonify, current_app
from core.schemas import parse
from core.care_schemas import CareProfileCreate, CareProfileReferral
from core.http import pagination
from core.errors import APIError
from services import care, care_uploads


def create_profile():
    return care.create_profile(g.user, parse(CareProfileCreate))


def profiles():
    return care.list_profiles(g.user, *pagination(), module=request.args.get('module'))


def profile(profile_id):
    return jsonify(profile=care.profile_data(care.accessible_profile(g.user, str(profile_id))))


def connect_profile_doctor(profile_id):
    return care.connect_profile(g.user, str(profile_id), parse(CareProfileReferral).referral_id)


def reports(profile_id):
    return care.list_reports(g.user, str(profile_id), *pagination())


def upload_report(profile_id):
    request.max_content_length = current_app.config['MAX_REPORT_BYTES'] + 65536
    # Authorize the profile before parsing a possibly large multipart body.
    care.accessible_profile(g.user, str(profile_id))
    if request.mimetype != 'multipart/form-data':
        raise APIError(415, 'multipart_required', 'Send multipart/form-data with field file')
    if len(request.files.getlist('file')) != 1 or set(request.files) != {'file'}:
        raise APIError(422, 'report_file_required', 'Send exactly one file in field file')
    return care_uploads.upload_report(g.user, str(profile_id), request.files['file'])


def download_report(profile_id, report_id):
    return care_uploads.download_report(g.user, str(profile_id), str(report_id))
