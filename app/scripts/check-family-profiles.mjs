import { chromium, expect } from '@playwright/test';
import assert from 'node:assert/strict';
import { mkdir } from 'node:fs/promises';
const browser=await chromium.launch({headless:true});
const page=await browser.newPage({viewport:{width:1448,height:1086}});
const records=new Map(), errors=[],unexpected=[];let next=1;
page.on('pageerror',e=>errors.push(e.message));
await page.route('**/api/v1/**',async route=>{
 const req=route.request(),url=new URL(req.url()),path=url.pathname,method=req.method();
 const json=data=>route.fulfill({json:data});
 if(path==='/api/v1/patients/me')return json({user:{id:'account',role:'PATIENT',full_name:'Priyanshu Kishor',email:'person@example.com',phone_number:'+919876543210'}});
 if(path==='/api/v1/patients/profiles'){
  if(method==='GET')return json({items:[...records.values()].filter(p=>!url.searchParams.get('module')||p.module===url.searchParams.get('module')),total:records.size});
  const body=req.postDataJSON();assert.ok(body.full_name);assert.match(body.date_of_birth,/^\d{4}-\d{2}-\d{2}$/);assert.equal(body.member_email,undefined);
  for(const c of body.emergency_contacts)assert.equal(c.relationship,'Emergency contact');
  if(body.referral_id==='invalid')return route.fulfill({status:422,json:{error:{code:'invalid_referral',message:'Doctor referral not found'}}});
  const profile={...body,id:'profile-'+next++,created_at:new Date().toISOString(),doctor:body.referral_id?{referral_id:body.referral_id,full_name:'Dr Rahul Kumar'}:null};records.set(profile.id,profile);return json({profile});
 }
 const match=path.match(/^\/api\/v1\/patients\/profiles\/([^/]+)(\/reports)?$/);
 if(match){const profile=records.get(match[1]);assert.ok(profile);if(!match[2]){assert.equal(method,'GET');return json({profile});}
  if(method==='GET')return json({items:profile.reports??[],total:profile.reports?.length??0});
  assert.equal(method,'POST');const form=await new Request(req.url(),{method:'POST',body:req.postDataBuffer(),headers:{'content-type':req.headers()['content-type']}}).formData();const file=form.get('file');assert.ok(file);const report={id:'report-'+next++,name:file.name,size_bytes:file.size,created_at:new Date().toISOString()};profile.reports=[...(profile.reports??[]),report];return json({report});
 }
 unexpected.push(method+' '+path);return route.fulfill({status:404,json:{error:{message:'Unexpected API request'}}});
});
const save=()=>page.getByRole('button',{name:'Save & open profile',exact:true}).click();
const upload=()=>page.getByLabel('Add reports',{exact:true}).setInputFiles({name:'blood-test.pdf',mimeType:'application/pdf',buffer:Buffer.from('%PDF-1.4 test')});
try{
 await mkdir('artifacts',{recursive:true});
 await page.goto('http://127.0.0.1:5180/customer/child');
 await expect(page.locator('[name=memberName]')).toBeVisible();await page.screenshot({path:'artifacts/child-form.png',fullPage:true}); for(const [width,height] of [[1366,768],[1600,900],[1920,1080],[2560,1440]]){await page.setViewportSize({width,height});assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);await expect(page.getByRole('button',{name:'Save & open profile',exact:true})).toBeVisible();await page.screenshot({path:'artifacts/child-wide-'+width+'.png',fullPage:true});}await page.setViewportSize({width:1448,height:1086});
 await page.locator('[name=memberName]').fill('Aarav Kumar');await page.locator('[name=memberDob]').fill('2018-05-14');await page.locator('[name=guardianContact]').fill('9876543210');await upload();
 await page.getByText('Doctor',{exact:true}).click();await page.locator('[name=doctorReferralCode]').fill('invalid');await save();await expect(page.getByRole('alert')).toContainText('Doctor referral not found');
 await page.locator('[name=doctorReferralCode]').fill('rahulkumarD000001');await save();await expect(page.locator('.ch-child-identity strong')).toHaveText('Aarav Kumar');await page.getByRole('navigation',{name:'Child care navigation',exact:true}).getByRole('link',{name:'Doctor consultation',exact:true}).click();await expect(page.getByText('Dr Rahul Kumar',{exact:true})).toBeVisible();await page.getByRole('navigation',{name:'Child care navigation',exact:true}).getByRole('link',{name:'Health reports',exact:true}).click();await expect(page.getByRole('button',{name:/blood-test.pdf/})).toBeVisible();
 assert.equal([...records.values()][0].guardian_contact,'+919876543210');await page.reload();await expect(page.getByRole('button',{name:/blood-test.pdf/})).toBeVisible();
 await page.goto('http://127.0.0.1:5180/customer/women');await expect(page.locator('[name=memberName]')).toHaveValue('Priyanshu Kishor');await expect(page.locator('[name=memberName]')).toHaveAttribute('readonly','');await page.locator('[name=memberDob]').fill('1990-04-12');await page.screenshot({path:'artifacts/women-form.png',fullPage:true});await save();await expect(page.getByRole('heading',{name:'Priyanshu Kishor',exact:true})).toBeVisible();
 await page.goto('http://127.0.0.1:5180/customer/adult');await expect(page.getByRole('heading',{name:'Priyanshu Kishor',exact:true})).toBeVisible();assert.equal([...records.values()].filter(p=>p.profile_type==='self').length,1);
 await page.getByRole('button',{name:'Add member',exact:true}).click();await page.locator('[name=memberName]').fill('Adult Member');await page.locator('[name=memberDob]').fill('1980-01-01');for(let i=1;i<=3;i++){await page.getByRole('button',{name:'Add contact',exact:true}).click();await page.getByRole('textbox',{name:'Contact '+i+' name',exact:true}).fill('Contact '+i);await page.getByRole('textbox',{name:'Contact '+i+' mobile',exact:true}).fill('9876543210');}await expect(page.getByRole('button',{name:'Add contact',exact:true})).toBeDisabled();await page.screenshot({path:'artifacts/adult-form.png',fullPage:true});
 for(const width of [375,768,1366,1600,1920,2560]){await page.setViewportSize({width,height:900});assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false,'overflow at '+width);}
 await save();await expect(page.getByRole('heading',{name:'Adult Member',exact:true})).toBeVisible();await page.getByRole('button',{name:'Add reports',exact:true}).click();await expect(page.locator('[name=memberName]')).toHaveAttribute('readonly','');await upload();await save();await expect(page.getByRole('button',{name:/blood-test.pdf/})).toBeVisible();
 assert.deepEqual(unexpected,[]);assert.deepEqual(errors,[]);console.log('PASS canonical API requests, child referral validation/report upload/reload, Self autofill/reuse, adult contacts/report additions and responsive layouts.');
}finally{await browser.close();}
