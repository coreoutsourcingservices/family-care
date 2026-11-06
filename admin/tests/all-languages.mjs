import assert from 'node:assert/strict';
import {spawn,spawnSync} from 'node:child_process';
import {readFileSync,writeFileSync} from 'node:fs';
import {fileURLToPath} from 'node:url';
import path from 'node:path';
import {chromium} from 'playwright';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const backend=path.resolve(root,'../backend');
const messages=JSON.parse(readFileSync(path.join(backend,'locales/ml.json'),'utf8'));
const catalogs=Object.fromEntries(['en','hi','mr','ml','ta','te','gu','bn','kn','pa','ur','or','as','ne','fr','awadhi','bhojpuri','dogri','khasi','kokborok','konkani','maithili','manipuri','marwari','mizo','santali','tulu'].map(code=>[code,JSON.parse(readFileSync(path.join(backend,'locales',code+'.json'),'utf8'))]));
const generatedFiles=['tsconfig.json','next-env.d.ts'].map(name=>[path.join(root,name),readFileSync(path.join(root,name))]);
const api=spawn(path.join(backend,'venv/Scripts/python.exe'),['tests/frontend_fixture.py'],{cwd:backend,env:{...process.env,FRONTEND_FIXTURE_THREADS:'1'},stdio:'pipe'});
const app=spawn(process.execPath,[path.join(root,'node_modules/next/dist/bin/next'),'dev','--port','3006'],{cwd:root,env:{...process.env,BACKEND_URL:'http://127.0.0.1:5501',NEXT_DIST_DIR:'.next-localization'},stdio:'pipe'});
let browser,logs='';for(const child of [api,app]){child.stderr.on('data',b=>logs+=b);child.stdout.on('data',b=>logs+=b);child.on('error',e=>logs+=e.message);}
async function ready(url){for(let i=0;i<100;i++){try{if((await fetch(url)).ok)return;}catch{}await new Promise(r=>setTimeout(r,500));}throw Error('Server not ready '+url);}
try{
 await Promise.all([ready('http://127.0.0.1:5501/health'),ready('http://localhost:3006')]);
 browser=await chromium.launch({headless:true,channel:'msedge'});
 for(const role of (process.env.LANGUAGE_MATRIX_ROLES||'admin,superadmin').split(',')){
  const context=await browser.newContext({viewport:{width:1440,height:1000}}),page=await context.newPage(),errors=[];
  page.on('pageerror',e=>errors.push(e.message));const prefix=role==='admin'?'':'/superadmin';
  page.setDefaultTimeout(60000);page.setDefaultNavigationTimeout(120000);
  const login=await context.request.post('http://localhost:3006/api/v1/'+role+'/login',{headers:{Origin:'http://localhost:3006','X-Requested-With':'FamilyCare','X-FamilyCare-Portal':role},data:{email:role==='admin'?'admin@example.com':'super@example.com',password:'SmokePassword8!'}});
  assert.equal(login.status(),200,await login.text());console.log(role+' fixture login ready');
  await page.goto('http://localhost:3006'+prefix+'/vaccination');await page.locator('.language-selector select').first().selectOption('Kerala');await page.waitForFunction(()=>!!document.querySelector('option[value="ml"]'));await page.locator('.language-selector select').nth(1).selectOption('ml');await page.waitForFunction(()=>document.documentElement.lang==='ml');
  await page.locator('.language-selector select').nth(1).selectOption('__other__');await page.waitForFunction(()=>!!document.querySelector('option[value="fr"]'));
  for(const [code,words] of Object.entries(catalogs)){
   await page.locator('.language-selector select').nth(1).selectOption(code);await page.waitForFunction(code=>document.documentElement.lang===code,code);
   assert.ok((await page.locator('.page-heading h1').innerText()).includes(words.Vaccination),role+' '+code+' title');
   assert.equal(await page.locator('#uip-starter-title').innerText(),words['UIP vaccination schedule']);
   assert.equal(await page.locator('.sa-sidebar a[href="'+prefix+'/dashboard"]').innerText(),words.Dashboard);
   assert.equal(await page.locator('html').getAttribute('dir'),code==='ur'?'rtl':'ltr');
  }
  for(const code of (process.env.LANGUAGE_MATRIX_PANELS||'en,hi,ml,fr,ur').split(',')){
   await page.locator('.language-selector select').nth(1).selectOption(code);await page.waitForFunction(code=>document.documentElement.lang===code,code);
   const words=catalogs[code];
   console.log(role+' panels: '+code);
   for(const [route,key] of [['doctors','Doctors'],['patients','Patients'],['settings','Account settings'],[role==='admin'?'women-health-articles':'growth-nutrition',role==='admin'?'Women Health Articles':'Growth & Nutrition'],['recycle-bin','Recycle Bin'],[role==='admin'?'recent-activity':'audit-logs',role==='admin'?'Recent Activity':'Activity Log']]){
    await page.goto('http://localhost:3006'+prefix+'/'+route);await page.waitForFunction(code=>document.documentElement.lang===code,code);
    await page.waitForFunction(text=>document.querySelector('.page-heading h1')?.textContent.includes(text),words[key]);
   }
   await page.goto('http://localhost:3006'+prefix+'/vaccination');await page.waitForFunction(code=>document.documentElement.lang===code,code);
   await page.locator('.language-selector select').nth(1).selectOption('__other__');await page.waitForFunction(()=>!!document.querySelector('option[value="fr"]'));
  }
  await page.locator('.language-selector select').nth(1).selectOption('ml');await page.waitForFunction(()=>document.documentElement.lang==='ml');
  await page.getByRole('tab',{name:messages['Dose & Schedule'],exact:true}).click();
  const age=page.getByLabel(messages['Age unit'],{exact:true});await age.selectOption('months');assert.equal(await age.inputValue(),'months');assert.equal(await age.locator('option:checked').innerText(),messages.months);
  for(const title of ['Eligibility Rules','Reminder Settings','Change History','Vaccine Catalog'])await page.getByRole('tab',{name:messages[title],exact:true}).click();
  assert.equal(await page.locator('.sa-sidebar nav').evaluate(e=>e.scrollWidth<=e.clientWidth),true);
  assert.deepEqual(errors,[]);console.log('PASS '+role+': 27 language selections; panel page translations; RTL; canonical form values');await context.close();
 }
}catch(e){console.error(e);console.error(logs.slice(-2500));process.exitCode=1;}
finally{await browser?.close();for(const child of [api,app])if(child.pid)spawnSync('taskkill',['/PID',String(child.pid),'/T','/F'],{stdio:'ignore'});for(const [file,content] of generatedFiles)writeFileSync(file,content);}
