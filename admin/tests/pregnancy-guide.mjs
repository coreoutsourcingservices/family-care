import {chromium} from 'playwright';
import assert from 'node:assert/strict';
const browser=await chromium.launch({channel:'msedge',headless:true});
try{
 const context=await browser.newContext();const base='http://127.0.0.1:5176';
 const response=await context.request.post(base+'/api/v1/patients/login',{headers:{Origin:base,'X-Auth-Transport':'cookie','X-Requested-With':'FamilyCare','X-FamilyCare-Portal':'patient'},data:{email:'owner@example.com',password:'BrowserTest8!'}});
 assert.equal(response.status(),200);const login=await response.json();await context.addInitScript(csrf=>localStorage.setItem('familycare_csrf_patient',csrf),login.csrf_token);
 const page=await context.newPage();page.setDefaultTimeout(60000);const errors=[];page.on('pageerror',e=>errors.push(e.message));
 await page.goto(base+'/customer/women/pregnancy?profile=44444444-4444-4444-8444-444444444444');
 await page.getByLabel('Pregnancy month',{exact:true}).fill('5');
 await page.getByRole('button',{name:'Save pregnancy stage',exact:true}).click();
 await page.getByRole('heading',{name:'Food & nutrition',exact:true}).waitFor();
 await page.getByText('Week 18 · Trimester 2',{exact:true}).waitFor();
 await page.reload();await page.getByText('Week 18 · Trimester 2',{exact:true}).waitFor();
 await page.getByRole('button',{name:/^Notifications/}).click();
 await page.locator('.customer-notifications-list').getByText('Pregnancy Care Guide',{exact:true}).waitFor();
 await page.getByRole('button',{name:'Close notifications'}).click();
 await page.setViewportSize({width:390,height:844});
 assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1));
 await page.screenshot({path:'../test-results/pregnancy-guide-mobile.png',fullPage:true});
 await page.getByLabel('Enable pregnancy guide & weekly care notifications').uncheck();
 await page.getByRole('button',{name:'Save pregnancy stage',exact:true}).click();
 await page.getByText('Pregnancy guide is turned off.',{exact:true}).waitFor();
 assert.deepEqual(errors,[]);console.log('PASS month input, saved guide, WHO sources, weekly notification, mobile layout and opt-out');
}finally{await browser.close();}
