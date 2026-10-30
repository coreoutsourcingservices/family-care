"""Supplement route metadata for dynamic CRUD handlers and multipart contracts."""
import re
from copy import deepcopy
from core import vaccination_schemas as vs

def sample(schema,definitions=None):
    definitions=definitions or {}
    if '$ref' in schema:return sample(definitions.get(schema['$ref'].split('/')[-1],{}),definitions)
    if 'default' in schema:return deepcopy(schema['default'])
    if 'enum' in schema:return schema['enum'][0]
    if 'anyOf' in schema:return sample(next((s for s in schema['anyOf'] if s.get('type')!='null'),{}),definitions)
    kind=schema.get('type')
    if kind=='object':return {k:sample(v,definitions) for k,v in schema.get('properties',{}).items()}
    if kind=='array':return []
    if kind in ('integer','number'):return schema.get('minimum',0)
    if kind=='boolean':return False
    if schema.get('format')=='uuid':return '00000000-0000-4000-8000-000000000001'
    if schema.get('format')=='date':return '2026-10-30'
    if schema.get('format') in ('uri','uri-reference'):return 'https://example.org/guideline'
    return 'Example value'

def enrich(paths,components):
    from patient.child_routes import RecordInput,PreferencesInput,KINDS
    from patient.adult_routes import AdultInput
    vaccine=vs.VaccineInput(code='EXAMPLE_VACCINE',name_en='Example vaccine',category='Government',protects_against='Source-reviewed indication').model_dump(mode='json')
    vaccine['id']='00000000-0000-4000-8000-000000000001'
    schedule=vs.ScheduleInput(vaccine_id=vaccine['id'],schedule_type='UIP',dose_code='D1',dose_name='Example dose',version='example-v1',age_label='Source-defined age',age_unit='days',age_start=0,age_end=0,route='Other',source_url='https://example.org/guideline',source_reference='Synthetic contract example only',effective_from='2026-10-30').model_dump(mode='json')
    schedule.update(id='<schedule UUID>',vaccine=vaccine,status='DRAFT',published_at=None)
    def body(operation,model):
        definition=model.model_json_schema(ref_template='#/components/schemas/{model}')
        components.update(definition.pop('$defs',{}));components[model.__name__]=definition
        operation['requestBody']={'required':True,'content':{'application/json':{'schema':{'$ref':'#/components/schemas/'+model.__name__},'example':sample(definition,components)}}}
    def result(operation,value,status=200):
        for key in list(operation['responses']):
            if key.startswith('2'):del operation['responses'][key]
        operation['responses'][str(status)]={'description':'Success; example uses synthetic values','content':{'application/json':{'example':value}}}
    for path,methods in paths.items():
      for method,op in methods.items():
        op['operationId']+='_'+method
        model=None
        if re.fullmatch(r'/api/v1/patients/profiles/\{profile_id\}',path) and method=='put':
            from core.care_schemas import CareProfileEdit
            model=CareProfileEdit
        if '/vaccination/' in path:
            end=path.rsplit('/',1)[-1]
            if method=='post' and '/import-' in path:result(op,{'created':26 if path.endswith('uip') else 18,'skipped':0,'schedule_type':'UIP' if path.endswith('uip') else 'IAP','message':'Drafts saved. Independent medical review and admin publication are required.'})
            elif method in ('post','put'):
                if end=='vaccines' or '/vaccines/' in path:model=vs.VaccineInput
                elif end=='eligibility':model=vs.EligibilityInput
                elif end=='reminders':model=vs.ReminderInput
                elif end=='submit-review':model=vs.AssignReview
                elif end=='retire':model=vs.RetireInput
                elif end not in ('publish','withdraw'):model=vs.ScheduleInput
        if '/vaccination-reviews/' in path and method=='post':model=vs.MedicalReview
        if path.endswith('/vaccination-context'):
            if method=='put':model=vs.ChildContextInput
            result(op,{'context':sample(vs.ChildContextInput.model_json_schema())})
        child_resource=next((r for r in KINDS if re.search(r'/children/\{child_id\}/'+re.escape(r)+r'(?:/\{record_id\})?$',path)),None)
        if child_resource and method in ('post','patch'):model=RecordInput
        if '/patients/adults/' in path and '/records' in path and method in ('post','patch') and not path.endswith('/delete'):model=AdultInput
        if path.endswith('/reminder-preferences') and method=='put':model=PreferencesInput
        if path.endswith('/vaccination-plan'):
            from services.child_vaccination_plan import Decision
            if method=='post':model=Decision;result(op,{'message':'Child-specific applicability saved. Recorded doses and routine dates were not changed.'})
            else:result(op,{'child':{'id':'<child UUID>','name':'Example child'},'UIP':{'items':[],'counts':{},'context':{},'status':'NOT_AVAILABLE','message':'No reviewed schedule has been published for this schedule type.'},'IAP':{'items':[],'counts':{},'context':{},'status':'NOT_AVAILABLE','message':'No reviewed schedule has been published for this schedule type.'}})
        if model:body(op,model)
        if path.endswith('/text') and '/reports/' in path:
            from services.report_text import Options
            if method=='post':body(op,Options)
            result(op,{'analysis':{'report_id':'<report UUID>','status':'QUEUED','options':{'source_language':'hi','translate_to_english':False,'external_translation_consent':False},'result':None,'error':None,'updated_at':'2026-10-30T00:00:00Z'}} if method=='post' else {'analysis':{'status':'NOT_REQUESTED','result':None}},202 if method=='post' else 200)
        if child_resource or '/patients/adults/' in path and '/records' in path:
            record={'id':'<record UUID>','kind':KINDS[child_resource] if child_resource else 'history','title':'Example record','date':'2026-10-30','status':'Recorded','notes':'Synthetic example','verification_status':'PARENT_REPORTED' if child_resource else 'SELF_REPORTED'}
            if method=='delete' or path.endswith('/delete'):result(op,{'message':'Record removed'})
            elif method=='get' and '{record_id}' not in path:result(op,{'items':[record],'total':1,'page':1,'per_page':25})
            else:result(op,{'record':record},201 if method=='post' and '{record_id}' not in path else 200)
        if path.endswith('/profile-photo') or path.endswith('/setup-images'):
            photo={'name':'profile photo.png','url':'<short-lived signed private image URL>'}
            if method in ('post','put'):
                props={'file':{'type':'string','format':'binary','description':'JPEG/PNG/WebP, max 5 MB'}}
                if path.endswith('/setup-images'):props.update(setup_token={'type':'string'},kind={'type':'string','enum':['profile_photo','degree_photo']})
                op['requestBody']={'required':True,'content':{'multipart/form-data':{'schema':{'type':'object','required':list(props),'properties':props}}}}
                result(op,{'images':{'profile_photo':photo}},201)
            elif method=='delete':result(op,{'photo':None,'message':'Profile photo removed'})
            else:result(op,{'photo':photo})
        if re.search(r'/(?:admin|superadmin)/doctors/\{user_id\}$',path):
            result(op,{'user':{'id':'<UUID>','public_id':'D000001','full_name':'Example doctor','role':'DOCTOR','approval_status':'APPROVED','doctor':{'qualification':'MBBS','images':{}}}})
        if re.search(r'/(?:admin|superadmin)/doctors/\{user_id\}/profiles$',path):result(op,{'items':[{'id':'<profile UUID>','full_name':'Example member','module':'child','owner_id':'<patient UUID>','date_of_birth':'2020-01-01'}],'total':1,'page':1,'per_page':25})
        if path.endswith('/doctor') and method=='delete':result(op,{'profile':{'id':'<profile UUID>','doctor':None},'message':'Doctor disconnected from this profile'})
        if '/doctors/notifications' in path:
            op['description']='Signed doctor notification token required in Authorization bearer header; access/setup tokens are not interchangeable with this token.'
            op['security']=[{'bearerAuth':[]}]
            if path.endswith('/subscriptions'):
                schema={'type':'object','required':['endpoint'],'properties':{'endpoint':{'type':'string','format':'uri'}}}
                example={'endpoint':'https://push.example.org/device-subscription'}
                if method=='post':
                    schema['required'].append('keys');schema['properties']['keys']={'type':'object','required':['p256dh','auth'],'properties':{'p256dh':{'type':'string'},'auth':{'type':'string'}}}
                    example['keys']={'p256dh':'<browser subscription p256dh key>','auth':'<browser subscription auth key>'}
                op['requestBody']={'required':True,'content':{'application/json':{'schema':schema,'example':example}}}
                result(op,{'message':'Notifications enabled on this browser' if method=='post' else 'Notifications disabled on this browser'},201 if method=='post' else 200)
            elif path.endswith('/push-config'):result(op,{'public_key':'<VAPID public key>','enabled':True})
            elif path.endswith('/read'):result(op,{'message':'Notification marked as read'})
            else:result(op,{'items':[],'total':0,'unread':0,'page':1,'per_page':25})
        if '/vaccination/' in path or '/vaccination-reviews' in path:
            last=path.rsplit('/',1)[-1]
            if '/import-' not in path:
                if last=='reviewers':result(op,{'items':[{'id':'<doctor UUID>','name':'Example reviewer','qualification':'MBBS','registration':'EXAMPLE-1','council':'Example council'}]})
                elif last=='audit':result(op,{'items':[],'total':0,'page':1,'per_page':25})
                elif '/vaccines' in path:result(op,{'items':[vaccine],'total':1,'page':1,'per_page':25} if method=='get' else {'vaccine':vaccine},201 if method=='post' else 200)
                elif method=='get':result(op,{'items':[],'total':0,'page':1,'per_page':25})
                else:
                    state='IN_REVIEW' if last=='submit-review' else 'PUBLISHED' if last=='publish' else 'RETIRED' if last=='retire' else 'APPROVED' if '/vaccination-reviews/' in path else 'DRAFT'
                    value={**schedule,'status':state,'created_by':'<author UUID>','reviewer_id':'<reviewer UUID>' if state!='DRAFT' else None}
                    if state=='PUBLISHED':value['published_at']='2026-10-30T00:00:00Z'
                    result(op,{'schedule':value},201 if method=='post' and last=='schedules' else 200)
        if path=='/api/v1/vaccines':result(op,{'items':[],'total':0,'status':'NOT_AVAILABLE'})
        if path=='/api/v1/vaccination-schedules':result(op,{'items':[],'total':0,'status':'NOT_AVAILABLE'})
        if re.fullmatch(r'/api/v1/vaccination-schedules/\{schedule_id\}',path):result(op,{'schedule':{**schedule,'status':'PUBLISHED','published_at':'2026-10-30T00:00:00Z'}})
        if re.fullmatch(r'/api/v1/(admin|superadmin)/patients/\{user_id\}',path):result(op,{'user':{'id':'<patient UUID>','public_id':'C000001','full_name':'Example patient','role':'PATIENT','created_at':'2026-10-30T00:00:00Z'},'profile_counts':{'total':0,'members':0,'self':0,'child':0,'adult':0,'women':0}})
        if re.fullmatch(r'/api/v1/doctors/care-profiles/\{profile_id\}/records',path):result(op,{'items':[],'total':0,'page':1,'per_page':25})
        if path.startswith('/api/v1/children') and not child_resource and not path.endswith('/vaccination-context'):
            from core.models import CareProfile
            from patient.child_routes import child_age,today
            from datetime import date
            child={'id':'<child UUID>','full_name':'Example child','module':'child','date_of_birth':'2020-01-01','profile_type':'member','doctor':None}
            age=child_age(CareProfile(dob=date(2020,1,1)))
            if path.endswith('/records'):result(op,{'items':[],'total':0,'page':1,'per_page':25})
            elif path.endswith('/reminders'):result(op,{'items':[],'total':0,'preferences':{'in_app':True},'message':'Recorded-date and published-schedule reminders. Schedule emails require explicit parent opt-in; SMS is not enabled.'})
            elif path.endswith('/reminder-preferences'):result(op,{'in_app':True})
            elif path=='/api/v1/children':result(op,{'items':[{**child,'age':age}],'total':1,'page':1,'per_page':25})
            elif path.endswith('/age'):result(op,{'age':age,'as_of_date':today().isoformat()})
            elif path.endswith('/health-guide'):result(op,{'status':'NOT_AVAILABLE','items':[],'message':'No medically reviewed health guide has been published for this child. Ask your doctor for guidance.'})
            elif '/vaccinations' in path:result(op,{'items':[],'total':0,'counts':dict.fromkeys(('COMPLETED','UPCOMING','DUE','OVERDUE','NOT_APPLICABLE','REVIEW_REQUIRED'),0),'status':'NOT_AVAILABLE','schedule_type':'UIP','context':{},'message':'No reviewed schedule has been published for this schedule type.'})
            elif re.fullmatch(r'/api/v1/children/\{child_id\}',path):result(op,{'child':{**child,'age':age}})
        if path.endswith('/report-text/options'):
            from services.report_text import LANGUAGES
            result(op,{'languages':[{'code':c,'name':n} for c,n in LANGUAGES.items()],'max_file_bytes':10485760,'max_pages':5,'target_language':'en','translation_provider':'MyMemory via deep-translator','translation_enabled':True,'max_translation_characters':4000,'ocr_engine':'PaddleOCR','configured':False})
        if path=='/api/v1/doctors/me':
            result(op,{'user':{'id':'<doctor UUID>','public_id':'D000001','full_name':'Example doctor','email':'doctor@example.com','role':'DOCTOR','approval_status':'APPROVED','account_status':'ACTIVE','email_verified':True,'must_change_password':False,'referral_id':'exampleD000001','doctor':{'qualification':'MBBS','medical_registration_number':'EXAMPLE-1','registering_council':'Example Council','specialization':'General Medicine','nmr_id':None,'verification_status':'APPROVED','address':'Example address','clinic_address':'Example clinic','years_of_experience':5,'images':{'profile_photo':{'name':'profile photo.png','url':'<signed private image URL valid for five minutes>'}}}},'notification_token':'<doctor-notification-purpose JWT>'})
        if path.startswith('/api/v1/auth/sessions/') and method=='delete':result(op,{'message':'Session revoked'})
        if model is AdultInput:
            op['requestBody']['content']['application/json']['example']={'kind':'history','title':'Example history','date':'2026-10-01','status':'Recorded','notes':'Existing condition recorded by the account owner'}
        if model is RecordInput:
            op['requestBody']['content']['application/json']['example']={'title':'Example diary entry','date':'2026-10-01','status':'Recorded','notes':'Account owner supplied record'}
            if method=='patch':
                # Handler merges a partial patch with the saved record before validation.
                partial=deepcopy(components['RecordInput']);partial.pop('required',None);partial['minProperties']=1
                partial['description']='Partial fields are merged with the existing record before validation.'
                op['requestBody']['content']['application/json']['schema']=partial
                op['requestBody']['content']['application/json']['example']={'notes':'Updated account owner notes'}
        # JSON examples are illustrative contracts; validation rules remain authoritative.
        op['x-example-kind']='synthetic-contract'
