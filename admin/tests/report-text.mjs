import assert from 'node:assert/strict';
import {chromium} from 'playwright';
import {mkdir} from 'node:fs/promises';
const browser=await chromium.launch({channel:'chrome',headless:true});
try{
 const page=await browser.newPage({viewport:{width:1440,height:1000}}),errors=[];page.on('pageerror',e=>errors.push(e.message));
 await page.goto('http://127.0.0.1:5175/customer/login');await page.locator('input[name=email]').fill('patient@example.com');await page.locator('input[name=password]').fill('SmokePassword8!');await page.getByRole('button',{name:'Login',exact:true}).click();await page.waitForURL('**/customer/dashboard');await page.goto('http://127.0.0.1:5175/customer/child/reports');
 await page.getByRole('button',{name:'Extract text / Translate to English',exact:true}).click();await page.getByLabel('Document language for Synthetic report.pdf',{exact:true}).selectOption('hi');
 const consent=page.getByRole('checkbox');assert.equal(await consent.isChecked(),false);
 const queued=page.waitForRequest(r=>r.url().endsWith('/text')&&r.method()==='POST');await page.getByRole('button',{name:'Extract text',exact:true}).click();const payload=(await queued).postDataJSON();assert.equal(payload.translate_to_english,false);assert.equal(payload.external_translation_consent,false);
 await page.locator('pre').filter({hasText:'\u092a\u0930\u0940\u0915\u094d\u0937\u0923'}).waitFor();await consent.check();await page.getByRole('button',{name:'Extract again',exact:true}).click();await page.locator('pre').filter({hasText:'Synthetic test report'}).waitFor();
 await page.reload();await page.getByRole('button',{name:'Extract text / Translate to English',exact:true}).click();await page.locator('pre').filter({hasText:'Synthetic test report'}).waitFor();assert.equal(await page.getByRole('checkbox').isChecked(),false);
 await mkdir('test-results',{recursive:true});await page.screenshot({path:'test-results/report-text.png',fullPage:true});await page.setViewportSize({width:390,height:844});await page.screenshot({path:'test-results/report-text-mobile.png',fullPage:true});assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=document.documentElement.clientWidth+1));assert.deepEqual(errors,[]);console.log('PASS report OCR request, explicit translation consent, original/English result, persisted reload and mobile width');
}finally{await browser.close();}
