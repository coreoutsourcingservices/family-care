import {chromium} from 'playwright';
import assert from 'node:assert/strict';
const browser=await chromium.launch({channel:'msedge',headless:true});
try {
 for(const [module,email,profile] of [['women','owner@example.com','44444444-4444-4444-8444-444444444444'],['adult','owner@example.com','66666666-6666-4666-8666-666666666666']]){
  const context=await browser.newContext();
  const response=await context.request.post('http://127.0.0.1:5176/api/v1/patients/login',{headers:{Origin:'http://127.0.0.1:5176','X-Auth-Transport':'cookie','X-Requested-With':'FamilyCare','X-FamilyCare-Portal':'patient'},data:{email,password:'BrowserTest8!'}});
  assert.equal(response.status(),200);const login=await response.json();
  await context.addInitScript(csrf=>localStorage.setItem('familycare_csrf_patient',csrf),login.csrf_token);
  const page=await context.newPage();page.setDefaultTimeout(60000);const errors=[];page.on('pageerror',e=>errors.push(e.message));
  await page.goto(`http://127.0.0.1:5176/customer/${module}/planner?profile=${profile}`);
  await page.getByRole('heading',{name:'Notes & tasks',exact:true}).waitFor();
  await page.getByRole('button',{name:'Add note',exact:true}).click();
  await page.getByLabel('Title',{exact:true}).fill('Private QA note');
  await page.locator('.profile-planner textarea').fill('Synthetic note only');
  await page.getByRole('button',{name:'Save note',exact:true}).click();
  await page.getByRole('heading',{name:'Private QA note'}).waitFor();
  await page.getByRole('button',{name:/^Notifications/}).click();
  await page.getByRole('button',{name:'Enable alarm sound',exact:true}).click();
  await page.getByRole('button',{name:'Close notifications'}).click();
  await page.getByRole('button',{name:'Add task',exact:true}).click();
  await page.getByLabel('Title',{exact:true}).fill('Timed QA task');
  const date=new Date(Date.now()-60000);const local=new Date(date.getTime()-date.getTimezoneOffset()*60000).toISOString().slice(0,16);
  await page.getByLabel('Task date & time').fill(local);
  await page.getByRole('button',{name:'Save task',exact:true}).click();
  await page.getByRole('heading',{name:'Timed QA task'}).waitFor();
  await page.getByRole('button',{name:/^Notifications/}).click();
  await page.getByRole('button',{name:'Stop alarm',exact:true}).waitFor();
  await page.getByRole('button',{name:'Stop alarm',exact:true}).click();
  await page.getByRole('button',{name:'Close notifications'}).click();
  await page.getByRole('button',{name:'Mark complete',exact:true}).click();
  await page.getByRole('button',{name:'Reopen task',exact:true}).waitFor();
  await page.reload();await page.getByRole('button',{name:'Reopen task',exact:true}).waitFor();
  await page.getByRole('button',{name:/^Notifications/}).click();
  await page.getByText('Task completed',{exact:true}).first().waitFor();
  assert.deepEqual(errors,[]);console.log('PASS '+module+' note, task, alarm controls, completion notification and persistence');
  await context.close();
 }
}finally{await browser.close();}
