import io
import json
from pathlib import Path
from unittest.mock import patch
from test_care import patient, create_profile, cloud


def test_women_sample_report_upload_and_real_ocr_result_round_trip(app, client, cloud, monkeypatch):
    # The result fixture was produced by the installed PaddleOCR runner from this PDF.
    import sys
    monkeypatch.setitem(app.config,'OCR_PYTHON',sys.executable)
    root=Path(__file__).resolve().parents[2]/'app/public/demo/women'
    result=json.loads((root/'ocr-result.json').read_text(encoding='utf-8'))
    assert result.get('engine')=='PaddleOCR' and result.get('page_count')==1
    assert all(value in result['original_text'] for value in ['DEMO REPORT','Demo Woman','Hemoglobin','12.4','TSH','2.1','Fasting glucose','89'])
    owner=patient(app,client)
    profile=create_profile(client,owner,module='women',full_name='Demo Woman (Sample)',date_of_birth='1996-04-12',gender='Female')
    for index,section in enumerate(['health','cycle','nutrition']):
        saved=client.put(f'/api/v1/women/profiles/{profile}/diary/de000000-0000-4000-8000-{index+1:012d}',headers=owner,json={'section':section,'data':{'date':'2026-11-05','title':'DEMO - '+section,'notes':'Synthetic example only'},'version':0})
        assert saved.status_code==200,saved.json
    uploaded=client.post(f'/api/v1/women/profiles/{profile}/reports',headers=owner,data={'file':(io.BytesIO((root/'demo-women-lab-report.pdf').read_bytes()),'demo-women-lab-report.pdf'),'category':'Lab tests','source_language':'en','auto_read':'true'})
    assert uploaded.status_code==201,uploaded.json
    identifier=uploaded.json['report']['id']
    endpoint=f'/api/v1/patients/profiles/{profile}/reports/{identifier}/text'
    assert client.get(endpoint,headers=owner).json['analysis']['status']=='QUEUED'
    with app.app_context():
        from services.report_text import process_one
        with patch('services.report_text.run_processor',return_value=result):assert process_one()
    analysis=client.get(endpoint,headers=owner).json['analysis']
    assert analysis['status']=='COMPLETED'
    assert '12.4' in analysis['result']['original_text']
    workspace=client.get(f'/api/v1/women/profiles/{profile}/workspace',headers=owner).json
    assert {'health','cycle','nutrition'}.issubset({record['section'] for record in workspace['records']})
