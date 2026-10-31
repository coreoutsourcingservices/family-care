"""Patient-owned asynchronous OCR; medical text is never included in logs."""
import json
import os
import subprocess
import tempfile
from pathlib import Path
from datetime import timedelta
from urllib.request import Request,urlopen,HTTPRedirectHandler,build_opener
from urllib.parse import urlsplit
from flask import current_app,g,jsonify
from pydantic import Field,model_validator
from sqlalchemy import select,or_,and_
from core.schemas import Schema,parse
from core.database import db
from core.errors import APIError
from core.models import ReportText,CareReport,CareProfile,User,now,uid
from services.care import accessible_report
from services.repository import audit

LANGUAGES={'hi':'Hindi','en':'English','mr':'Marathi','ne':'Nepali','sa':'Sanskrit','ta':'Tamil','te':'Telugu','ur':'Urdu','ar':'Arabic','fr':'French','de':'German','es':'Spanish','pt':'Portuguese','ru':'Russian'}
ROOT=Path(__file__).resolve().parents[1]
MESSAGES={'processing_failed':'Text extraction failed. Try a clearer scan or a smaller file.',
 'processor_stopped':'Report reading stopped before finishing. Please retry; your uploaded report is retained.',
 'processor_timeout':'Processing took too long. Try fewer pages or a clearer scan.',
 'report_download_failed':'The stored report could not be read. Please retry.',
 'invalid_document':'The image or PDF could not be decoded. Use a clear, unencrypted file.',
 'too_many_pages':'Please split PDFs into files of up to 5 pages.',
 'image_too_large':'The document image is too large to process safely.',
 'text_too_large':'The extracted text is too long. Split the document into smaller files.',
 'processor_unavailable':'The OCR processor is unavailable. Contact your care team.'}

class Options(Schema):
    source_language:str=Field(default='hi',max_length=8)
    target_language:str=Field(default='en',max_length=8)
    translate:bool=False
    auto_import:bool=False
    translate_to_english:bool=False
    external_translation_consent:bool=False

    @model_validator(mode='after')
    def valid(self):
        if self.source_language not in LANGUAGES:raise ValueError('Unsupported OCR language')
        if self.target_language not in LANGUAGES:raise ValueError('Unsupported display language')
        if self.translate and self.source_language!=self.target_language and not self.external_translation_consent:
            raise ValueError('Explicit consent is required before sending extracted medical text to MyMemory')
        if self.translate_to_english and self.source_language!='en' and not self.external_translation_consent:
            raise ValueError('Explicit consent is required before sending extracted medical text to MyMemory')
        return self

def processor_python():
    default=ROOT/'.ocr-venv'/('Scripts/python.exe' if os.name=='nt' else 'bin/python')
    return Path(current_app.config.get('OCR_PYTHON') or os.getenv('OCR_PYTHON') or default)

def options_endpoint():
    return jsonify(languages=[dict(code=code,name=name) for code,name in LANGUAGES.items()],max_file_bytes=10*1024*1024,max_pages=5,
        target_language='en',translation_provider='MyMemory via deep-translator',translation_enabled=True,max_translation_characters=4000,ocr_engine='PaddleOCR',configured=processor_python().is_file())

def serialize(row):
    if not row:return dict(status='NOT_REQUESTED',result=None)
    return dict(report_id=row.report_id,status=row.status,options=row.options,result=row.result or None,
        error=dict(code=row.error_code,message=MESSAGES.get(row.error_code,MESSAGES['processing_failed'])) if row.error_code else None,
        updated_at=row.updated_at.isoformat()+'Z')

def get_text(profile_id,report_id):
    accessible_report(g.user,str(profile_id),str(report_id))
    return jsonify(analysis=serialize(db().get(ReportText,str(report_id))))

def request_text(profile_id,report_id):
    report=accessible_report(g.user,str(profile_id),str(report_id))
    if report.category_reviewed and report.category == 'Scans':
        raise APIError(409,'imaging_ocr_skipped','X-ray and imaging files are stored without text extraction')
    value=parse(Options).model_dump(mode='json')
    if not processor_python().is_file():raise APIError(503,'processor_unavailable',MESSAGES['processor_unavailable'])
    # Lock the parent row, including when a result has not yet been created.
    db().scalar(select(CareReport).where(CareReport.id==report.id).with_for_update())
    row=db().get(ReportText,report.id)
    if row and row.status in ('QUEUED','PROCESSING'):return jsonify(analysis=serialize(row)),202
    if (value['translate_to_english'] or value.get('translate')) and value['source_language']!=value.get('target_language','en') and row and row.status=='PARTIAL' and row.result.get('translation_error',{}).get('code')=='translation_rate_limited' and row.updated_at>now()-timedelta(seconds=60):
        raise APIError(429,'translation_rate_limited','The translation provider is rate-limiting requests. Wait at least one minute before retrying.')
    if row and row.status=='COMPLETED' and row.options==value:return jsonify(analysis=serialize(row))
    if not row:row=ReportText(report_id=report.id,requested_by=g.user.id,options=value);db().add(row)
    row.options=value;row.requested_by=g.user.id;row.status='QUEUED';row.result={};row.error_code=None;row.lease_id=None;row.started_at=None
    audit('report_text_requested',g.user.id,g.user.id)
    db().commit()
    return jsonify(analysis=serialize(row)),202

