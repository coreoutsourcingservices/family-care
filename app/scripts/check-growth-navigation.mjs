import {chromium,expect} from '@playwright/test';
import assert from 'node:assert/strict';
import {readFile,mkdir} from 'node:fs/promises';

const content=JSON.parse(await readFile('backend/content/child_growth_nutrition.json','utf8'));
const base=process.env.GROWTH_TEST_URL||'http://127.0.0.1:5173';
const browser=await chromium.launch({channel:'chrome',headless:true});
const profile={id:'growth-child',profile_type:'member',module:'child',full_name:'Priyanshu Kishor',date_of_birth:'2020-02-21',gender:'Male',created_at:'2026-01-01',family_access:true};
const records=[{id:'growth-before',kind:'growth',title:'Earlier measurement',date:'2026-05-04',height:'118.2',weight:'22.7'},
 {id:'growth-latest',kind:'growth',title:'Latest measurement',date:'2026-10-29',height:'120.5',weight:'23.8',notes:'Keep recording measurements and bring your growth diary to the next visit.'},
 {id:'meal-latest',kind:'nutrition',title:'Lunch note',date:'2026-10-30',meal:'Lunch',notes:'Rice, dal and vegetables recorded for lunch.'}];

async function fixture(page,{denied=false,networkError=false,empty=false}={}){
 const calls={session:0,profiles:0,records:0};const errors=[];let saved;
 page.on('pageerror',error=>errors.push(error.message));
 await page.route('**/api/v1/**',async route=>{
  const request=route.request(),path=new URL(request.url()).pathname;
  const json=data=>route.fulfill({json:data});
  if(path==='/api/v1/patients/me'){
   calls.session++;await new Promise(resolve=>setTimeout(resolve,200));
   if(networkError)return route.abort('failed');
   if(denied)return route.fulfill({status:401,json:{error:{code:'session_revoked',message:'Sign in again'}}});
   return json({user:{id:'growth-owner',role:'PATIENT',full_name:'Family Owner',email:'owner@example.com'}});
  }
  if(path==='/api/v1/patients/profiles'){calls.profiles++;return json({items:[profile],total:1});}
  if(path.endsWith('/growth-nutrition-guide')){
   const band=content.age_bands.find(b=>b.id==='year-6');
   return json({active:true,status:'AVAILABLE',child:{age:{display:'6 years 8 months'}},age_band:{label:band.label},guide:{notice:content.notice,nutrition:band,growth_monitoring:content.growth_monitoring,food_safety:content.food_safety,sources:content.sources}});
  }
  if(path.endsWith('/records')){calls.records++;return json({items:empty?[]:records,total:empty?0:records.length});}
  if(path.endsWith('/growth')&&request.method()==='POST'){saved=request.postDataJSON();return json({record:{...saved,id:'new-measurement',kind:'growth'}});}
  if(path.endsWith('/nutrition')&&request.method()==='POST')return json({record:{...request.postDataJSON(),id:'new-meal',kind:'nutrition'}});
  if(path.endsWith('/dashboard'))return json({child:{age:{display:'6 years 8 months'}},counts:{},vaccination:{status:'NOT_AVAILABLE',message:'Synthetic empty schedule'}});
  if(path.endsWith('/age'))return json({age:{display:'6 years 8 months'}});
  if(path.endsWith('/health-guide'))return json({status:'NOT_AVAILABLE',message:'No published guide'});
  if(path.endsWith('/reminders'))return json({items:[],preferences:{in_app:true}});
  return json({items:[],total:0,unread_count:0});
 });
 return {calls,errors,saved:()=>saved};
}

