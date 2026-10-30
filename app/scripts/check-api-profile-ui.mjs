import {chromium} from 'playwright';
import assert from 'node:assert/strict';
import {mkdir} from 'node:fs/promises';
const browser=await chromium.launch({channel:'chrome',headless:true});
const errors=[];let uploaded=false,puts=0,deletes=0;
const photo={name:'doctor.png',url:'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+jDQAAAABJRU5ErkJggg=='};
try{
 const page=await browser.newPage({viewport:{width:1440,height:1000}});page.on('pageerror',e=>errors.push(e.message));
 await page.route('**/api/v1/**',route=>{const req=route.request(),path=new URL(req.url()).pathname;let json={items:[],total:0};
  if(path.endsWith('/profile-photo')){if(req.method()==='PUT'){uploaded=true;puts++;}if(req.method()==='DELETE'){uploaded=false;deletes++;}json={images:uploaded?{profile_photo:photo}:{},photo:uploaded?photo:null};}
  else if(path.endsWith('/doctors/me'))json={user:{id:'doctor-ui',role:'DOCTOR',full_name:'Example Doctor',public_id:'D000001',approval_status:'APPROVED',doctor:{qualification:'MBBS',images:uploaded?{profile_photo:photo}:{}}}};
  return route.fulfill({json});});
 await page.goto('http://127.0.0.1:5175/doctor/settings');await page.getByLabel('Choose profile photo').setInputFiles({name:'doctor.png',mimeType:'image/png',buffer:Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+jDQAAAABJRU5ErkJggg==','base64')});
 await page.getByRole('button',{name:'Save photo',exact:true}).click();await page.getByText('Profile photo saved.',{exact:true}).waitFor();assert.equal(puts,1);await page.getByAltText('Your current doctor profile').waitFor();await page.getByAltText('Doctor profile',{exact:true}).waitFor();
 await mkdir('test-results',{recursive:true});await page.screenshot({path:'test-results/doctor-profile-photo-api.png',fullPage:true});
 await page.reload();await page.getByAltText('Your current doctor profile').waitFor();
 await page.getByRole('button',{name:'Remove photo',exact:true}).click();await page.getByText('Photo removed.',{exact:true}).waitFor();assert.equal(deletes,1);assert.equal(await page.getByAltText('Your current doctor profile').count(),0);
 await page.setViewportSize({width:390,height:844});assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
 console.log('PASS doctor photo upload, refreshed header, persistence, remove and mobile layout');
 const family=await browser.newPage();let saved='Example child';let edited;
 family.on('pageerror',e=>errors.push(e.message));
 await family.route('**/api/v1/**',route=>{const req=route.request(),path=new URL(req.url()).pathname;let json={items:[],total:0};const profile={id:'child-ui',module:'child',full_name:saved,date_of_birth:'2020-01-01',profile_type:'member',guardian_contact:''};
  if(path.endsWith('/me'))json={user:{id:'owner-ui',role:'PATIENT',full_name:'Example parent'}};
  else if(path.endsWith('/patients/profiles'))json={items:[profile],total:1};
  else if(path.endsWith('/patients/profiles/child-ui')){if(req.method()==='PUT'){edited=req.postDataJSON();saved=edited.full_name;profile.full_name=saved;}json={profile};}
  else if(path.endsWith('/reminders'))json={items:[],preferences:{in_app:true}};
  else if(path.endsWith('/dashboard'))json={counts:{},vaccination:{status:'NOT_AVAILABLE',message:'No schedule'}};
  else if(path.endsWith('/age'))json={age:{display:'6 years'}};
  return route.fulfill({json});});
 await family.goto('http://127.0.0.1:5174/customer/child/settings');await family.getByLabel('Edit profile full name').fill('Updated child');await family.getByLabel('Edit profile contact number').fill('+919876543210');await family.getByRole('button',{name:'Save profile information',exact:true}).click();await family.getByText('Profile information saved.',{exact:true}).waitFor();assert.equal(edited.full_name,'Updated child');assert.equal(edited.date_of_birth,undefined);console.log('PASS customer profile edit uses PUT with owner-editable fields');
 for(const [url,heading] of [['http://127.0.0.1:5174/customer/login',/login|welcome/i],['http://127.0.0.1:5175/doctor/login',/login|welcome/i]]){const p=await browser.newPage();p.on('pageerror',e=>errors.push(e.message));await p.goto(url);await p.locator('input[name=email]').waitFor();await p.locator('input[name=password]').waitFor();assert.ok(await p.getByRole('button',{name:/login|sign in/i}).count());}
 assert.deepEqual(errors,[]);console.log('PASS customer and doctor login forms; no browser runtime errors');
}finally{await browser.close();}
