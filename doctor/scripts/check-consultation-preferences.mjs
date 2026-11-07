import { chromium, expect } from '@playwright/test';
import assert from 'node:assert/strict';
const browser=await chromium.launch({channel:'chrome',headless:true});
const page=await browser.newPage();
let options={physical_enabled:true,video_enabled:false,physical_fee_paise:null,video_fee_paise:null};let saved;
const errors=[];page.on('pageerror',e=>errors.push(e.message));
await page.route('**/api/v1/**',route=>{const req=route.request(),path=new URL(req.url()).pathname;const json=data=>route.fulfill({json:data});
 if(path.endsWith('/doctors/me'))return json({user:{id:'doc',full_name:'QA Doctor',role:'DOCTOR',public_id:'D000007',approval_status:'APPROVED'}});
 if(path.endsWith('/consultation-settings')){if(req.method()==='PUT'){saved=req.postDataJSON();options=saved;}return json({consultation_options:options,doctor_id:'D000007',referral_id:'qaDoctorD000007'});}
 return json({items:[],total:0,unread_count:0,preferences:{}});
});
try{
 await page.goto('http://localhost:5173/doctor/settings');
 await expect(page.getByText('qaDoctorD000007',{exact:true})).toBeVisible();
 await page.getByLabel('physical consultation fee').fill('600');
 await page.getByLabel('Video consultation',{exact:true}).check();
 await page.getByLabel('video consultation fee').fill('400');
 await page.getByRole('button',{name:'Save consultation preferences'}).click();
 await expect(page.getByRole('status').filter({hasText:'Consultation modes and fees saved.'})).toBeVisible();
 assert.equal(saved.physical_fee_paise,60000);assert.equal(saved.video_fee_paise,40000);
 await page.getByLabel('Video consultation',{exact:true}).uncheck();
 await page.getByRole('button',{name:'Save consultation preferences'}).click();
 assert.equal(options.video_enabled,false);
 assert.deepEqual(errors,[]);console.log('PASS doctor settings referral ID, mode toggle, INR fees and saved API payload');
}finally{await browser.close();}
