// Isolated admin_members_fixture.py (5501) and a built Next server (3006).
// Uses one browser context to reproduce cookies shared by frontend/admin ports.
import assert from 'node:assert/strict';
import {chromium} from 'playwright';
const base='http://127.0.0.1:3006';
const browser=await chromium.launch({channel:'chrome',headless:true});
try{
 const context=await browser.newContext();
 const shared=(value)=>[{name:'fc_access',value,domain:'127.0.0.1',path:'/'},{name:'fc_refresh',value:value+'-refresh',domain:'127.0.0.1',path:'/api/v1/auth'}];
 await context.addCookies(shared('patient-session-one'));
 const admin=await context.newPage(),superadmin=await context.newPage();
 async function login(page,role){await page.goto(base+(role==='superadmin'?'/superadmin':'/'));await page.locator('#identifier').fill(role==='superadmin'?'super@example.com':'admin@example.com');await page.locator('#password').fill('SmokePassword8!');await page.getByRole('button',{name:'Sign in',exact:true}).click();await page.waitForURL(role==='superadmin'?'**/superadmin/dashboard':'**/dashboard');}
 async function api(page,path,portal,method='GET',origin=base){return page.evaluate(async({path,portal,method,origin})=>{const r=await fetch('/api/v1/'+path,{method,headers:{'Content-Type':'application/json','X-Requested-With':'FamilyCare','X-FamilyCare-Portal':portal},body:method==='POST'?'{}':undefined});return {status:r.status,data:await r.json()};},{path,portal,method,origin});}
 await login(admin,'admin');await admin.goto(base+'/patients');await admin.getByText('3 members',{exact:true}).waitFor();
 await login(superadmin,'superadmin');await superadmin.goto(base+'/superadmin/patients');await superadmin.getByText('3 members',{exact:true}).waitFor();
 await context.addCookies(shared('patient-session-two'));
 assert.equal((await api(admin,'admin/patients','admin')).status,200);
 assert.equal((await api(superadmin,'superadmin/patients','superadmin')).status,200);
 let cookies=await context.cookies();
 for(const name of ['fc_admin_access','fc_admin_refresh','fc_admin_csrf','fc_superadmin_access','fc_superadmin_refresh','fc_superadmin_csrf'])assert.ok(cookies.some(c=>c.name===name&&c.httpOnly),name);
 assert.equal(cookies.find(c=>c.name==='fc_access').value,'patient-session-two');
 assert.equal((await api(admin,'auth/refresh','admin','POST')).status,200);
 assert.equal((await api(superadmin,'auth/refresh','superadmin','POST')).status,200);
 await admin.reload();await admin.getByText('3 members',{exact:true}).waitFor();
 assert.equal((await api(admin,'auth/logout','admin','POST')).status,200);
 assert.equal((await api(superadmin,'superadmin/patients','superadmin')).status,200);
 cookies=await context.cookies();assert.ok(!cookies.some(c=>c.name==='fc_admin_access'));assert.equal(cookies.find(c=>c.name==='fc_access').value,'patient-session-two');
 // Reproduce a stale panel with a wrong-role access cookie: keep role checks strict.
 const superToken=cookies.find(c=>c.name==='fc_superadmin_access').value;
 await context.addCookies([{name:'fc_admin_access',value:superToken,domain:'127.0.0.1',path:'/',httpOnly:true}]);
 await admin.getByRole('button',{name:'Refresh',exact:true}).click();
 await admin.waitForURL('**/?session=changed');
 await admin.getByRole('status').filter({hasText:'Your session has changed'}).waitFor();
 await login(admin,'admin');await admin.goto(base+'/patients');await admin.getByText('3 members',{exact:true}).waitFor();
 // An expired access cookie should rotate only the admin refresh session.
 await context.addCookies([{name:'fc_admin_access',value:'expired-token',domain:'127.0.0.1',path:'/',httpOnly:true}]);
 await admin.getByRole('button',{name:'Refresh',exact:true}).click();await admin.getByText('3 members',{exact:true}).waitFor();
 assert.equal(new URL(admin.url()).pathname,'/patients');
 assert.equal((await api(superadmin,'superadmin/patients','superadmin')).status,200);
 // API failure must never be presented as an empty patient directory.
 await admin.route('**/api/v1/admin/patients?*',route=>route.fulfill({status:503,json:{error:{code:'database_unavailable',message:'Test API temporarily unavailable'}}}));
 await admin.getByRole('button',{name:'Refresh',exact:true}).click();
 await admin.getByRole('alert').filter({hasText:'Test API temporarily unavailable'}).waitFor();
 assert.equal(await admin.getByRole('heading',{name:'No accounts here yet',exact:true}).count(),0);
 await admin.getByText('Unable to load accounts. Please refresh or sign in again.',{exact:true}).waitFor();
 await admin.unroute('**/api/v1/admin/patients?*');await admin.getByRole('button',{name:'Refresh',exact:true}).click();await admin.getByText('3 members',{exact:true}).waitFor();
 const cross=await context.request.post(base+'/api/v1/admin/login',{headers:{Origin:'https://untrusted.example','X-Requested-With':'FamilyCare'},data:{}});assert.equal(cross.status(),403);
 console.log('PASS: loopback login, frontend/admin/superadmin cookie isolation, HttpOnly cookies, independent refresh/logout, stale-role recovery, access refresh, truthful error state and cross-origin rejection.');
}finally{await browser.close();}
