"""Private onboarding images, authorized with the limited setup token only."""
import io
import time
import cloudinary.uploader
import cloudinary.utils
from flask import request, jsonify, current_app
from sqlalchemy import select
from core.database import db
from core.errors import APIError
from core.models import User, DoctorProfile, uid
from core.security import decode_token
from services.care_uploads import credentials, file_type
from services.repository import audit


def image_details(profile):
    result = {}
    for kind, asset in (profile.onboarding_images or {}).items():
        result[kind] = dict(name=asset['name'], url=cloudinary.utils.private_download_url(
            asset['public_id'], asset['format'], resource_type='image', type='authenticated',
            expires_at=int(time.time()) + 300, secure=True, **credentials()))
    return result


def upload():
    request.max_content_length = 5 * 1024 * 1024 + 65536
    claims = decode_token(request.form.get('setup_token', ''), 'doctor_profile_setup')
    user = db().scalar(select(User).where(User.id == claims['sub']).with_for_update())
    if (not user or user.role != 'DOCTOR' or not user.email_verified or
            user.account_status != 'ACTIVE' or user.approval_status not in ('PROFILE_REQUIRED', 'REJECTED')):
        raise APIError(409, 'invalid_state', 'Images can only be changed during account setup')
    kind = request.form.get('kind')
    if kind not in ('profile_photo', 'degree_photo'):
        raise APIError(422, 'invalid_image_kind', 'Choose profile_photo or degree_photo')
    file = request.files.get('file')
    if not file or not file.filename:
        raise APIError(422, 'image_required', 'Choose an image to upload')
    content = file.stream.read(5 * 1024 * 1024 + 1)
    if not content or len(content) > 5 * 1024 * 1024:
        raise APIError(422, 'invalid_image_size', 'Choose a nonempty image up to 5 MB')
    _, extension, resource = file_type(content)
    if resource != 'image':
        raise APIError(422, 'invalid_image_type', 'Use a JPEG, PNG or WebP image')
    keys = credentials()
    public_id = f'familycare/{user.public_id}/onboarding/{kind}_{uid()}'
    try:
        asset = cloudinary.uploader.upload(io.BytesIO(content), public_id=public_id,
            resource_type='image', type='authenticated', overwrite=False, timeout=30, **keys)
        if asset.get('public_id') != public_id or asset.get('type') != 'authenticated' or asset.get('resource_type') != 'image':
            raise ValueError('Unexpected image metadata')
    except Exception:
        raise APIError(502, 'image_upload_failed', 'Image upload failed. Please try again.') from None
    profile = db().get(DoctorProfile, user.id)
    old = (profile.onboarding_images or {}).get(kind)
    try:
        profile.onboarding_images = {**(profile.onboarding_images or {}), kind: {
            'public_id': public_id, 'format': asset.get('format') or extension,
            'name': kind.replace('_', ' ') + '.' + extension}}
        audit('doctor_setup_image_uploaded', user.id, user.id)
        db().commit()
    except Exception:
        db().rollback()
        cloudinary.uploader.destroy(public_id, resource_type='image', type='authenticated', **keys)
        raise
    if old:
        try:
            cloudinary.uploader.destroy(old['public_id'], resource_type='image', type='authenticated', **keys)
        except Exception:
            current_app.logger.warning('Could not remove replaced doctor onboarding image')
    return jsonify(images=image_details(profile)), 201
