// Start backend/tests/growth_nutrition_fixture.py and Vite first.
import {chromium} from 'playwright';
import assert from 'node:assert/strict';
const browser=await chromium.launch({channel:'msedge',headless:true});
try{
 const context=await browser.newContext();
 await context.route('**/api/**',async route=>{const url=new URL(route.request().url());url.port='5509';const response=await route.fetch({url:url.toString()});await route.fulfill({response});});
 const family=await context.newPage(),doctor=await context.newPage();const errors=[];
 family.on('pageerror',e=>errors.push(e.message));doctor.on('pageerror',e=>errors.push(e.message));
 async function login(page,role,email,password){await page.goto('http://127.0.0.1:5173/'+(role==='doctor'?'doctor':'customer')+'/login',{waitUntil:'domcontentloaded',timeout:60000});await page.evaluate(async({role,email,password})=>{const response=await fetch('/api/v1/'+(role==='doctor'?'doctors':'patients')+'/login',{method:'POST',credentials:'include',headers:{'Content-Type':'application/json','X-Auth-Transport':'cookie','X-Requested-With':'FamilyCare','X-FamilyCare-Portal':role},body:JSON.stringify({email,password})});const data=await response.json();if(!response.ok)throw Error(JSON.stringify(data));sessionStorage.setItem('familycare_csrf_'+role,data.csrf_token);},{role,email,password});}
 await login(family,'patient','family@example.com','FamilyPassword8!');
 const id='00000000-0000-4000-8000-000000000010';
 await family.goto('http://127.0.0.1:5173/customer/child/'+id+'/growth',{waitUntil:'domcontentloaded',timeout:60000});
 await family.getByRole('heading',{name:'Food guidance for 8–9 Months'}).waitFor();
 assert((await family.locator('.nutrition-age-guide').innerText()).includes('fully cooked eggs'));
 await family.screenshot({path:'test-results/growth-nutrition-active.png',fullPage:true});
 await login(doctor,'doctor','doctor@example.com','DoctorPassword8!');
 await doctor.goto('http://127.0.0.1:5173/doctor/child-care?patient='+id,{waitUntil:'domcontentloaded',timeout:60000});
 await doctor.getByRole('combobox',{name:'Child care section'}).selectOption('growth');
 await doctor.getByRole('button',{name:'Deactivate guide',exact:true}).click();
 await doctor.getByRole('button',{name:'Activate guide',exact:true}).waitFor();
 await family.reload({waitUntil:'domcontentloaded',timeout:60000});await family.getByText(/Your connected doctor has deactivated this guide/).waitFor();
 assert.equal(await family.getByRole('heading',{name:'Food guidance for 8–9 Months'}).count(),0);
 await doctor.getByRole('button',{name:'Activate guide',exact:true}).click();
 await doctor.getByRole('button',{name:'Deactivate guide',exact:true}).waitFor();
 await family.reload({waitUntil:'domcontentloaded',timeout:60000});await family.getByRole('heading',{name:'Food guidance for 8–9 Months'}).waitFor();
 assert.deepEqual(errors,[]);
 console.log('PASS age-selected child guide, doctor deactivation, parent hidden content and reactivation');
}finally{await browser.close();}
