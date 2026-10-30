import {chromium} from 'playwright';
import assert from 'node:assert/strict';
import {mkdir} from 'node:fs/promises';
const browser=await chromium.launch({channel:'chrome',headless:true});
const errors=[];let writes=[];
const states=['COMPLETED','UPCOMING','OVERDUE','REVIEW_REQUIRED','NOT_APPLICABLE'];
const doses=states.map((status,i)=>({id:'dose-'+i,vaccine:{name_en:'Synthetic '+i},dose_name:'Test dose',age_label:'1-3 years',age_group:'1-3',age_relation:'CURRENT',recommended_date:'2026-11-06',window_end:'2026-11-07',status,reasons:[],version:'test',schedule_type:'UIP'}));
try{
 const page=await browser.newPage({viewport:{width:1440,height:1000}});page.on('pageerror',e=>errors.push(e.message));
 await page.route('**/api/v1/**',route=>{const req=route.request(),path=new URL(req.url()).pathname;let json={items:[],total:0};if(req.method()!=='GET')writes.push({path,body:req.postDataJSON()});
  if(path.startsWith('/api/v1/children/'))assert.equal(req.headers()['x-familycare-portal'],'patient');
  if(path.endsWith('/me'))json={user:{id:'test-owner',role:'PATIENT'}};
  else if(path.endsWith('/patients/profiles'))json={items:[{id:'test-child',module:'child',full_name:'Synthetic child',date_of_birth:'2024-01-01',profile_type:'member'}],total:1};
  else if(path.endsWith('/vaccinations'))json={items:new URL(req.url()).searchParams.get('schedule_type')==='IAP'?[]:doses,total_published:5,child:{age:{completed_years:2}}};
  else if(path.endsWith('/vaccination-context'))json={context:{country:'IN',history_status:'UNKNOWN'}};
  else if(path.endsWith('/dashboard'))json={child:{age:{display:'2 years'}},counts:{},vaccination:{status:'AVAILABLE',message:'Synthetic test'}};
  else if(path.endsWith('/age'))json={age:{display:'2 years'}};
  else if(path.endsWith('/reminders'))json={items:[{id:'reminder',kind:'vaccination',title:'Synthetic upcoming dose',date:'2026-11-06',message:'Vaccination is due in 7 days.',status:'UPCOMING'}],preferences:{in_app:true}};
  return route.fulfill({json});});
 await page.goto('http://127.0.0.1:5174/customer/child/vaccination');
 await page.locator('.child-vaccine-rows article').first().waitFor();assert.equal(await page.locator('.child-vaccine-rows article:visible').count(),5);
 for(const status of ['COMPLETED','UPCOMING','OVERDUE','REVIEW_REQUIRED','NOT_APPLICABLE']){await page.getByLabel('Vaccination status',{exact:true}).selectOption(status);assert.equal(await page.locator('.child-vaccine-rows article:visible').count(),1);}
 await page.getByLabel('Vaccination status',{exact:true}).selectOption('All');
 const clinicalWrites=()=>writes.filter(w=>w.path.includes('/children/'));const beforeRead=clinicalWrites().length;await page.getByRole('checkbox',{name:'Mark as read: Synthetic 0 / Test dose',exact:true}).check();assert.equal(clinicalWrites().length,beforeRead);
 await page.getByText("Vaccination information & reminder preferences",{exact:true}).click();
 await page.getByLabel('I have entered the previous vaccination records available to me.').check();
 await page.getByRole('button',{name:'Save vaccination information',exact:true}).click();await page.getByText('Saved. Vaccination statuses refreshed.',{exact:true}).waitFor();const contextWrite=writes.find(w=>w.path.endsWith('/vaccination-context'));assert.equal(contextWrite.body.history_status,'PARENT_REPORTED');assert.equal(contextWrite.body.email_reminders,false);
 await mkdir('test-results',{recursive:true});await page.screenshot({path:'test-results/vaccination-five-statuses.png',fullPage:true});
 await page.setViewportSize({width:390,height:844});assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));await page.screenshot({path:'test-results/vaccination-five-statuses-mobile.png',fullPage:true});
 console.log('PASS five status filters, read-only checkbox, explicit history consent, mobile width');
 const doc=await browser.newPage({viewport:{width:1440,height:1000}});doc.on('pageerror',e=>errors.push(e.message));let imported=false;
 const draft={...doses[0],id:'draft',created_by:'doctor-test',status:'DRAFT',schedule_type:'IAP',instructions:'Synthetic source review only',source_url:'https://example.org',source_reference:'Test reference',reminders:{before_days:[7,1],overdue_days:[1,7]},age_unit:'months',age_start:6,age_end:6};
 await doc.route('**/api/v1/**',route=>{const req=route.request(),path=new URL(req.url()).pathname;let json={items:[],total:0};
  if(path.startsWith('/api/v1/doctors/'))assert.equal(req.headers()['x-familycare-portal'],'doctor');
  if(path.endsWith('/doctors/me'))json={user:{id:'doctor-test',role:'DOCTOR',full_name:'Synthetic doctor',approval_status:'APPROVED'}};
  else if(path.endsWith('/import-iap')){imported=true;json={message:'Drafts saved for review'};}
  else if(path.endsWith('/vaccination/schedules'))json={items:imported?[draft]:[],total:imported?1:0};
  else if(path.endsWith('/vaccination/reviewers'))json={items:[{id:'other-doctor',name:'Independent reviewer',qualification:'MD'}]};
  else if(path.endsWith('/care-profiles'))json={items:[{id:'child',full_name:'Synthetic child',module:'child'}],total:1};
  else if(path.endsWith('/vaccination-plan'))json=req.method()==='GET'?{UIP:{items:[{...doses[3],display_status:'Doctor Review'}],message:'Published synthetic dose'},IAP:{items:[],message:'Drafts awaiting publication'}}:{message:'Child-specific applicability saved'};
  else if(req.method()!=='GET')json={message:'Saved synthetic draft'};
  return route.fulfill({json});});
 await doc.goto('http://127.0.0.1:5175/doctor/vaccination');await doc.getByRole('button',{name:'Add IAP starter schedule',exact:true}).click();await doc.getByText('Drafts saved for review',{exact:true}).waitFor();
 await doc.getByLabel('Independent reviewing doctor').selectOption('other-doctor');await doc.getByRole('button',{name:'Request independent review',exact:true}).click();await doc.getByText('Saved synthetic draft',{exact:true}).waitFor();
 await doc.getByLabel('Child',{exact:true}).selectOption('child');await doc.getByLabel('Published dose').selectOption('dose-3');await doc.getByLabel('Clinical notes').fill('Synthetic clinical review notes for testing only.');await doc.getByLabel("I reviewed the child's history, eligibility, product and dose intervals.").check();await doc.getByRole('button',{name:'Save child review',exact:true}).click();await doc.getByText('Child-specific applicability saved',{exact:true}).waitFor();await doc.screenshot({path:'test-results/vaccination-doctor-starters.png',fullPage:true});
 assert.deepEqual(errors,[]);console.log('PASS doctor import, independent reviewer selection and connected-child review UI; no runtime errors');
}finally{await browser.close();}
