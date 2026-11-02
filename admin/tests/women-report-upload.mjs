import {chromium} from 'playwright';
import assert from 'node:assert/strict';
const browser=await chromium.launch({channel:'msedge',headless:true});
try{
 const context=await browser.newContext();const base='http://127.0.0.1:5176';
 const response=await context.request.post(base+'/api/v1/patients/login',{headers:{Origin:base,'X-Auth-Transport':'cookie','X-Requested-With':'FamilyCare','X-FamilyCare-Portal':'patient'},data:{email:'owner@example.com',password:'BrowserTest8!'}});
 assert.equal(response.status(),200);const login=await response.json();await context.addInitScript(csrf=>localStorage.setItem('familycare_csrf_patient',csrf),login.csrf_token);
 const page=await context.newPage();page.setDefaultTimeout(60000);const errors=[];page.on('pageerror',e=>errors.push(e.message));
 const filename='synthetic-'+Date.now()+'.pdf';
 const profile='44444444-4444-4444-8444-444444444444';
 for(const section of ['health','cycle','pcos','pregnancy','fertility','symptoms','nutrition','screening','records','consultation','settings','planner']){
  await page.goto(`${base}/customer/women/${section}?profile=${profile}`);
  await page.locator('.wh-header-title').waitFor();
  if(section==='records')await page.getByRole('heading',{name:'Upload & read medical report',exact:true}).waitFor();
  else assert.equal(await page.getByLabel('Upload medical reports').count(),0);
 }
 await page.goto(`${base}/customer/women/records?profile=${profile}`);
 await page.getByRole('heading',{name:'Upload & read medical report',exact:true}).waitFor();
 await page.screenshot({path:'../test-results/women-records-desktop.png',fullPage:true});
 await page.setViewportSize({width:390,height:844});
 assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1));
 await page.screenshot({path:'../test-results/women-records-mobile.png',fullPage:true});
 await page.getByLabel('Upload medical reports').setInputFiles({name:filename,mimeType:'application/pdf',buffer:Buffer.from('%PDF-1.7 synthetic QA')});
 await page.getByText('SYNTHETIC REPORT\nHemoglobin: 12.5 g/dL',{exact:true}).waitFor();
 await page.goto(`${base}/customer/women/records?profile=${profile}`);
 await page.getByRole('button',{name:filename,exact:true}).waitFor();
 await page.getByRole('button',{name:filename,exact:true}).locator('..').getByRole('button',{name:'Read report / Extract text',exact:true}).click();
 await page.getByText('SYNTHETIC REPORT\nHemoglobin: 12.5 g/dL',{exact:true}).waitFor();
 assert.deepEqual(errors,[]);console.log('PASS upload only in Medical records, responsive layout, queued OCR text and persistence');
}finally{await browser.close();}
