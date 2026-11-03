import {chromium,expect} from '@playwright/test';
import assert from 'node:assert/strict';
const browser=await chromium.launch({channel:'chrome',headless:true});
const page=await browser.newPage({viewport:{width:390,height:844},reducedMotion:'reduce'});
const errors=[];page.on('pageerror',error=>errors.push(error.message));
const id='11111111-1111-4111-8111-111111111111';
let member=false,invited,setup,permission,revoked=false,loginCount=0;
const profile={id,profile_type:'member',module:'adult',full_name:'Example Member',date_of_birth:'1995-02-28',created_at:'2026-01-01',emergency_contacts:[]};
const family={id:'owner',full_name:'Main Family',email:'family@example.com',role:'PATIENT'};
const own=()=>member?{id:'member',full_name:'Example Member',email:'member@example.com',role:'PATIENT',is_family_member:true,member_module:'adult',member_profile_id:id,redirect_url:'/customer/adult/dashboard?profile='+id}:family;
await page.route('**/api/v1/**',async route=>{
 const req=route.request(),path=new URL(req.url()).pathname.replace('/api/v1','');
 const json=(value,status=200)=>route.fulfill({json:value,status});
 if(path==='/patients/me')return json({user:own()});
 if(path==='/patients/login'){member=true;loginCount++;return json({user:own(),csrf_token:'synthetic-csrf',redirect_url:own().redirect_url});}
 if(path==='/patients/profiles')return json({items:[profile],total:1});
 if(path==='/patients/profiles/'+id)return json({profile});
 if(path==='/patients/family-invitations'){
  if(req.method()==='POST'){invited=req.postDataJSON();return json({invitation:{...invited,id:'invite',status:'PENDING'},email_status:'sent'},201);}
  return json({items:invited?[{...invited,id:'invite',status:'PENDING'}]:[],total:invited?1:0});
 }
 if(path==='/family-invitations/synthetic-token')return json({invitation:{full_name:'Example Member',email:'member@example.com',module:'adult'},family});
 if(path.endsWith('/setup')){setup=req.postDataJSON();return json({email_status:'sent',otp_destination:'member_email'},202);}
 if(path.endsWith('/verify-otp')){assert.equal(req.postDataJSON().otp,'123456');member=true;return json({user:own(),csrf_token:'synthetic-csrf',redirect_url:own().redirect_url},201);}
 if(path.endsWith('/doctor-access')){
  if(req.method()==='PUT'){permission=req.postDataJSON();return json({access:{...permission,active:true}});}
  if(req.method()==='DELETE'){revoked=true;return json({message:'Revoked'});}
  return json({access:permission?{...permission,active:true}:null});
 }
 if(path.endsWith('/reports'))return json({items:[{id:'report-one',name:'Selected lab.pdf',created_at:'2026-01-01',category:'Lab tests'}],total:1});
 if(path.endsWith('/records'))return json({items:[],total:0});
 if(path.startsWith('/notifications'))return json({items:[],total:0,unread_count:0});
 return json({items:[],total:0});
});
try{
 await page.goto('http://127.0.0.1:5173/customer/dashboard');
 await expect(page.locator('.customer-family-hero')).toBeVisible();
 await expect(page.locator('.family-invite-page')).toHaveCount(0);
 await page.goto('http://127.0.0.1:5173/customer/adult?add=1');
 await page.getByLabel('Member name',{exact:true}).fill('Example Member');
 await page.getByLabel('Member email',{exact:true}).fill('member@example.com');
 await page.getByLabel('Relationship',{exact:true}).fill('Cousin');
 await page.getByRole('button',{name:'Send email invitation',exact:true}).click();
 await expect(page.getByRole('status').filter({hasText:'Invitation sent'})).toBeVisible();
 assert.equal(invited.module,'adult');assert.equal(invited.email,'member@example.com');
 await page.setViewportSize({width:1366,height:900});
 await page.goto('http://127.0.0.1:5173/customer/women?add=1');
 await expect(page.getByRole('heading',{name:"Invite to Women's Health",exact:true})).toBeVisible();
 await page.screenshot({path:'.preview/women-invite-redesign-desktop.png',fullPage:true});
 await page.setViewportSize({width:390,height:844});
 assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);
 await page.screenshot({path:'.preview/women-invite-redesign-mobile.png',fullPage:true});
 await page.goto('http://127.0.0.1:5173/customer/family-invite#token=synthetic-token');
 await page.getByLabel('Your mobile number',{exact:true}).fill('+919876543211');
 await page.getByLabel('Date of birth',{exact:true}).fill('1995-02-28');
 await page.getByLabel('Create your password',{exact:true}).fill('SyntheticPassword8!');
 await page.getByLabel('Confirm password',{exact:true}).fill('SyntheticPassword8!');
 await page.getByRole('checkbox').check();
 await page.getByRole('button',{name:'Send verification OTP',exact:true}).click();
 await expect(page.getByText('The OTP was sent to',{exact:false})).toContainText('member@example.com');
 assert.equal(setup.email,'member@example.com');
 await page.getByLabel('Verification OTP',{exact:true}).fill('123456');
 await page.getByRole('button',{name:'Verify and open my profile',exact:true}).click();
 await expect(page).toHaveURL(/customer\/adult\/dashboard/);
 await expect(page.getByRole('link',{name:'Add member',exact:true})).not.toBeVisible();
 await page.goto('http://127.0.0.1:5173/customer/child/dashboard');
 await expect(page).toHaveURL(/customer\/adult\/dashboard/);
 await page.goto('http://127.0.0.1:5173/customer/login');
 await page.locator('input[type=email]').fill('member@example.com');
 await page.locator('input[type=password]').fill('SyntheticPassword8!');
 await page.locator('form button[type=submit]').click();
 await expect(page).toHaveURL(/customer\/adult\/dashboard/);assert.equal(loginCount,1);
 await page.goto('http://127.0.0.1:5173/customer/adult/settings');
 await page.getByLabel('Doctor referral ID',{exact:true}).fill('exampleD000001');
 await page.getByLabel('All reports, including future uploads',{exact:true}).uncheck();
 await page.getByLabel('Selected lab.pdf',{exact:true}).check();
 await page.getByRole('button',{name:'Save doctor permission',exact:true}).click();
 await expect(page.getByRole('status').filter({hasText:'Permission saved'})).toBeVisible();
 assert.deepEqual(permission.report_ids,['report-one']);assert.deepEqual(permission.scopes,['reports']);assert(new Date(permission.expires_at)>new Date());
 const overflow=await page.evaluate(()=>({width:innerWidth,scroll:document.documentElement.scrollWidth,items:[...document.querySelectorAll('main *')].filter(e=>{const r=e.getBoundingClientRect();return r.width&&r.right>innerWidth+1&&getComputedStyle(e).position!=='fixed';}).slice(0,12).map(e=>({tag:e.tagName,class:e.className,width:e.getBoundingClientRect().width}))}));if(overflow.scroll>overflow.width)console.log('OVERFLOW',JSON.stringify(overflow));assert.equal(overflow.scroll>overflow.width,false);
 await page.screenshot({path:'.preview/member-doctor-permissions-mobile.png',fullPage:true});
 await page.getByRole('button',{name:'Revoke doctor access',exact:true}).click();
 await expect(page.getByRole('status').filter({hasText:'revoked immediately'})).toBeVisible();assert(revoked);
 assert.deepEqual(errors,[]);
 console.log('PASS mocked browser: invite before adult add, member email OTP setup, independent direct member login, child-route denial, scoped expiring doctor permission and revoke; mobile fits. No SMTP email sent.');
}finally{await browser.close();}
