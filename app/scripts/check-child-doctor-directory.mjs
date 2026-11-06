import {chromium,expect} from '@playwright/test';
import assert from 'node:assert/strict';
import {mkdir} from 'node:fs/promises';
const browser=await chromium.launch({channel:'chrome',headless:true});
const profile={id:'demo-child',profile_type:'member',module:'child',full_name:'Demo Child',date_of_birth:'2020-02-21',gender:'Male',created_at:'2026-01-01',family_access:true};
const doctors=[{id:'doc-a',name:'Dr Demo Asha',specialization:'Pediatrics',referral_id:'demoAshaD000001',public_id:'D000001',qualification:'MBBS',experience:10},{id:'doc-b',name:'Dr Demo Ravi',specialization:'Family medicine',referral_id:'demoRaviD000002',public_id:'D000002',qualification:'MBBS',experience:8}];
let connected=null,posts=0;
try{
 const page=await browser.newPage({viewport:{width:1366,height:900},reducedMotion:'reduce'});const errors=[];page.on('pageerror',error=>errors.push(error.message));
 await page.route('**/api/v1/**',route=>{const req=route.request(),url=new URL(req.url()),path=url.pathname;const json=value=>route.fulfill({json:value});
 if(path==='/api/v1/patients/me')return json({user:{id:'demo-owner',role:'PATIENT',full_name:'Demo Owner',email:'demo@example.invalid'}});
 const remote={...profile,...(connected?{doctor:{id:connected.id,full_name:connected.name,referral_id:connected.referral_id,public_id:connected.public_id,specialization:connected.specialization,qualification:connected.qualification}}:{})};
 if(path==='/api/v1/patients/profiles')return json({items:[remote],total:1});
 if(path==='/api/v1/patients/profiles/demo-child')return json({profile:remote});
 if(path.endsWith('/doctor-directory')){const search=url.searchParams.get('search').toLowerCase();const items=doctors.filter(d=>(d.name+' '+d.specialization).toLowerCase().includes(search));return json({items,total:items.length});}
 if(path.endsWith('/connect-doctor')){posts++;const data=req.postDataJSON();connected=doctors.find(d=>d.referral_id===data.referral_id);if(!connected)return route.fulfill({status:422,json:{error:{code:'doctor_not_found',message:'Doctor ID not found'}}});return json({profile:{...profile,doctor:{...connected,full_name:connected.name}}});}
 if(path.endsWith('/age'))return json({age:{display:'6 years 8 months'}});
 if(path.endsWith('/dashboard'))return json({child:{age:{display:'6 years 8 months'}},counts:{},vaccination:{status:'NOT_AVAILABLE'}});
 return json({items:[],total:0,unread_count:0,status:'NOT_AVAILABLE'});
 });
 await page.goto('http://localhost:5173/customer/child/consultation');await expect(page.locator('.ch-directory-grid article')).toHaveCount(2);
 await expect(page.getByRole('heading',{name:'Request a consultation',exact:true})).toHaveCount(0);await expect(page.getByRole('heading',{name:'Consultation journal',exact:true})).toHaveCount(0);
 await page.getByRole('button',{name:'Add doctor',exact:true}).click();await expect(page.getByLabel('Doctor referral ID')).toBeVisible();await page.getByLabel('Doctor referral ID').fill('invalid');await page.getByRole('button',{name:'Connect doctor',exact:true}).click();await expect(page.getByRole('alert')).toContainText('Doctor ID not found');
 await page.getByLabel('Doctor referral ID').fill(doctors[0].referral_id);await page.getByRole('button',{name:'Connect doctor',exact:true}).click();await expect(page.getByText('Doctor connected successfully.',{exact:true})).toBeVisible();await expect(page.locator('#child-add-doctor')).toHaveCount(0);await expect(page.locator('.connected-doctor-summary')).toContainText('Dr Demo Asha');assert.equal(posts,2);
 const search=page.getByRole('textbox',{name:'Search child doctors'});await search.fill('Ravi');await expect(page.locator('.ch-directory-grid article')).toHaveCount(1);await expect(page.locator('.ch-directory-grid')).toContainText('Dr Demo Ravi');await expect(page.locator('.ch-directory-grid')).not.toContainText('Dr Demo Asha');
 await page.getByRole('button',{name:'Use referral ID'}).click();await expect(page.getByLabel('Doctor referral ID')).toHaveValue(doctors[1].referral_id);assert.equal(posts,2,'Selecting an ID must wait for connection confirmation');
 await search.fill('does-not-exist');await expect(page.getByText('No approved doctors match your search.')).toBeVisible();await search.fill('');await expect(page.locator('.ch-directory-grid article')).toHaveCount(2);
 await mkdir('app/.preview',{recursive:true});await page.screenshot({path:'app/.preview/child-doctor-directory-1366.png',fullPage:true});await page.setViewportSize({width:390,height:844});assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));await page.screenshot({path:'app/.preview/child-doctor-directory-390.png',fullPage:true});assert.deepEqual(errors,[]);console.log('PASS child doctor toggle, ID validation/connection, search/all/empty results, removed sections, explicit confirmation and mobile');
}finally{await browser.close();}
