// Requires tests/admin_members_fixture.py on 5501 and a built Next server on 3006
// configured with BACKEND_URL=http://127.0.0.1:5501. Never uses live patient data.
import assert from 'node:assert/strict';
import {chromium} from 'playwright';
import {mkdir} from 'node:fs/promises';
const browser=await chromium.launch({channel:'chrome',headless:true});
try{
 const page=await browser.newPage({viewport:{width:1440,height:1000},reducedMotion:'reduce'});
 const errors=[];page.on('pageerror',e=>errors.push(e.message));
 await page.goto('http://localhost:3006');
 await page.locator('#identifier').fill('admin@example.com');
 await page.locator('#password').fill('SmokePassword8!');
 await page.getByRole('button',{name:'Sign in',exact:true}).click();
 await page.waitForURL('**/dashboard');
 await page.getByRole('link',{name:'Patients',exact:true}).click();
 await page.getByRole('link',{name:'Test Patient',exact:true}).waitFor();
 await page.getByText('3 members',{exact:true}).waitFor();
 await page.getByRole('link',{name:'Test Patient',exact:true}).click();
 await page.getByRole('heading',{name:'Patient & family.'}).waitFor();
 await page.getByRole('link',{name:'View profile Aarav Kumar',exact:true}).waitFor();
 assert.equal(await page.locator('tbody tr').count(),4);
 await page.getByLabel('Filter family profiles').selectOption('child');
 await page.getByRole('link',{name:'View profile Aarav Kumar',exact:true}).waitFor();
 assert.equal(await page.locator('tbody tr').count(),2);
 await page.getByRole('link',{name:'View profile Aarav Kumar',exact:true}).click();
 await page.getByRole('heading',{name:'Aarav Kumar',exact:true}).waitFor();
 await page.getByText('Family member',{exact:true}).waitFor();
 await page.getByText('Added by',{exact:false}).waitFor();
 await page.reload();await page.getByRole('heading',{name:'Aarav Kumar',exact:true}).waitFor();
 assert.equal(await page.getByRole('link',{name:'Patients',exact:true}).getAttribute('class'),'active');
 await page.getByRole('link',{name:'Back to family profiles',exact:true}).click();
 await page.getByRole('link',{name:'View profile Parent self',exact:true}).waitFor();
 await mkdir('.preview',{recursive:true});
 await page.screenshot({path:'.preview/patient-members-desktop.png',fullPage:true});
 await page.setViewportSize({width:390,height:844});
 await page.screenshot({path:'.preview/patient-members-mobile.png',fullPage:true});
 assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);
 // A fresh context verifies the superadmin portal uses the same family flow.
 const superPage=await browser.newPage();
 await superPage.goto('http://localhost:3006/superadmin');
 await superPage.locator('#identifier').fill('super@example.com');
 await superPage.locator('#password').fill('SmokePassword8!');
 await superPage.getByRole('button',{name:'Sign in',exact:true}).click();
 await superPage.waitForURL('**/superadmin/dashboard');
 await superPage.getByRole('link',{name:'Patients',exact:true}).click();
 await superPage.getByRole('link',{name:'Test Patient',exact:true}).click();
 await superPage.getByRole('link',{name:'View profile Anaya Kumar',exact:true}).click();
 await superPage.getByRole('heading',{name:'Anaya Kumar',exact:true}).waitFor();
 assert.ok(superPage.url().includes('/superadmin/patients/'));
 assert.deepEqual(errors,[]);
 console.log('PASS: admin and superadmin patient/member navigation, accurate counts, module filtering, member details, reload, nested navigation and mobile layout.');
}finally{await browser.close();}
