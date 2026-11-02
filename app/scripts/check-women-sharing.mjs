// Run against tests/serve_women_workspace.py (5003) and the QA Vite proxy (5176).
import {chromium,expect} from '@playwright/test';
import assert from 'node:assert/strict';
const base=process.env.WOMEN_QA_URL??'http://127.0.0.1:5176';
const profile='44444444-4444-4444-8444-444444444444';
const member='22222222-2222-4222-8222-222222222222';
const doctor='33333333-3333-4333-8333-333333333333';
const browser=await chromium.launch({channel:'msedge',headless:true});
const errors=[];let lastPage;

async function session(email,portal='patient'){
 const context=await browser.newContext({viewport:{width:1440,height:960},reducedMotion:'reduce'});
 const response=await context.request.post(base+'/api/v1/'+(portal==='doctor'?'doctors':'patients')+'/login',{
  headers:{'X-Auth-Transport':'cookie','X-Requested-With':'FamilyCare','X-FamilyCare-Portal':portal,Origin:base},
  data:{email,password:'BrowserTest8!'}});
 assert.equal(response.status(),200,await response.text());
 const data=await response.json();
 await context.addInitScript(({csrf,portal})=>{if(!localStorage.getItem('familycare_csrf_'+portal))localStorage.setItem('familycare_csrf_'+portal,csrf);},{csrf:data.csrf_token,portal});
 const page=await context.newPage();page.setDefaultTimeout(90000);lastPage=page;page.on('pageerror',e=>errors.push(e.message));
 return {context,page,headers:{'X-Auth-Transport':'cookie','X-Requested-With':'FamilyCare','X-FamilyCare-Portal':portal,'X-CSRF-Token':data.csrf_token,Origin:base}};
}
try{
 const owner=await session('owner@example.com');
 const family=await session('family@example.com');
 const clinician=await session('doctor@example.com','doctor');
 const page=owner.page;lastPage=page;console.log('QA: login complete');
 const api=base+'/api/v1/women/profiles/'+profile;
 const current=await (await owner.context.request.get(api+'/workspace',{headers:owner.headers})).json();
 for(const record of current.records)await owner.context.request.delete(api+'/diary/'+record.id+'?version='+record.version,{headers:owner.headers});
 const existing=await (await owner.context.request.get(api+'/sharing',{headers:owner.headers})).json();
 for(const grant of existing.grants)await owner.context.request.delete(api+'/sharing/'+grant.id,{headers:owner.headers});
 await page.goto(base+'/customer/women/cycle?profile='+profile);
 await page.getByRole('button',{name:'Log period',exact:true}).click();
 await page.getByRole('dialog').getByLabel('Start date',{exact:true}).fill('2026-10-01');
 await page.getByRole('dialog').getByLabel('Title',{exact:true}).fill('Browser period entry');
 await page.getByRole('button',{name:'Save entry',exact:true}).click();
 await expect(page.getByRole('heading',{name:'Browser period entry',exact:true})).toBeVisible();
 await page.reload();
 await expect(page.getByRole('heading',{name:'Browser period entry',exact:true})).toBeVisible();
 await page.getByRole('link',{name:'Doctor consultation',exact:true}).first().click();console.log('QA: consultation navigation',page.url());
 const sharing=page.getByRole('region',{name:'Women tab sharing',exact:true});
 await sharing.getByLabel('Share with',{exact:true}).selectOption(member);console.log('QA: sharing selector ready');
 await sharing.getByRole('checkbox',{name:'Period & cycle',exact:true}).check();
 await sharing.getByRole('checkbox',{name:'Nutrition & lifestyle',exact:true}).check();
 await sharing.getByLabel('Nutrition & lifestyle permission',{exact:true}).selectOption('edit');
 await sharing.getByLabel('Access duration',{exact:true}).selectOption('7');
 await sharing.getByRole('button',{name:'Save access',exact:true}).click();
 await expect(sharing.getByRole('status')).toContainText('Access saved');
 await page.screenshot({path:'.preview/women-sharing-desktop.png',fullPage:true});
 await page.setViewportSize({width:390,height:844});
 assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false,'Owner mobile overflow');
 await page.screenshot({path:'.preview/women-sharing-mobile.png',fullPage:true});
 const shared=family.page;
 await shared.goto(base+'/customer/women/shared/'+profile);
 await shared.getByRole('button',{name:'Period & cycle · View',exact:true}).click();
 await expect(shared.getByRole('heading',{name:'Browser period entry',exact:true})).toBeVisible();
 assert.equal(await shared.getByRole('button',{name:'Log period',exact:true}).count(),0);
 assert.equal(await shared.getByRole('button',{name:'Edit',exact:true}).count(),0);
 assert.equal(await shared.getByRole('button',{name:/PCOS|Pregnancy|Medical records/}).count(),0);
 await shared.getByRole('button',{name:'Nutrition & lifestyle · View + Edit',exact:true}).click();
 await shared.getByRole('button',{name:'Add record',exact:true}).click();
 await shared.getByRole('dialog').getByLabel('Title',{exact:true}).fill('Family nutrition entry');
 await shared.getByRole('button',{name:'Save entry',exact:true}).click();
 await expect(shared.getByRole('heading',{name:'Family nutrition entry',exact:true})).toBeVisible();
 await shared.getByRole('button',{name:'Edit',exact:true}).click();
 await shared.getByRole('dialog').getByLabel('Title',{exact:true}).fill('Updated family nutrition');
 await shared.getByRole('button',{name:'Save entry',exact:true}).click();
 await expect(shared.getByRole('heading',{name:'Updated family nutrition',exact:true})).toBeVisible();
 await shared.setViewportSize({width:390,height:844});
 assert.equal(await shared.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false,'Recipient mobile overflow');
 await shared.screenshot({path:'.preview/women-sharing-recipient-mobile.png',fullPage:true});
 // The doctor gets an independent tab set and a custom expiry, through the same UI.
 await page.setViewportSize({width:1440,height:960});
 await sharing.getByLabel('Share with',{exact:true}).selectOption(doctor);
 await sharing.getByRole('checkbox',{name:'Pregnancy care',exact:true}).check();
 await sharing.getByLabel('Pregnancy care permission',{exact:true}).selectOption('edit');
 await sharing.getByLabel('Access duration',{exact:true}).selectOption('custom');
 const expires=new Date(Date.now()+3600000);const local=new Date(expires.getTime()-expires.getTimezoneOffset()*60000).toISOString().slice(0,16);
 await sharing.getByLabel('Expiry date & time',{exact:true}).fill(local);
 await sharing.getByRole('button',{name:'Save access',exact:true}).click();
 await expect(sharing.getByRole('status')).toContainText('Access saved');
 await clinician.page.goto(base+'/doctor/women/'+profile);
 await clinician.page.getByRole('button',{name:'Pregnancy care · View + Edit',exact:true}).click();
 await clinician.page.getByRole('button',{name:'Add record',exact:true}).click();
 await clinician.page.getByRole('dialog').getByLabel('Title',{exact:true}).fill('Doctor antenatal note');
 await clinician.page.getByRole('button',{name:'Save entry',exact:true}).click();
 await expect(clinician.page.getByRole('heading',{name:'Doctor antenatal note',exact:true})).toBeVisible();
 assert.equal(await clinician.page.getByRole('button',{name:'Period & cycle · View',exact:true}).count(),0);
 // Revoke family while the doctor grant stays active.
 const familyGrant=sharing.locator('article').filter({has:page.getByText('QA Family',{exact:true})});
 await familyGrant.getByRole('button',{name:'Revoke',exact:true}).click();
 await expect(sharing.getByRole('status')).toContainText('revoked');
 await shared.getByRole('button',{name:'Refresh',exact:true}).click();
 await expect(shared.getByRole('alert')).toContainText('expired or revoked');
 assert.equal(await shared.getByRole('heading',{name:'Updated family nutrition',exact:true}).count(),0);
 assert.deepEqual(errors,[]);
 console.log(JSON.stringify({passed:true,checks:['server persistence','per-tab selection','family view-only','family edit','doctor independent scope','custom expiry','revocation','desktop/mobile overflow','no page errors']}));
}catch(e){console.log(JSON.stringify({errors}));if(lastPage){console.log((await lastPage.locator('body').innerText()).slice(-4000));await lastPage.screenshot({path:'.preview/women-sharing-failure.png',fullPage:true});}throw e;}finally{await browser.close();}
