// Isolated browser regression: no Supabase, SMTP or external translation requests.
import assert from 'node:assert/strict';
import {spawn,spawnSync} from 'node:child_process';
import {readFileSync,readdirSync} from 'node:fs';
import {fileURLToPath} from 'node:url';
import path from 'node:path';
import os from 'node:os';
import {chromium} from 'playwright';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const backend=path.resolve(root,'../backend');
const python=path.join(backend,process.platform==='win32'?'venv/Scripts/python.exe':'venv/bin/python');
const api=spawn(python,[path.join(backend,'tests/frontend_fixture.py')],{cwd:backend,stdio:'pipe'});
const app=spawn(process.execPath,[path.join(root,'node_modules/next/dist/bin/next'),'start','--port','3006'],{cwd:root,env:{...process.env,BACKEND_URL:'http://127.0.0.1:5501'},stdio:'pipe'});
const base='http://localhost:3006';
let logs='',browser;
for(const process of [api,app]){process.stderr.on('data',b=>{logs+=b;});process.on('error',e=>{logs+=e.message;});}
const catalogs=Object.fromEntries(readdirSync(path.join(backend,'locales')).filter(f=>f.endsWith('.json')).map(f=>[f.slice(0,-5),JSON.parse(readFileSync(path.join(backend,'locales',f),'utf8'))]));
const checkedCatalogs=process.env.LOCALIZATION_QUICK?{en:catalogs.en,mr:catalogs.mr,fr:catalogs.fr}:catalogs;
async function ready(url){for(let i=0;i<100;i++){try{if((await fetch(url)).ok)return;}catch{}await new Promise(r=>setTimeout(r,500));}throw new Error('Fixture failed to start');}
async function language(page,code){await page.locator('.language-selector select').nth(1).selectOption(code);await page.waitForFunction(code=>document.documentElement.lang===code,code);}
try{
 await Promise.all([ready(base),ready('http://127.0.0.1:5501/health')]);
 browser=await chromium.launch({headless:true,...(process.env.PLAYWRIGHT_CHANNEL?{channel:process.env.PLAYWRIGHT_CHANNEL}:{})});
 for(const role of ['admin','superadmin']){
  const context=await browser.newContext({viewport:{width:1440,height:1000}});
  const page=await context.newPage();const errors=[];page.on('pageerror',e=>errors.push(page.url()+': '+e.message));
  const login=role==='admin'?'/':'/superadmin';
  await page.goto(base+login+'?session=expired');
  await page.locator('.language-selector select').nth(1).waitFor({state:'visible'});
  await page.locator('.language-selector select').nth(1).selectOption('__other__');
  await page.waitForFunction(()=>!!document.querySelector('.language-selector option[value="fr"]'));
  await language(page,'fr');
  assert.equal(await page.locator('.login-form-wrap h2').innerText(),catalogs.fr['Welcome back.']);
  await page.getByRole('button',{name:catalogs.fr['Regional languages'],exact:true}).click();
  assert.equal(await page.locator('option[value="__other__"]').count(),1);
  for(const [code,messages] of Object.entries(checkedCatalogs)){
   await page.evaluate(code=>localStorage.setItem('familycare-language',code),code);
   await page.goto(base+login+'?session=expired');
   await page.waitForFunction(code=>document.documentElement.lang===code,code);
   await page.waitForFunction(message=>document.querySelector('[role="status"]')?.textContent===message,messages['Your session has ended. Please sign in again.']);
   assert.equal(await page.locator('.login-form-wrap h2').innerText(),messages['Welcome back.']);
   assert.ok((await page.locator('.login-story h1').innerText()).includes(messages['Better care starts']));
   assert.equal(await page.locator('.language-selector').count(),1);
  }
  // Reproduce the reported stale English notice: switch without reloading.
  await page.locator('.language-selector select').first().selectOption('Maharashtra');
  await page.waitForFunction(()=>!!document.querySelector('option[value="mr"]'));
  for(const code of ['mr','hi','en','mr']){
   await language(page,code);
   assert.equal(await page.locator('.alert[role="status"]').innerText(),catalogs[code]['Your session has ended. Please sign in again.']);
  }
  await page.screenshot({path:path.join(os.tmpdir(),`familycare-${role}-marathi.png`),fullPage:true});
  await page.locator('#identifier').fill(role==='admin'?'admin@example.com':'super@example.com');
  await page.locator('#password').fill('SmokePassword8!');
  await page.locator('button.login-submit').click();
  const prefix=role==='admin'?'':'/superadmin';
  await page.waitForURL(base+prefix+'/dashboard');
  await page.locator('.workspace .language-selector').waitFor({state:'visible'});
  await page.waitForFunction(()=>document.documentElement.lang==='mr');
  assert.equal(await page.locator('.language-selector').count(),1);
  for(const route of ['dashboard','doctors','patients','settings',...(role==='superadmin'?['admins','audit-logs']:[])]){
   await page.goto(base+prefix+'/'+route);
   await page.waitForFunction(()=>document.documentElement.lang==='mr');
   const heading=await page.locator('.page-heading h1').innerText();
   const key={dashboard:'Care starts with you',doctors:'Doctors',patients:'Patients',settings:'Account settings',admins:'Administrators','audit-logs':'Activity log'}[route];
   assert.ok(heading.includes(catalogs.mr[key]),`${role} ${route}: ${heading}`);
  }
  await page.goto(base+prefix+'/dashboard');
  await page.waitForFunction(()=>document.documentElement.lang==='mr');
  await page.locator('.workspace .page-heading h1').waitFor({state:'visible'});
  await page.screenshot({path:path.join(os.tmpdir(),`familycare-${role}-dashboard-marathi.png`),fullPage:true});
  assert.deepEqual(errors,[]);
  await context.close();
  console.log(`PASS ${role}: ${Object.keys(checkedCatalogs).length} complete login languages, session notice switching, saved preference, authenticated dashboard and all panel routes.`);
 }
}catch(error){console.error(error.stack||error);console.error(logs.slice(-2000));process.exitCode=1;}
finally{
 for(const child of [api,app]){if(process.platform==='win32')spawnSync('taskkill',['/PID',String(child.pid),'/T','/F'],{stdio:'ignore'});else child.kill();}
 await browser?.close();
}
