import {chromium,expect} from '@playwright/test';
import assert from 'node:assert/strict';
import {mkdir} from 'node:fs/promises';
const browser=await chromium.launch({headless:true});const page=await browser.newPage({viewport:{width:1600,height:1100},reducedMotion:'reduce'});const errors=[],unexpected=[];
page.on('pageerror',e=>errors.push(e.message));
const portal=process.env.PREVIEW_URL??'http://127.0.0.1:5180';
const records=[{id:'child-one',profile_type:'member',module:'child',full_name:'Aarav Sharma',date_of_birth:'2020-06-15',guardian_contact:'+919876543210',created_at:'2026-10-01T00:00:00Z'},{id:'child-two',profile_type:'member',module:'child',full_name:'Anaya Sharma',date_of_birth:'2022-06-15',created_at:'2026-10-01T00:00:00Z'}];const reports=[];
await page.route('**/api/v1/**',async route=>{const req=route.request(),url=new URL(req.url()),path=url.pathname;const json=data=>route.fulfill({json:data});
 if(path==='/api/v1/patients/me')return json({user:{id:'owner',role:'PATIENT',full_name:'Account Owner',email:'owner@example.com'}});
 if(path==='/api/v1/patients/profiles')return json({items:records,total:records.length});
 const match=path.match(/^\/api\/v1\/patients\/profiles\/([^/]+)(.*)$/);if(match){const profile=records.find(p=>p.id===match[1]);if(!profile)return route.fulfill({status:404,json:{error:{message:'Profile not found',code:'not_found'}}});const suffix=match[2];if(!suffix)return json({profile});
 if(suffix==='/connect-doctor'){assert.equal(req.method(),'POST');assert.equal(req.postDataJSON().referral_id,'rahulkumarD000001');profile.doctor={full_name:'Dr Rahul Kumar',referral_id:'rahulkumarD000001',email:'doctor@example.com',mobile_number:'+919876543211'};return json({profile});}
 if(suffix==='/reports'){if(req.method()==='GET')return json({items:reports,total:reports.length});const data=await new Request(req.url(),{method:'POST',body:req.postDataBuffer(),headers:{'content-type':req.headers()['content-type']}}).formData();assert.equal(data.get('file').name,'child-report.pdf');const report={id:'report-one',name:'child-report.pdf',created_at:'2026-10-27T00:00:00Z'};reports.push(report);return json({report});}
 }
 unexpected.push(req.method()+' '+path);return route.fulfill({status:404,json:{error:{message:'Unexpected API'}}});});

try{for(const width of [390,1366]){await page.setViewportSize({width,height:900});await page.goto(portal+'/customer/child/child-one/dashboard');await expect(page.getByRole('heading',{name:/Hello! Aarav/})).toBeVisible();await page.evaluate(()=>{if(!localStorage.getItem('familycare.child.v1.owner.child-one'))localStorage.setItem('familycare.child.v1.owner.child-one',JSON.stringify(Array.from({length:5},(_,i)=>({id:'test-growth-'+i,kind:'growth',title:'Measurement '+(i+1),date:'2026-'+String(i+6).padStart(2,'0')+'-01',height:String(100+i),weight:String(15+i*.4)}))));});await page.reload();await expect(page.locator('canvas')).toBeVisible();await page.evaluate(()=>document.fonts.ready);await page.screenshot({path:'artifacts/sage-final-'+width+'.png',fullPage:true});console.log(width,await page.locator('.ch-app').boundingBox());}assert.deepEqual(errors,[]);}finally{await browser.close();}