"""Isolated report UI fixture: mocked processor, synthetic private report, no SMTP."""
import sys
from child_frontend_fixture import app
from core.database import db
from core.models import CareProfile,CareReport
from sqlalchemy import select
import services.report_text
app.config['OCR_PYTHON']=sys.executable
with app.app_context():
    profile=db().scalar(select(CareProfile).where(CareProfile.module=='child'))
    db().add(CareReport(profile_id=profile.id,name='Synthetic report.pdf',content_type='application/pdf',storage_provider='database',content=b'%PDF-1.7\nSynthetic',size_bytes=20));db().commit()
def fake_processor(report,options):
    return dict(engine='PaddleOCR',source_language=options['source_language'],original_text='\u092a\u0930\u0940\u0915\u094d\u0937\u0923 \u0930\u093f\u092a\u094b\u0930\u094d\u091f',english_text='Synthetic test report' if options['translate_to_english'] else None,translation_status='COMPLETED' if options['translate_to_english'] else 'NOT_REQUESTED',page_count=1,warnings=['Synthetic browser test only.'])
services.report_text.run_processor=fake_processor
@app.after_request
def complete_fixture(response):
    from flask import request
    if request.method=='POST' and request.path.endswith('/text') and response.status_code==202:services.report_text.process_one()
    return response
if __name__=='__main__':
    from waitress import serve
    serve(app,host='127.0.0.1',port=5501,threads=1)
