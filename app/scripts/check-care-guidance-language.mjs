import { chromium, expect } from '@playwright/test';
import assert from 'node:assert/strict';
import { mkdir } from 'node:fs/promises';
const browser=await chromium.launch({channel:'chrome',headless:true});
const page=await browser.newPage({viewport:{width:1366,height:900}});
const errors=[];page.on('pageerror',error=>errors.push(error.message));
let module='adult';
const languages=[{code:'en',name:'English',native_name:'English',translation_status:'available'}, {code:'hi',name:'Hindi',native_name:'हिन्दी',translation_status:'available'}, {code:'ml',name:'Malayalam',native_name:'മലയാളം',translation_status:'available'}];
await page.route('**/api/v1/**',route=>{
  const path=new URL(route.request().url()).pathname;
  const json=data=>route.fulfill({json:data});
  const profile={id:'guide-'+module,profile_type:'self',module,full_name:'QA Private Name',date_of_birth:module==='child'?'2020-01-01':'1995-01-01',created_at:'2026-01-01',family_access:true};
  if(path==='/api/v1/localization')return json({location:{state:'Kerala',status:'detected'},languages,recommended_language:'en'});
  if(path.endsWith('/localization/states'))return json({items:[{name:'Kerala'},{name:'Maharashtra'}]});
  if(path.endsWith('/localization/languages'))return json({items:languages,total:3});
  if(path.includes('/localization/messages/'))return json({messages:{},language:path.split('/').at(-1)});
  if(path.endsWith('/patients/me'))return json({user:{id:'guide-owner',role:'PATIENT',full_name:'QA Account'}});
  if(path==='/api/v1/patients/profiles')return json({items:[profile],total:1});
  if(path==='/api/v1/patients/profiles/'+profile.id)return json({profile});
  if(path.endsWith('/workspace'))return json({profile:{id:profile.id,name:profile.full_name,dob:profile.date_of_birth},owner:true,permissions:{},records:[{id:'cycle',section:'cycle',date:'2026-11-01',start_date:'2026-11-01',end_date:'2026-11-05',title:'User private note',flow:'Light'}]});
  if(path.includes('/patients/adults/')&&path.endsWith('/records'))return json({items:[{id:'bp',kind:'bp',date:'2026-11-01',title:'User private BP note',systolic:190,diastolic:122}]});
  if(path.endsWith('/pregnancy-care'))return json({settings:null,guide:null});
  if(path.endsWith('/growth-nutrition-guide'))return json({active:true,status:'AVAILABLE',age_band:{label:'6–7 years'},guide:{notice:'Use age-appropriate growth charts.',nutrition:{foods:'Balanced meals for the saved age',meal_frequency:'Regular meals and snacks'},sources:[{title:'API source',url:'https://www.who.int/'}]}});
  if(path.endsWith('/age'))return json({age:{display:'6 years'}});
  if(path.endsWith('/dashboard'))return json({child:{age:{display:'6 years'}},counts:{},vaccination:{status:'NOT_AVAILABLE'}});
  return json({items:[],total:0,unread_count:0,status:'NOT_AVAILABLE'});
});
try {
  await mkdir('app/.preview',{recursive:true});
  await page.goto('http://localhost:5173/customer/adult/bp');
  await expect(page.getByRole('combobox',{name:'Language',exact:true})).toBeVisible();
  await expect(page.locator('.cg-reading')).toContainText('190/122');
  await expect(page.locator('.cg-urgent')).toBeVisible();
  await page.getByRole('combobox',{name:'Language',exact:true}).selectOption('hi');
  await expect(page.locator('.cg-card h2')).toHaveText('ब्लड प्रेशर की देखभाल');
  await expect(page.locator('.ah-content')).toContainText('User private BP note');
  await page.getByRole('combobox',{name:'Language',exact:true}).selectOption('__more');
  await expect(page.locator('#customer-language-panel')).toBeVisible();
  await expect(page.locator('.customer-language-state select')).toHaveValue('Kerala');
  await expect(page.getByRole('radio',{name:'Malayalam',exact:true})).toBeVisible();
  await page.keyboard.press('Escape');
  for(const width of [1366,390,320]){
    await page.setViewportSize({width,height:900});
    assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),'Adult overflow '+width);
    await page.screenshot({path:`app/.preview/guidance-adult-${width}.png`,fullPage:true});
  }
  await page.getByRole('combobox',{name:'Language',exact:true}).selectOption('en');
  module='women';
  for(const section of ['cycle','pcos','pregnancy','fertility','symptoms','nutrition','screening','records']){
    await page.goto('http://localhost:5173/customer/women/'+section);
    await expect(page.locator('.cg-rail')).toBeVisible();
    assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),'Women overflow '+section);
  }
  await page.setViewportSize({width:1366,height:900});
  await page.goto('http://localhost:5173/customer/women/cycle');
  await expect(page.locator('.cg-rail')).toBeVisible();
  await page.screenshot({path:'app/.preview/guidance-women-cycle-1366.png',fullPage:true});
  module='child';
  await page.goto('http://localhost:5173/customer/child/growth');
  await expect(page.locator('.cg-rail')).toContainText('Balanced meals for the saved age');
  await expect(page.locator('.cg-band')).toHaveText('6–7 years');
  assert.deepEqual(errors,[]);
  console.log('PASS page-specific guidance, saved BP alert, English/Hindi, IP state, more languages, child API guide and responsive layouts');
} finally {await browser.close();}