try{
 await mkdir('app/.preview',{recursive:true});
 const page=await browser.newPage({viewport:{width:1366,height:900},reducedMotion:'reduce'});
 const state=await fixture(page);
 await page.goto(base+'/customer/child/dashboard');
 await expect(page.locator('.ch-sidebar')).toBeVisible();
 await expect(page.locator('.ch-chart canvas').first()).toBeVisible();
 assert.equal(await page.locator('.ch-breadcrumb,.ch-device-note').count(),0);
 await page.evaluate(()=>{window.originalChildShell=document.querySelector('.ch-child-workspace');});
 for(const section of ['growth','care','dashboard','growth']){
  await page.locator('.ch-sidebar a[href="/customer/child/'+section+'"]').click();
  await expect(page).toHaveURL(new RegExp('/customer/child/'+section+'$'));
  assert(await page.evaluate(()=>window.originalChildShell===document.querySelector('.ch-child-workspace')),'Child workspace remounted on '+section);
  assert.equal(await page.locator('.customer-session-status,.ch-loading').count(),0,'Fullscreen loader returned during navigation');
 }
 await expect(page.getByRole('heading',{name:'Example Daily Meal Plan',exact:true})).toBeVisible();
 await expect(page.getByRole('heading',{name:'Nutrition Priorities',exact:true})).toBeVisible();
 await expect(page.getByRole('region',{name:'Growth latest update',exact:true})).toContainText('Keep recording measurements');
 await expect(page.getByRole('region',{name:'Meal latest update',exact:true})).toContainText('Rice, dal and vegetables');
 assert.equal(await page.locator('.gn-latest').count(),2);
 const order=await page.evaluate(()=>['.ch-growth-overview','.ch-overview-chart .gn-latest','.gn-guide'].map(selector=>document.querySelector(selector).getBoundingClientRect().top+scrollY));
 assert(order[0]<order[1]&&order[1]<order[2],'Chart, latest update and guide must appear in that order');
 assert.deepEqual(state.calls,{session:1,profiles:1,records:1},'Internal navigation refetched session/profile/records');
 await page.getByRole('button',{name:'Add measurement',exact:true}).click();
 await page.getByLabel('Measurement label').fill('New measurement');
 await page.getByLabel('Weight (kg)',{exact:false}).fill('24');
 await page.getByLabel('Height / length (cm)',{exact:false}).fill('121');
 await page.getByRole('button',{name:'Save to account',exact:true}).click();
 await expect(page.locator('.gn-snapshot')).toContainText('121 cm');
 assert.equal(state.saved().weight,'24');
 await page.getByRole('button',{name:'Add meal note',exact:true}).click();
 await page.getByLabel('Meal / feeding name').fill('Fresh meal note');
 await page.getByLabel('Food, portions or feeding notes').fill('New meal update stays with the meal journal.');
 await page.getByRole('button',{name:'Save to account',exact:true}).click();
 await expect(page.getByRole('region',{name:'Meal latest update',exact:true})).toContainText('New meal update stays with the meal journal.');
 await expect(page.getByRole('region',{name:'Growth latest update',exact:true})).not.toContainText('New meal update');
 for(const width of [390,768,1366,1920]){
  await page.setViewportSize({width,height:1000});
  await page.evaluate(()=>window.scrollTo(0,0));
  await expect(page.locator('.gn-hero')).toBeVisible();
  if(width>=1366){
   const columns=await page.evaluate(()=>['.ch-overview-chart','.gn-meal-panel'].map(selector=>{const r=document.querySelector(selector).getBoundingClientRect();return {left:r.left,right:r.right,top:r.top};}));
   assert(Math.abs(columns[0].top-columns[1].top)<2&&columns[0].right<=columns[1].left,'Growth chart and meal journal should be side by side');
  }
  await expect.poll(()=>page.locator('.ch-chart canvas').evaluate(canvas=>{
   const pixels=canvas.getContext('2d').getImageData(0,0,canvas.width,canvas.height).data;
   let painted=0;for(let index=3;index<pixels.length;index+=4)if(pixels[index])painted++;
   return painted;
  })).toBeGreaterThan(100);
  await page.screenshot({path:'app/.preview/growth-nutrition-'+width+'.png',fullPage:true});
  const overflow=await page.evaluate(()=>({screen:innerWidth,body:document.documentElement.scrollWidth}));
  assert(overflow.body<=overflow.screen+1,JSON.stringify({width,...overflow}));
 }
 assert.deepEqual(state.errors,[]);
 await page.close();
 for(const options of [{denied:true},{networkError:true},{empty:true}]){
  const check=await browser.newPage({viewport:{width:390,height:850},reducedMotion:'reduce'});await fixture(check,options);
  await check.goto(base+'/customer/child/growth');
  if(options.denied){await expect(check).toHaveURL(/\/customer\/login/);assert.equal(await check.locator('.ch-child-workspace').count(),0);}
  else if(options.networkError){await expect(check.getByRole('button',{name:'Try again',exact:true})).toBeVisible();assert.equal(await check.locator('.ch-child-workspace').count(),0);}
  else{await expect(check.getByRole('heading',{name:'Example Daily Meal Plan',exact:true})).toBeVisible();await expect(check.locator('.gn-snapshot')).toContainText('Not recorded');assert.equal(await check.locator('.ch-chart canvas').count(),0);}
  await check.close();
 }
 console.log('PASS: retained workspace, one session/profile/records fetch, chart/update/guide order, measurement save, four responsive widths, empty records and auth/network failure gates.');
}finally{await browser.close();}
