import {chromium,expect} from '@playwright/test';
import assert from 'node:assert/strict';
import {mkdir} from 'node:fs/promises';
const browser=await chromium.launch({channel:'chrome',headless:true});
const base=process.env.FAMILY_TEST_URL||'http://localhost:5173';
async function fixture(page,module,empty=false){
 let profiles=empty?[]:[{id:'self-'+module,profile_type:'self',module,full_name:'Demo Owner',date_of_birth:'1995-03-09',family_access:true,created_at:'2026-01-01'},{id:'child-member',profile_type:'member',module:'child',full_name:'Demo Owner',date_of_birth:'2020-01-01',family_access:true,created_at:'2026-01-01'},{id:'women-member',profile_type:'member',module:'women',full_name:'Demo Member',date_of_birth:'1996-01-01',family_access:true,created_at:'2026-01-01'}];
 let saved;const errors=[];page.on('pageerror',e=>errors.push(e.message));
 await page.route('**/api/v1/**',route=>{const request=route.request(),url=new URL(request.url()),path=url.pathname;const json=data=>route.fulfill({json:data});
 if(path.endsWith('/patients/me'))return json({user:{id:'demo-owner',role:'PATIENT',full_name:'Demo Owner',email:'demo@example.invalid'}});
 if(path==='/api/v1/patients/profiles'){
  if(request.method()==='POST'){saved=request.postDataJSON();const profile={...saved,id:'new-self',created_at:'2026-11-05',family_access:true};profiles.push(profile);return json({profile});}
  return json({items:profiles.filter(p=>!url.searchParams.get('module')||p.module===url.searchParams.get('module')),total:profiles.length});}
 if(path.endsWith('/workspace')){const selected=profiles.find(item=>path.includes(item.id));return json({profile:{id:selected.id,name:selected.full_name,dob:selected.date_of_birth},owner:true,permissions:{},records:[]});}
 const profile=profiles.find(p=>path==='/api/v1/patients/profiles/'+p.id);if(profile)return json({profile});
 return json({items:[],total:0,unread_count:0});
 });return {errors,saved:()=>saved};
}
try{
 await mkdir('app/.preview',{recursive:true});
 for(const module of ['adult','women']){
  const page=await browser.newPage({viewport:{width:1366,height:900}});const state=await fixture(page,module);
  await page.goto(base+'/customer/dashboard');await expect(page.getByRole('region',{name:'Continue to your account'})).toBeVisible();await expect(page.locator('.fh-account-continue')).toContainText('Demo Owner');await expect(page.locator('.fh-sidebar').getByRole('link',{name:'Women shared tabs',exact:true})).toHaveCount(0);await expect(page.locator('.fh-sidebar').getByRole('link',{name:'Adult shared tabs',exact:true})).toHaveCount(0);await expect(page.locator('.fh-member-list .fh-member:not(.fh-add)')).toHaveCount(2);await expect(page.locator('.fh-members .fh-heading span')).toHaveText('2 added');
  await expect(page.locator('.fh-member-list')).not.toContainText('Self');await expect(page.locator('.fh-role-description').first()).toHaveText(module==='adult'?'Adult Health':"Women's Health");
  await page.locator('.fh-quick').getByRole('button',{name:'My account',exact:true}).click();await expect(page).toHaveURL(base+'/customer/'+module+'/dashboard?profile=self-'+module);
  const sidebar=page.locator(module==='adult'?'.ah-sidebar':'.ch-sidebar');
  await expect(sidebar.getByRole('link',{name:'Family dashboard',exact:true})).toBeVisible();
  await expect(sidebar.getByRole('link',{name:'Settings',exact:true})).toHaveCount(1);
  await sidebar.getByRole('link',{name:'Add notes',exact:true}).click();await expect(page.getByRole('heading',{name:'Your notes',exact:true})).toBeVisible();
  await sidebar.getByRole('link',{name:'Add member',exact:true}).click();await expect(page.getByRole('dialog',{name:'Add family member',exact:true})).toBeVisible();
  await page.getByRole('dialog',{name:'Add family member',exact:true}).getByRole('button',{name:'Close',exact:true}).click();await expect(page).toHaveURL(base+'/customer/dashboard');

  await page.goto(base+'/customer/dashboard');await page.locator('.fh-sidebar').getByRole('button',{name:'Open my health account',exact:false}).click();await expect(page).toHaveURL(base+'/customer/'+module+'/dashboard?profile=self-'+module);
  await page.goto(base+'/customer/dashboard');await page.locator('.fh-sidebar').getByRole('button',{name:'Add member',exact:false}).click();const picker=page.getByRole('dialog',{name:'Add family member',exact:true});await expect(picker).toBeVisible();await picker.getByRole('link',{name:"Women's Health",exact:false}).click();await expect(page.getByRole('dialog',{name:'Invite family member',exact:true})).toBeVisible();await expect(page.getByRole('button',{name:'Send email invitation',exact:false})).toBeVisible();
  if(module==='women'){await page.goto(base+'/customer/women/dashboard?profile=women-member');await expect(page.locator('.ch-sidebar')).toBeVisible();await expect(page.locator('.ch-sidebar').getByRole('link',{name:'Add member',exact:true})).toHaveCount(0);await expect(page.locator('.ch-sidebar').getByRole('link',{name:'Add notes',exact:true})).toHaveCount(0);await page.goto(base+'/customer/women/notes?profile=women-member');await expect(page.getByRole('heading',{name:'Page not found',exact:true})).toBeVisible();}
  assert.equal(state.saved(),undefined);assert.deepEqual(state.errors,[]);await page.close();console.log('PASS existing '+module+' self routing, member list separation and invitation flow');
 }
 for(const module of ['adult','women']){
  const page=await browser.newPage({viewport:{width:390,height:844}});const state=await fixture(page,module,true);
  await page.goto(base+'/customer/dashboard');await page.locator('.fh-self').getByRole('button',{name:'Add account',exact:true}).click();const picker=page.getByRole('dialog',{name:'Add self account'});await picker.getByRole('link',{name:module==='adult'?'Adult Health':"Women's Health",exact:false}).click();
  const form=page.getByRole('dialog',{name:'Set up self account'});await form.locator('input[name="memberDob"]').fill('1995-03-09');if(module==='adult')await form.getByLabel('Gender',{exact:true}).selectOption('Male');await form.getByRole('button',{name:'Continue',exact:true}).click();await form.getByRole('button',{name:'Continue',exact:true}).click();await form.getByRole('button',{name:'Confirm & save',exact:true}).click();
  await expect(page).toHaveURL(base+'/customer/'+module+'/dashboard?profile=new-self');assert.equal(state.saved().profile_type,'self');assert.equal(state.saved().module,module);
  await page.goto(base+'/customer/dashboard');await expect(page.locator('.fh-member-list .fh-member:not(.fh-add)')).toHaveCount(0);await expect(page.locator('.fh-members .fh-heading span')).toHaveText('0 added');
  assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));await page.screenshot({path:'app/.preview/family-self-'+module+'-390.png',fullPage:true});assert.deepEqual(state.errors,[]);await page.close();console.log('PASS create '+module+' Self payload, direct workspace navigation and exclusion from member list');
 }
}finally{await browser.close();}
