"""Synthetic Cloudinary/OCR browser fixture; no external files or medical data."""
import sys
from serve_women_workspace import app
from core.models import uid
import cloudinary.uploader
import services.report_text
from scripts.report_worker import start_background
app.config.update(OCR_PYTHON=sys.executable,CLOUDINARY_CLOUD_NAME='qa-cloud',CLOUDINARY_API_KEY='qa-key',CLOUDINARY_API_SECRET='qa-secret')
def upload(stream,**options):
    return dict(public_id=options['public_id'],type='authenticated',resource_type=options['resource_type'],asset_id=uid(),secure_url='https://res.cloudinary.com/qa-cloud/private-synthetic',format='pdf')
cloudinary.uploader.upload=upload
def processor(report,options):
    return dict(engine='Synthetic QA',source_language=options['source_language'],original_text='SYNTHETIC REPORT\nHemoglobin: 12.5 g/dL',english_text=None,translation_status='NOT_REQUESTED',page_count=1,warnings=['Synthetic test only.'])
services.report_text.run_processor=processor
if __name__=='__main__':
    start_background(app)
    app.run(host='127.0.0.1',port=5003,threaded=False,use_reloader=False)
