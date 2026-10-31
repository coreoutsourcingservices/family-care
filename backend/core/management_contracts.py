def enrich(paths):
    response={'counts':[{'role':'PATIENT','approval_status':'APPROVED','count':3}],
        'as_of':'2026-10-31','metrics':{k:{'total':v,'this_month':1} for k,v in [('administrators',2),('doctors',4),('patients',3),('children',5)]},
        'monthly_growth':[{'month':'2026-10','patients':3,'doctors':4,'administrators':2}],
        'recent_registrations':[{'id':'<UUID>','public_id':'C000001','full_name':'Example Patient','email':'patient@example.com','role':'PATIENT','approval_status':'APPROVED','account_status':'ACTIVE','created_at':'<UTC timestamp>'}],
        'pending_requests':{'total':0,'items':[]},'recent_activities':[{'id':'<UUID>','action':'registered','person':'Example Patient','created_at':'<UTC timestamp>'}],
        'child_care':{'total_children':5,'active_guides':4,'inactive_guides':1,'growth_records':2,'nutrition_records':3,'vaccination_records':4}}
    paths['/api/v1/superadmin/dashboard']['get']['responses']['200']={'description':'Organization aggregate summary. Monthly growth contains 12 calendar months; examples abbreviate the series. Counts remain backward compatible.','content':{'application/json':{'example':response}}}
    from copy import deepcopy
    admin_response=deepcopy(response)
    admin_response['approved_doctors']=3
    admin_response['metrics']['administrators']={'total':0,'this_month':0}
    paths['/api/v1/admin/dashboard']['get']['responses']['200']={'description':'Doctor/patient dashboard; pending requests contain doctors only.','content':{'application/json':{'example':admin_response}}}
    operation=paths['/api/v1/superadmin/search']['get']
    operation['parameters'].append({'name':'q','in':'query','schema':{'type':'string','maxLength':80},'description':'At least 2 characters. Literal case-insensitive name/email/public-ID search. Returns at most 8 accounts.'})
    operation['responses']['200']={'description':'Search matches','content':{'application/json':{'example':{'items':response['recent_registrations']}}}}
    paths['/api/v1/admin/search']['get']['parameters']=deepcopy(operation['parameters'])
    paths['/api/v1/admin/search']['get']['responses']['200']=deepcopy(operation['responses']['200'])
    for path,methods in paths.items():
        if path in ('/api/v1/admin/doctors','/api/v1/admin/patients','/api/v1/superadmin/admins','/api/v1/superadmin/doctors','/api/v1/superadmin/patients'):
            methods['get']['parameters'].append({'name':'search','in':'query','schema':{'type':'string','maxLength':80},'description':'Literal case-insensitive name/email/public-ID filter before pagination.'})
