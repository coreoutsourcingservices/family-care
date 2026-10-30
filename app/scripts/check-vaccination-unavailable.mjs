import {build} from 'esbuild';
import {chromium} from 'playwright';
import {createRequire} from 'node:module';
import path from 'node:path';
import fs from 'node:fs';
import assert from 'node:assert/strict';
const require=createRequire(import.meta.url);
const bundle=await build({stdin:{contents:"import React from 'react';import{createRoot}from'react-dom/client';import M from './admin/src/components/vaccination-manager';createRoot(document.getElementById('root')).render(<M role='ADMIN'/>);",resolveDir:process.cwd(),loader:'tsx'},jsx:'automatic',bundle:true,write:false,define:{'process.env.NODE_ENV':'"production"'},plugins:[{name:'fixture',setup(b){
 b.onResolve({filter:/^react(?:-dom)?(?:\/.*)?$/},a=>({path:require.resolve(a.path)}));
 b.onResolve({filter:/^@\/lib\/api$/},()=>({path:'api',namespace:'fixture'}));
 b.onLoad({filter:/.*/,namespace:'fixture'},()=>({contents:"export async function api(path){if(window.__vaxFail)throw new Error('Database connection is temporarily unavailable. Please retry shortly.');return {items:path.includes('/vaccines')?[{id:'example',name_en:'Example vaccine',code:'TEST',active:true,category:'Government',protects_against:'Synthetic test'}]:[],total:path.includes('/vaccines')?1:0};}"}));
 b.onResolve({filter:/^@\//},a=>({path:path.join(process.cwd(),'admin/src',a.path.slice(2)+'.ts')}));
}}]});
const browser=await chromium.launch({channel:'chrome',headless:true});
try{
 const p=await browser.newPage();const errors=[];p.on('pageerror',e=>errors.push(e.message));
 await p.setContent('<main><div id="root"></div></main>');await p.evaluate(()=>window.__vaxFail=true);
 await p.addStyleTag({content:fs.readFileSync('admin/src/app/globals.css','utf8').split('\n').slice(1).join('\n')});await p.addScriptTag({content:bundle.outputFiles[0].text});
 await p.getByText('Unavailable',{exact:true}).first().waitFor();assert.deepEqual(await p.locator('.vax-stats strong').allTextContents(),Array(5).fill('Unavailable'));
 await p.evaluate(()=>window.__vaxFail=false);await p.getByRole('button',{name:'Refresh',exact:true}).click();await p.getByText('Example vaccine',{exact:true}).first().waitFor();assert.equal(await p.locator('.vax-stats strong').first().textContent(),'1');
 await p.evaluate(()=>window.__vaxFail=true);await p.getByRole('button',{name:'Refresh',exact:true}).click();await p.getByRole('alert').waitFor();assert.equal(await p.locator('.vax-stats strong').first().textContent(),'1');assert.deepEqual(errors,[]);
 console.log('PASS failed API shows Unavailable, Refresh recovers, later failure retains last loaded data.');
}finally{await browser.close();}
