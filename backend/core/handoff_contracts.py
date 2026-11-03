"""Synthetic request/response examples for consented doctor referrals."""
def enrich(paths):
    row=dict(id='<handoff UUID>',profile_id='<women profile UUID>',patient_name='Example Woman',
        source_name='Dr First',source_public_id='D000001',recipient_name='Dr Second',recipient_public_id='D000002',
        recipient_email='second@example.com',recipient_phone='',external=False,status='PENDING',
        summary=['Reason for referral: specialist review'],reports=[{'id':'<report UUID>','name':'lab.pdf'}],
        expires_at='<UTC expiry timestamp>',created_at='<UTC creation timestamp>')
    for path,methods in paths.items():
        if 'handoff' not in path:
            continue
        for method,op in methods.items():
            code='200'
            if path.endswith('/download'):
                op['responses']['200']={'description':'Selected original reports and doctor-authored summary ZIP',
                    'content':{'application/zip':{'schema':{'type':'string','format':'binary'}}}}
                continue
            if path.endswith('/handoff-options'):
                example={'patient_name':'Example Woman','reports':[{'id':'<report UUID>','name':'lab.pdf','category':'Lab tests'}]}
            elif method=='post':
                code='201';example={'handoff':row}
                op['requestBody']['content']['application/json']['example']={
                    'doctor_identifier':'D000002','summary':row['summary'],
                    'report_ids':['11111111-1111-4111-8111-111111111111'],'expires_in_days':7}
            elif method=='put':
                example={'handoff':dict(row,status='APPROVED')}
                op['requestBody']['content']['application/json']['example']={'decision':'APPROVED'}
            else:
                example={'items':[dict(row,status='APPROVED',direction='received')]} if path.startswith('/api/v1/doctors/') else {'items':[row]}
            op['responses']={key:value for key,value in op['responses'].items() if not key.startswith('2')}
            op['responses'][code]={'description':'Success','content':{'application/json':{'example':example}}}
