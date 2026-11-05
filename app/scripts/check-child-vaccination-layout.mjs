import {chromium} from '@playwright/test';
import assert from 'node:assert/strict';
const browser=await chromium.launch({channel:'chrome',headless:true});
const base=process.env.VACCINE_TEST_URL||'http://127.0.0.1:5178';
const profile={id:'child-test',profile_type:'member',module:'child',full_name:'Aarav Sharma',date_of_birth:'2020-02-21',created_at:'2026-01-01',family_access:true};
const doctorRecord={id:'doctor-dose',kind:'vaccination',title:'BCG',date:'2020-02-21',status:'Completed',schedule_id:'schedule-0',source_role:'DOCTOR',author_name:'Dr. Ankit Sharma',notes:'Synthetic doctor vaccination note'};
const familyRecord={id:'family-dose',kind:'vaccination',title:'Family recorded vaccine',date:'2020-04-03',status:'Completed',source_role:'PATIENT',provider:'Dr. Family Clinic',author_name:'This must not appear'};
const schedule=[{id:'schedule-0',vaccine_id:'vaccine-0',vaccine:{name_en:'BCG'},dose_code:'birth',dose_name:'Birth',recommended_date:'2020-02-21',age_label:'At birth',status:'COMPLETED'}, {id:'schedule-1',vaccine_id:'vaccine-1',vaccine:{name_en:'Hepatitis B'},dose_code:'birth',dose_name:'Birth',recommended_date:'2020-02-21',age_label:'At birth',status:'OVERDUE'}, {id:'schedule-2',vaccine_id:'vaccine-2',vaccine:{name_en:'Pneumococcal conjugate vaccine with a longer name'},dose_code:'1',dose_name:'Dose 1',recommended_date:'2020-04-03',age_label:'6 Weeks',status:'REVIEW_REQUIRED',instructions:'Synthetic instructions only.'}];
try{for(const width of [320,390,440,1280,1366,1536,1920]){
 const page=await browser.newPage({viewport:{width,height:900},reducedMotion:'reduce'});let saved;
 await page.route('**/api/v1/**',async route=>{const url=new URL(route.request().url()),path=url.pathname;let data={items:[],total:0};
  if(path.endsWith('/patients/me'))data={user:{id:'family-test',role:'PATIENT',full_name:'Example Family',email:'family@example.com'}};
  else if(path.endsWith('/patients/profiles'))data={items:[profile],total:1};
  else if(path.endsWith('/patients/profiles/child-test'))data={profile};
  else if(path.endsWith('/vaccinations'))data={items:url.searchParams.get('schedule_type')==='UIP'?schedule:[],total:3};
  else if(path.endsWith('/vaccinations/history')&&route.request().method()==='POST'){saved=route.request().postDataJSON();data={record:{id:'saved-new',kind:'vaccination',...saved}};}
  else if(path.endsWith('/records')||path.endsWith('/vaccinations/history'))data={items:[doctorRecord,familyRecord],total:2};
  else if(path.endsWith('/vaccination-context'))data={context:{}};
  else if(path.endsWith('/age'))data={age:{display:'6 years'}};
  else if(path.endsWith('/reminders'))data={items:[],preferences:{in_app:true}};
  return route.fulfill({json:data});
 });
 const errors=[];page.on('pageerror',e=>errors.push(e.message));
 await page.goto(base+'/customer/child/vaccination');
 await page.locator('.cv-band').first().waitFor();await page.waitForTimeout(150);
 assert.equal(await page.locator('.cv-band[open]').count(),1,'DOB age range opens initially');
 assert.deepEqual(await page.locator('.cv-band>summary h2').allTextContents(),['0–1 year','1–3 years','3–5 years','5–12 years']);
 await page.locator('.cv-band').evaluateAll(groups=>groups.forEach(group=>{group.open=true;}));
 assert.equal(await page.locator('.cv-age[open]').count(),1,'Only the current age group opens initially');
 await page.locator('.cv-age').evaluateAll(groups=>groups.forEach(group=>{group.open=true;}));
 assert.equal(await page.locator('.cv-card').count(),4,'Linked doctor record should not duplicate its schedule');
 assert.equal(await page.locator('.cv-card .cv-doctor').count(),1,'Only actual doctor entries get a badge');
 assert.equal(await page.locator('.cv-card .cv-doctor').innerText(),'Added by Dr. Ankit Sharma');
 assert.equal(await page.locator('.cv-progress small').innerText(),'2 of 4 doses completed');
 const overflow=await page.evaluate(()=>[...document.querySelectorAll('.cv-page,.cv-page *')].filter(el=>{const r=el.getBoundingClientRect();return r.width>0&&r.height>0&&(r.left< -1||r.right>innerWidth+1);}).map(el=>({tag:el.tagName,cls:el.className})));
 assert.deepEqual(overflow,[],`Vaccination clipped at ${width}: ${JSON.stringify(overflow)}`);
 assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false,`Horizontal page scroll at ${width}`);
 if(width>=1024){
  const density=await page.evaluate(()=>({sidebar:document.querySelector('.ch-sidebar').getBoundingClientRect().width,header:document.querySelector('.ch-topbar').getBoundingClientRect().height,card:document.querySelector('.cv-card').getBoundingClientRect().height}));
  assert.equal(density.sidebar,190,'Desktop sidebar must use compact sizing at 100%');
  assert.equal(density.header,68,'Desktop header must use compact sizing at 100%');
  assert.ok(density.card<=165,`Desktop vaccine card is too tall: ${JSON.stringify(density)}`);
 }
 await page.getByRole('button',{name:'Completed (2)',exact:true}).click();assert.equal(await page.locator('.cv-card').count(),2);
 await page.getByRole('button',{name:'All (4)',exact:true}).click();
 await page.locator('.cv-card').filter({hasText:'BCG'}).getByRole('button',{name:'View notes',exact:true}).click();
 await page.getByRole('dialog').getByText('Synthetic doctor vaccination note',{exact:false}).waitFor();
 await page.getByRole('button',{name:'Close vaccination details',exact:true}).click();
 await page.getByRole('button',{name:'List view',exact:true}).click();
 assert.equal(await page.locator('.cv-list-view').count(),1);
 await page.getByRole('button',{name:'Grid view',exact:true}).click();
 await page.evaluate(()=>{document.activeElement?.blur();window.scrollTo(0,0);});
 assert.equal(await page.locator('.cv-heading').isVisible(),true,'Heading must be visible on mobile');
 await page.screenshot({path:`.preview/child-vaccination-${width}.png`,fullPage:true});
 await page.locator('.cv-card').filter({hasText:'Hepatitis B'}).getByRole('button',{name:'Record completed',exact:true}).click();
 await page.getByLabel('Administration date').fill('2026-10-20');
 await page.getByRole('button',{name:'Save completed dose',exact:true}).click();
 await page.waitForFunction(()=>!document.querySelector('.cv-dialog'));
 assert.equal(saved.schedule_id,'schedule-1');assert.equal(saved.status,'Completed');assert.equal(saved.date,'2026-10-20');assert.equal(saved.source_role,undefined,'Client must not impersonate a doctor');
 assert.deepEqual(errors,[]);await page.close();console.log(`${width}px: no overflow, attribution, counts, filters, notes and completion passed`);
}
for(const [dob,currentAge,expectedGroup] of [['2026-05-03','6 months','6 months'],['2025-07-03','1 year 4 months','1 year 4 months']]){
 const page=await browser.newPage({viewport:{width:390,height:844}});
 await page.clock.setFixedTime(new Date('2026-11-03T12:00:00+05:30'));
 const child={...profile,date_of_birth:dob};
 const dates=dob==='2026-05-03'?['2026-05-03','2026-11-03','2027-09-03']:['2025-07-03','2026-01-03','2026-11-03'];
 const plans=[0,6,16].map((months,index)=>({...schedule[0],id:'age-'+index,vaccine_id:'vaccine-age-'+index,recommended_date:dates[index],status:'UPCOMING',age_label:months===0?'At birth':months+' months',age_start:months,age_end:months,age_unit:'months'}));
 await page.route('**/api/v1/**',route=>{const url=new URL(route.request().url()),path=url.pathname;let data={items:[],total:0};
  if(path.endsWith('/patients/me'))data={user:{id:'family-test',role:'PATIENT',full_name:'Example Family'}};
  else if(path.endsWith('/patients/profiles'))data={items:[child],total:1};
  else if(path.endsWith('/vaccinations'))data={items:url.searchParams.get('schedule_type')==='UIP'?plans:[]};
  else if(path.endsWith('/vaccination-context'))data={context:{}};
  else if(path.endsWith('/reminders'))data={items:[],preferences:{in_app:true}};
  return route.fulfill({json:data});
 });
 await page.goto(base+'/customer/child/vaccination');
 await page.locator('.cv-age[open]').waitFor();
 assert.equal(await page.locator('.cv-child-age').innerText(),'Age: '+currentAge);
 assert.equal(await page.locator('.cv-age[open] h2').innerText(),expectedGroup);
 assert.equal(await page.locator('.cv-band[open]>summary h2').innerText(),currentAge==='6 months'?'0–1 year':'1–3 years');
 assert.equal(await page.locator('.cv-age[open]').count(),1);
 await page.locator('.cv-age[open]>summary').click();assert.equal(await page.locator('.cv-age[open]').count(),0);
 await page.locator('.cv-band').first().evaluate(group=>{group.open=true;});
 await page.locator('.cv-age').filter({has:page.getByRole('heading',{name:'At Birth',exact:true})}).locator('summary').click();
 assert.equal(await page.locator('.cv-age[open] h2').innerText(),'At Birth');
 console.log(`${currentAge}: DOB group opens first, other groups remain available`);await page.close();
}
}finally{await browser.close();}
