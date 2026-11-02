// Real HTTP/browser workflow against the isolated SQLite QA server and Vite proxy.
import {chromium,expect} from '@playwright/test';
import assert from 'node:assert/strict';
const base=process.env.WOMEN_QA_URL??'http://127.0.0.1:5176';
const id='44444444-4444-4444-8444-444444444444';
const api=base+'/api/v1/women/profiles/'+id;
const browser=await chromium.launch({channel:'msedge',headless:true});
const context=await browser.newContext({viewport:{width:1440,height:1000},reducedMotion:'reduce'});
const page=await context.newPage();page.setDefaultTimeout(60000);
const errors=[];page.on('pageerror',e=>errors.push(e.message));
const cases=[
 ['health','My health',{category:'Condition',notes:'Synthetic health note'}],
 ['cycle','Period & cycle',{end:'2026-10-05',flow:'Medium',symptoms:'Synthetic symptom',notes:'Cycle diary'}],
 ['pcos','PCOS & hormonal',{category:'Lab test',severity:'Mild',notes:'Synthetic clinician note'}],
 ['pregnancy','Pregnancy care',{category:'Antenatal visit',week:'12',due:'2027-05-01',notes:'Synthetic visit'}],
 ['fertility','Fertility & reproductive',{category:'Question for doctor',notes:'Synthetic question'}],
 ['symptoms','Symptoms & wellness',{severity:'Mild',notes:'Synthetic symptom context'}],
 ['nutrition','Nutrition & lifestyle',{category:'Meals',notes:'Synthetic meal diary'}],
 ['screening','Screening & preventive',{category:'Other screening',status:'Planned',next:'2026-12-01',notes:'Synthetic screening note'}],
 ['consultation','Doctor consultation',{doctor:'Dr QA',status:'Planned',notes:'Synthetic questions, no booking'}],
];
try{
 for(let attempt=0;attempt<30;attempt++){const health=await context.request.get(base+'/api/v1/health');if(health.ok())break;if(attempt===29)throw Error('QA API not ready');await new Promise(resolve=>setTimeout(resolve,1000));}
 const response=await context.request.post(base+'/api/v1/patients/login',{
  headers:{'X-Auth-Transport':'cookie','X-Requested-With':'FamilyCare','X-FamilyCare-Portal':'patient',Origin:base},
  data:{email:'owner@example.com',password:'BrowserTest8!'}});
 assert.equal(response.status(),200,await response.text());
 const login=await response.json();
 const headers={'X-Auth-Transport':'cookie','X-Requested-With':'FamilyCare','X-FamilyCare-Portal':'patient','X-CSRF-Token':login.csrf_token,Origin:base};
 await context.addInitScript(csrf=>{if(!localStorage.getItem('familycare_csrf_patient'))localStorage.setItem('familycare_csrf_patient',csrf);},login.csrf_token);
 const previous=await (await context.request.get(api+'/workspace',{headers})).json();
 for(const record of previous.records)await context.request.delete(api+'/diary/'+record.id+'?version='+record.version,{headers});
 await page.goto(base+'/customer/women/dashboard?profile='+id);
 for(const [section,label,fields] of cases){
  await page.locator('.ch-sidebar nav').getByRole('link',{name:label,exact:true}).click();
  await page.getByRole('button',{name:section==='cycle'?'Log period':'Add record',exact:true}).click();
  const modal=page.getByRole('dialog');
  await modal.locator('[name=date]').fill('2026-10-01');
  await modal.locator('[name=title]').fill('QA '+label);
  for(const [key,value] of Object.entries(fields)){
   const input=modal.locator('[name='+key+']');
   if(await input.evaluate(el=>el.tagName)==='SELECT')await input.selectOption(value);else await input.fill(value);
  }
  await modal.getByRole('button',{name:'Save entry',exact:true}).click();
  await expect(page.getByRole('heading',{name:'QA '+label,exact:true})).toBeVisible({timeout:30000});
  await page.reload();
  await expect(page.getByRole('heading',{name:'QA '+label,exact:true})).toBeVisible({timeout:30000});
  await page.getByRole('button',{name:'Edit',exact:true}).click();
  await page.getByRole('dialog').locator('[name=title]').fill('QA '+label+' edited');
  await page.getByRole('button',{name:'Save entry',exact:true}).click();
  await expect(page.getByRole('heading',{name:'QA '+label+' edited',exact:true})).toBeVisible({timeout:30000});
  await page.reload();
  await expect(page.getByRole('heading',{name:'QA '+label+' edited',exact:true})).toBeVisible({timeout:30000});
  const saved=await (await context.request.get(api+'/workspace',{headers})).json();
  const record=saved.records.find(r=>r.section===section&&r.title==='QA '+label+' edited');
  assert.ok(record,section+' persisted in backend');
  for(const [key,value] of Object.entries(fields))assert.equal(record[key],value,section+'.'+key);
  console.log('PASS '+label+': form → API → reload');
 }
 // A second period start drives the dashboard's real recorded interval chart.
 await page.locator('.ch-sidebar nav').getByRole('link',{name:'Period & cycle',exact:true}).click();
 await page.getByRole('button',{name:'Log period',exact:true}).click();
 await page.getByRole('dialog').locator('[name=date]').fill('2026-10-29');
 await page.getByRole('dialog').locator('[name=title]').fill('QA second period');
 await page.getByRole('button',{name:'Save entry',exact:true}).click();
 await expect(page.getByRole('heading',{name:'QA second period',exact:true})).toBeVisible({timeout:30000});
 await page.locator('.ch-sidebar nav').getByRole('link',{name:'Dashboard',exact:true}).click();
 await expect(page.getByText('28 days on average',{exact:true})).toBeVisible({timeout:30000});
 await expect(page.getByText('2 logged starts',{exact:true})).toBeVisible({timeout:30000});
 await expect(page.getByRole('img',{name:'My recorded cycle intervals in days'})).toBeVisible({timeout:30000});
 console.log('PASS Dashboard: server diary → cycle summary/chart');
 await page.locator('.ch-sidebar nav').getByRole('link',{name:'Medical records',exact:true}).click();
 const download=page.waitForEvent('download');
 await page.getByRole('button',{name:'QA-report.pdf',exact:true}).click();
 assert.equal((await download).suggestedFilename(),'QA-report.pdf');
 console.log('PASS Medical records: backend list → authenticated download');
 // A concurrent update must stay protected, visible inside the dialog, with the user's draft retained.
 await page.locator('.ch-sidebar nav').getByRole('link',{name:'My health',exact:true}).click();
 await page.getByRole('button',{name:'Edit',exact:true}).click();
 await page.getByRole('dialog').locator('[name=title]').fill('Unsaved local draft');
 const current=await (await context.request.get(api+'/workspace',{headers})).json();
 const health=current.records.find(r=>r.section==='health');
 const {id:recordId,version,section,...data}=health;
 headers['X-CSRF-Token']=await page.evaluate(()=>localStorage.getItem('familycare_csrf_patient'));
 const concurrent=await context.request.put(api+'/diary/'+recordId,{headers,data:{section,version:Number(version),data:{...data,title:'Concurrent update'}}});
 assert.equal(concurrent.status(),200);
 await page.getByRole('button',{name:'Save entry',exact:true}).click();
 await expect(page.getByRole('dialog').getByRole('alert')).toContainText('Your form has been kept');
 assert.equal(await page.getByRole('dialog').locator('[name=title]').inputValue(),'Unsaved local draft');
 await page.getByRole('button',{name:'Close form',exact:true}).click();
 await expect(page.getByRole('heading',{name:'Concurrent update',exact:true})).toBeVisible({timeout:30000});
 console.log('PASS Concurrent edit: visible conflict, draft retained, fresh record loaded');
 // Delete through each tab with foreign keys enabled, then confirm the server no longer returns it.
 for(const [section,label] of cases){
  await page.locator('.ch-sidebar nav').getByRole('link',{name:label,exact:true}).click();
  const title=section==='health'?'Concurrent update':'QA '+label+' edited';
  page.once('dialog',dialog=>dialog.accept());
  await page.getByRole('button',{name:'Delete '+title,exact:true}).click();
  await expect(page.getByRole('heading',{name:title,exact:true})).toHaveCount(0,{timeout:30000});
  const remaining=await (await context.request.get(api+'/workspace',{headers})).json();
  assert.ok(!remaining.records.some(r=>r.section===section&&r.title===title));
  console.log('PASS '+label+': delete ? backend');
 }
 assert.deepEqual(errors,[]);
 console.log(JSON.stringify({passed:true,diarySections:9,dashboard:true,reportsDownload:true,pageErrors:errors}));
}catch(e){console.log((await page.locator('body').innerText()).slice(-2500));throw e;}finally{await browser.close();}
