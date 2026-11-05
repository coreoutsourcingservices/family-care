import io
import re
import time
import cloudinary.uploader
import cloudinary.utils
from flask import current_app, jsonify, send_file, request, g
from werkzeug.utils import secure_filename
from sqlalchemy.exc import SQLAlchemyError
from core.database import db
from core.models import CareReport, ProfileDoctorGrant, uid
from core.errors import APIError
from services.repository import audit
from services.care import accessible_profile, accessible_report


def credentials():
    values = {key: current_app.config.get('CLOUDINARY_'+key.upper(), '')
              for key in ('cloud_name', 'api_key', 'api_secret')}
    if not all(values.values()):
        raise APIError(503, 'cloudinary_not_configured', 'Set CLOUDINARY_CLOUD_NAME, CLOUDINARY_API_KEY and CLOUDINARY_API_SECRET in backend .env')
    return values


def report_data(report,internal=False):
    url = None
    if report.storage_provider == 'cloudinary' and all(current_app.config.get('CLOUDINARY_'+key)
            for key in ('CLOUD_NAME', 'API_KEY', 'API_SECRET')):
        url = cloudinary.utils.private_download_url(report.cloudinary_public_id,
            report.file_format if report.resource_type == 'image' else '',
            resource_type=report.resource_type, type='authenticated', attachment=report.resource_type == 'raw', expires_at=int(time.time())+300,
            secure=True, **credentials())
    if not internal and getattr(g,'user',None) and g.user.role=='DOCTOR' and db().get(ProfileDoctorGrant,report.profile_id):url=None
    if not internal and getattr(g,'user',None) and g.user.role=='PATIENT':
        from core.models import FamilyInvitation
        from sqlalchemy import select
        if db().scalar(select(FamilyInvitation.id).where(FamilyInvitation.profile_id==report.profile_id,FamilyInvitation.owner_id==g.user.id,FamilyInvitation.accepted_at.is_not(None))):url=None
    return dict(id=report.id, profile_id=report.profile_id, name=report.name, title=report.title, category=report.category, category_reviewed=report.category_reviewed,
                content_type=report.content_type, storage_provider=report.storage_provider,
                url=url, secure_url=report.secure_url, url_expires_in=300 if url else None,
                public_id=report.cloudinary_public_id, asset_id=report.cloudinary_asset_id,
                folder=report.folder, resource_type=report.resource_type,
                delivery_type=report.delivery_type, size_bytes=report.size_bytes,
                created_at=report.created_at.isoformat()+'Z')


def file_type(content):
    if content.startswith(b'%PDF-'):
        return 'application/pdf', 'pdf', 'raw'
    if content.startswith(b'\x89PNG\r\n\x1a\n'):
        return 'image/png', 'png', 'image'
    if content.startswith(b'\xff\xd8\xff'):
        return 'image/jpeg', 'jpg', 'image'
    if content[:4] == b'RIFF' and content[8:12] == b'WEBP':
        return 'image/webp', 'webp', 'image'
    raise APIError(422, 'unsupported_report_type', 'Only PDF, JPEG, PNG and WebP reports are accepted')


