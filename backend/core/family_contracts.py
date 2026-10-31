"""Synthetic examples for family invite onboarding; no secrets or real patient data."""
def enrich(paths):
    invite={'id':'<invitation UUID>','full_name':'Example Member','email':'member@example.com','module':'women',
        'relationship':'Family member','status':'PENDING','expires_at':'<UTC timestamp, 24 hours after creation>','profile_id':None}
    form={'full_name':'Example Member','email':'member@example.com','mobile_number':'+919876543211',
        'date_of_birth':'1995-02-28','password':'Choose-Your-Password8!','confirm_password':'Choose-Your-Password8!'}
    for path,methods in paths.items():
        if 'family-invitations' not in path:continue
        for method,op in methods.items():
            example=None;code=200;request=None
            if path=='/api/v1/patients/family-invitations':
                if method=='post':
                    request={k:invite[k] for k in ('full_name','email','module','relationship')}
                    example={'invitation':invite,'email_status':'sent'};code=201
                else:example={'items':[invite],'total':1,'page':1,'per_page':25}
            elif method=='delete':example={'message':'Invitation revoked'}
            elif path.endswith('/setup') or path.endswith('/resend-otp'):
                if path.endswith('/setup'):request=form
                example={'message':'Approval OTP sent to the inviting family email.','email_status':'sent',
                    'otp_destination':'inviting_family_email','expires_in':300,'resend_after':60};code=202
            elif path.endswith('/verify-otp'):
                request={'otp':'123456'};code=201
                example={'message':'Profile setup complete. Opening your profile.',
                    'access_token':'<member access JWT; omitted in cookie mode>',
                    'refresh_token':'<member refresh token; omitted in cookie mode>',
                    'expires_in':900,'token_type':'Bearer','redirect_url':'/customer/women/dashboard',
                    'user':{'id':'<member UUID>','public_id':'C000002','full_name':'Example Member',
                        'email':'member@example.com','phone_number':'+919876543211','role':'PATIENT','email_verified':True,
                        'approval_status':'APPROVED','account_status':'ACTIVE','must_change_password':False,'referred_doctor':None},
                    'profile':{'id':'<profile UUID>','profile_type':'member','module':'women','full_name':'Example Member',
                        'date_of_birth':'1995-02-28','member_email':'member@example.com','relationship':'Family member',
                        'linked_member':True,'parent_profile_id':None,'guardian_contact':'','guardian_name':'',
                        'emergency_contacts':[],'doctor':None,'created_at':'<UTC timestamp>'},
                    'family':{'full_name':'Example Family','relationship':'Family member'}}
            else:
                example={'invitation':invite,'family':{'full_name':'Example Family','email':'family@example.com'},
                    'form':{'full_name':invite['full_name'],'email':invite['email'],'readonly':['full_name','email']},
                    'otp_destination':'inviting_family_email','shared_profile':True}
            if request is not None:op['requestBody']['content']['application/json']['example']=request
            op['responses']={k:v for k,v in op['responses'].items() if not k.startswith('2')}
            op['responses'][str(code)]={'description':'Success','content':{'application/json':{'example':example}}}
            op['responses']['410']={'description':'Invitation expired, revoked or accepted','content':{'application/json':{'example':{'error':{'code':'invite_unavailable','message':'Invitation expired, revoked or already accepted'}}}}}
            if '{token}' in path:
                op['description']='Invitation secret authorizes this operation; no login session required. One-use link expires in 24 hours.'
                for param in op['parameters']:
                    if param['name']=='token':param['description']='Secret invitation token from the email link; not a UUID. Never log or publish it.'
