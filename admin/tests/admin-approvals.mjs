import {chromium} from 'playwright';
import assert from 'node:assert/strict';
const browser=await chromium.launch({channel:'msedge',headless:true});
try {
 const context=await browser.newContext({viewport:{width:1440,height:1000}});
 const login=await context.request.post('http://localhost:3006/api/v1/admin/login',{timeout:120000,headers:{Origin:'http://localhost:3006','X-Requested-With':'FamilyCare'},data:{email:'admin@example.com',password:'SmokePassword8!'}});
 assert.equal(login.status(),200);
 const page=await context.newPage();page.setDefaultTimeout(90000);page.setDefaultNavigationTimeout(120000);
 const errors=[];page.on('pageerror',e=>errors.push(e.message));
 await page.goto('http://localhost:3006/doctors?status=PENDING_APPROVAL');
 await page.waitForURL('**/approvals/doctors');
 await page.getByRole('button',{name:'Review request'}).first().click();
 await page.getByRole('button',{name:'Confirm approval',exact:true}).click();
 await page.getByRole('dialog').waitFor({state:'hidden'});
 await page.getByRole('status').filter({hasText:'approved.'}).waitFor();
 await page.goto('http://localhost:3006/doctors');
 assert.equal(await page.getByRole('combobox',{name:'Approval status'}).count(),0);
 await page.getByRole('link',{name:'Open profile →'}).first().click();
 await page.getByText('CARE NETWORK / DOCTOR DASHBOARD',{exact:true}).waitFor();
 assert.deepEqual(errors,[]);
 console.log('PASS admin separate approvals, legacy redirect, approve workflow and doctor profile navigation');
} finally {await browser.close();}
