import {chromium} from 'playwright';
import assert from 'node:assert/strict';
import {writeFile,unlink,mkdir} from 'node:fs/promises';
import {fileURLToPath} from 'node:url';
const html=new URL('../../app/women-articles-qa.html',import.meta.url);
const entry=new URL('../../app/women-articles-qa.tsx',import.meta.url);
const browser=await chromium.launch({channel:'msedge',headless:true});
try{
 await writeFile(html,'<html><body><div id="root"></div><script type="module" src="/women-articles-qa.tsx"></script></body></html>');
 await writeFile(entry,`import React from 'react';import {createRoot} from 'react-dom/client';import Manager from './src/components/WomenArticleManager';import Reader from '../customer/src/modules/women/WomenHealthArticles';const mode=new URLSearchParams(location.search).get('mode');const request=async(path,options={})=>{const r=await fetch('/api/v1/'+path,options);if(!r.ok)throw Error('Request failed');return r.json()};createRoot(document.getElementById('root')).render(mode==='reader'?<Reader profileId="qa" category="pregnancy"/>:<Manager request={request} doctor={mode==='doctor'}/>);`);
 const page=await browser.newPage();page.setDefaultTimeout(60000);const errors=[];page.on('pageerror',e=>errors.push(e.message));
 let items=[];let visibility=true;
 await page.route('**/api/v1/**',async route=>{
  const req=route.request(),url=new URL(req.url()),path=url.pathname;let response={};
  if(req.method()==='POST'){const a={...req.postDataJSON(),id:'qa-article',author:{full_name:'QA Admin',role:'ADMIN'}};items=[a];response={article:a};}
  else if(req.method()==='PUT'&&path.endsWith('/visibility')){visibility=req.postDataJSON().active;response={active:visibility};}
  else if(req.method()==='PUT'){items=[{...items[0],...req.postDataJSON()}];response={article:items[0]};}
  else if(path.endsWith('/qa-article'))response={article:items[0]};
  else response={items:items.map(a=>({...a,can_edit:false,doctor_active:visibility})),total:items.length,stage_month:3};
  await route.fulfill({json:response});
 });
 const base='http://127.0.0.1:5173/women-articles-qa.html';
 await page.goto(base);
 assert.equal(await page.getByRole('navigation',{name:'Article categories'}).getByRole('button').count(),7);
 await page.getByRole('button',{name:'Pregnancy care',exact:true}).click();
 await page.getByLabel('Title',{exact:true}).fill('Month three nutrition');
 await page.getByLabel('Description',{exact:true}).fill('QA article description supplied by the care team.');
 await page.getByLabel('Pregnancy month',{exact:true}).selectOption('3');
 await page.getByLabel('Time / stage label').fill('Daily care');
 await page.getByLabel('Status',{exact:true}).selectOption('PUBLISHED');
 await page.getByRole('button',{name:'Save article',exact:true}).click();
 await page.getByRole('heading',{name:'Month three nutrition',exact:true}).waitFor();
 assert.equal(items[0].stage_month,3);assert.equal(items[0].category,'pregnancy');
 await page.getByRole('button',{name:'Deactivate',exact:true}).click();
 await page.getByRole('button',{name:'Activate',exact:true}).waitFor();assert.equal(items[0].status,'DRAFT');
 await page.getByRole('button',{name:'Activate',exact:true}).click();
 await page.getByRole('button',{name:'Deactivate',exact:true}).waitFor();
 await page.goto(base+'?mode=doctor');await page.getByRole('button',{name:'Pregnancy care',exact:true}).click();
 await page.getByRole('button',{name:'Deactivate for my patients',exact:true}).click();
 await page.getByRole('button',{name:'Activate for my patients',exact:true}).waitFor();assert.equal(visibility,false);
 await page.getByText('Read admin article',{exact:true}).click();await page.getByText('QA article description supplied by the care team.',{exact:true}).waitFor();
 await page.goto(base+'?mode=reader');await page.getByText('Month three nutrition',{exact:true}).click();
 await page.getByText('QA article description supplied by the care team.',{exact:true}).waitFor();
 await page.setViewportSize({width:390,height:844});assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1));
 await mkdir(new URL('../../test-results/',import.meta.url),{recursive:true});
 await page.screenshot({path:fileURLToPath(new URL('../../test-results/women-articles-mobile.png',import.meta.url)),fullPage:true});
 assert.deepEqual(errors,[]);console.log('PASS: seven categories, month article creation, activation, doctor-scoped visibility, expanded reader, mobile layout; mocked API UI checks');
}finally{await browser.close();await Promise.allSettled([unlink(html),unlink(entry)]);}