def upload_report(user, profile_id, file):
    profile = accessible_profile(user, profile_id)
    title=request.form.get('title','').strip()
    if 'title' in request.form and (not title or len(title)>160):raise APIError(422,'invalid_title','Enter a report title up to 160 characters')
    category=request.form.get('category','Others')
    if category not in ('Doctor report','Lab tests','Prescriptions','Scans','Vaccination','Others'):
        raise APIError(422,'invalid_category','Choose a report category')
    read_requested=request.form.get('auto_read')=='true' and category!='Scans'
    from services.report_text import Options,processor_python
    try:
        options=Options(source_language=request.form.get('source_language','en'),auto_import=False).model_dump(mode='json')
    except ValueError:
        raise APIError(422,'invalid_language','Choose a supported document language') from None
    # Saving a private document must not depend on the optional OCR runtime.
    # If reading is unavailable, keep the original and let the owner retry later.
    auto_read=read_requested and processor_python().is_file()
    if not file or not file.filename:
        raise APIError(422, 'report_file_required', 'Send a file in multipart field file')
    limit = current_app.config['MAX_REPORT_BYTES']
    content = file.stream.read(limit+1)
    if not content:
        raise APIError(422, 'empty_report', 'Report file is empty')
    if len(content) > limit:
        raise APIError(413, 'report_too_large', 'Report file must be 10 MB or smaller')
    content_type, extension, resource_type = file_type(content)
    keys = credentials()
    name = re.sub(r'[\x00-\x1f\x7f]', '', file.filename.replace('\\', '/').split('/')[-1])[:255] or 'report.'+extension
    stem = (secure_filename(name).rsplit('.', 1)[0] or 'report')[:80]
    folder = f'familycare/{user.public_id}/profiles/{profile.id}/{profile.module}/reports'
    report_id = uid()
    public_id = f'{folder}/{report_id}_{stem}' + ('.pdf' if resource_type == 'raw' else '')
    try:
        result = cloudinary.uploader.upload(io.BytesIO(content), public_id=public_id,
            asset_folder=folder, resource_type=resource_type, type='authenticated',
            overwrite=False, unique_filename=False, use_filename=False, timeout=30, secure=True, **keys)
    except Exception as error:
        current_app.logger.warning('Cloudinary report upload failed: %s', type(error).__name__)
        raise APIError(502, 'report_upload_failed', 'Cloudinary could not accept the report. Please try again.') from None
    if (result.get('public_id') != public_id or result.get('type') != 'authenticated'
            or result.get('resource_type') != resource_type
            or not result.get('secure_url', '').startswith('https://res.cloudinary.com/'+keys['cloud_name']+'/')):
        raise APIError(502, 'invalid_upload_response', 'Cloudinary returned unexpected report metadata')
    report = CareReport(id=report_id, profile_id=profile.id, name=name, title=title or None, category=category,category_reviewed='category' in request.form,content_type=content_type,
        storage_provider='cloudinary', content=None, cloudinary_public_id=public_id,
        cloudinary_asset_id=result.get('asset_id'), secure_url=result['secure_url'], folder=folder,
        resource_type=resource_type, delivery_type='authenticated',
        file_format=result.get('format') or extension, size_bytes=len(content))
    try:
        db().add(report)
        if auto_read:
            from core.models import ReportText
            db().flush()
            db().add(ReportText(report_id=report.id,requested_by=user.id,options=options,status='QUEUED',result={}))
        from doctor.notifications import queue_notification
        queue_notification(profile.referred_doctor_id, 'report_shared', 'report:' + report.id)
        audit('care_report_uploaded', user.id, user.id)
        db().commit()
    except SQLAlchemyError:
        db().rollback()
        try:
            cloudinary.uploader.destroy(public_id, resource_type=resource_type, type='authenticated', **keys)
        except Exception as error:
            current_app.logger.error('Cloudinary orphan cleanup failed: %s', type(error).__name__)
        raise
    extraction=dict(status='QUEUED' if auto_read else 'UNAVAILABLE' if read_requested else 'SKIPPED' if category=='Scans' else 'NOT_REQUESTED')
    if read_requested and not auto_read:
        extraction['message']='Report uploaded. Automatic text reading is unavailable; you can retry reading this saved report later.'
    return jsonify(report=report_data(report),text_extraction=extraction), 201


def download_report(user, profile_id, report_id):
    report = accessible_report(user, profile_id, report_id)
    from core.models import FamilyInvitation
    from sqlalchemy import select
    family_view=user.role=='PATIENT' and db().scalar(select(FamilyInvitation.id).where(FamilyInvitation.profile_id==profile_id,FamilyInvitation.owner_id==user.id,FamilyInvitation.accepted_at.is_not(None)))
    if family_view or user.role=='DOCTOR' and db().get(ProfileDoctorGrant,report.profile_id):
        from services.report_text import report_bytes
        response=send_file(io.BytesIO(report_bytes(report)),mimetype=report.content_type,as_attachment=True,download_name=report.name)
        response.headers['Cache-Control']='no-store'
        return response
    if report.storage_provider == 'database':
        return send_file(io.BytesIO(report.content or b''), mimetype=report.content_type,
                         as_attachment=True, download_name=report.name)
    credentials()
    return jsonify(report=report_data(report))