def allowed_download(url,cloud):
    parts=urlsplit(url)
    return parts.scheme=='https' and not parts.username and not parts.password and parts.port in (None,443) and (
        parts.hostname=='res.cloudinary.com' and parts.path.startswith('/'+cloud+'/') or
        parts.hostname=='api.cloudinary.com' and parts.path.startswith('/v1_1/'+cloud+'/'))

class PrivateReportRedirect(HTTPRedirectHandler):
    def __init__(self,cloud):self.cloud=cloud
    def redirect_request(self,req,fp,code,msg,headers,newurl):
        if not allowed_download(newurl,self.cloud):raise ValueError('report_download_failed')
        return super().redirect_request(req,fp,code,msg,headers,newurl)

def report_bytes(report):
    limit=current_app.config['MAX_REPORT_BYTES']
    if report.storage_provider=='database':
        content=report.content or b''
    else:
        from services.care_uploads import report_data,credentials
        cloud=credentials()['cloud_name'];url=report_data(report)['url']
        if not url or not allowed_download(url,cloud):
            raise ValueError('report_download_failed')
        try:
            with build_opener(PrivateReportRedirect(cloud)).open(Request(url),timeout=30) as response:
                content=response.read(limit+1)
        except Exception:raise ValueError('report_download_failed') from None
    if not content or len(content)>limit:raise ValueError('invalid_document')
    return content

def run_processor(report,options):
    content=report_bytes(report)
    from services.care_uploads import file_type
    try:_,extension,_=file_type(content)
    except APIError:raise ValueError('invalid_document') from None
    with tempfile.TemporaryDirectory(prefix='familycare-ocr-') as temp:
        source=Path(temp)/('document.'+extension);output=Path(temp)/'result.json'
        source.write_bytes(content)
        args=[str(processor_python()),str(ROOT/'scripts'/'ocr_processor.py'),str(source),str(output),options['source_language']]
        if options['translate_to_english'] or options.get('translate'):args.append('--translate')
        if options.get('translate'):
            args.extend(['--target-language',options.get('target_language','en')])
        try:
            execution=subprocess.run(args,stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,
                timeout=360,check=False,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
        except subprocess.TimeoutExpired:raise ValueError('processor_timeout') from None
        except OSError:raise ValueError('processor_unavailable') from None
        if not output.is_file() and execution.returncode!=0:
            current_app.logger.warning('OCR processor exited before producing output: %s',execution.returncode)
            raise ValueError('processor_stopped')
        if not output.is_file() or output.stat().st_size>2*1024*1024:raise ValueError('processing_failed')
        result=json.loads(output.read_text(encoding='utf-8'))
        if result.get('error'):raise ValueError(result['error'])
        return result

def process_one():
    row=db().scalar(select(ReportText).where(or_(ReportText.status=='QUEUED',and_(ReportText.status=='PROCESSING',ReportText.started_at<now()-timedelta(minutes=10))))
        .order_by(ReportText.created_at).with_for_update(skip_locked=True).limit(1))
    if not row:db().rollback();return False
    report_id=row.report_id;lease=uid();options=dict(row.options)
    row.status='PROCESSING';row.started_at=now();row.lease_id=lease;db().commit()
    report=db().get(CareReport,report_id);owner=db().get(User,row.requested_by)
    result=None;code=None
    db().commit()  # Release the DB connection while CPU/network processing runs.
    try:
        if not report or not owner or owner.account_status!='ACTIVE':raise ValueError('processing_failed')
        profile=db().get(CareProfile,report.profile_id)
        if not profile or profile.deleted_at:raise ValueError('processing_failed')
        result=run_processor(report,options)
    except ValueError as error:
        code=str(error) if str(error) in MESSAGES else 'processing_failed'
    except Exception:
        code='processing_failed'
    db().expire_all();row=db().scalar(select(ReportText).where(ReportText.report_id==report_id).with_for_update())
    if row and row.lease_id==lease:
        row.result=result or {};row.error_code=code
        row.status='FAILED' if code else 'PARTIAL' if result.get('translation_status')=='FAILED' else 'COMPLETED'
        report=db().get(CareReport,row.report_id)
        if not code and report and options.get('auto_import'):
            from services.report_auto_records import save_extracted_records
            saved=save_extracted_records(report,result,row.requested_by)
            row.result=dict(result,auto_records=saved)
        if not code and report and not report.category_reviewed:
            from services.report_records import infer_category
            report.category=infer_category((result.get('english_text') or '')+'\n'+(result.get('original_text') or ''))
        db().commit()
    return True
