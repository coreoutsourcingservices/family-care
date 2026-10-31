// Uses the isolated management_dashboard_fixture API behind the preview Next app on 3006.
import {chromium} from 'playwright';
import assert from 'node:assert/strict';
for(let attempt=0;;attempt++){try{const r=await fetch('http://127.0.0.1:5511/health',{signal:AbortSignal.timeout(2000)});if(r.ok)break;}catch{}if(attempt>=30)throw Error('Dashboard fixture did not start');await new Promise(r=>setTimeout(r,500));}
const browser=await chromium.launch({channel:'msedge',headless:true});
try{
 const context=await browser.newContext({viewport:{width:1536,height:1050}});const page=await context.newPage();page.setDefaultTimeout(90000);page.setDefaultNavigationTimeout(120000);const errors=[];
 page.on('pageerror',e=>errors.push(e.message));await page.addInitScript(()=>localStorage.setItem('familycare-language','en'));
 await page.goto('http://localhost:3006/superadmin',{waitUntil:'domcontentloaded',timeout:120000});
 await page.locator('.language-selector select').first().waitFor({timeout:60000});
 await page.getByLabel('Email address',{exact:true}).fill('super@example.com');await page.getByLabel('Password',{exact:true}).fill('SmokePassword8!');
 await page.getByRole('button',{name:'Sign in',exact:true}).click();await page.waitForURL('**/superadmin/dashboard',{timeout:120000});
 await page.getByRole('heading',{name:'User Growth',exact:true}).waitFor({timeout:60000});
 await page.locator('.sa-stats .sa-stat strong').first().filter({hasText:/[0-9]/}).waitFor();
 assert.equal(await page.locator('.sa-stats .sa-stat').count(),4);
 assert.equal(await page.getByRole('button',{name:'Approve Suman Reddy',exact:true}).count(),0);
 const data=await page.evaluate(async()=>{const r=await fetch('/api/v1/superadmin/dashboard',{headers:{'X-Requested-With':'FamilyCare','X-FamilyCare-Portal':'superadmin'}});return r.json();});
 const reviewName=data.pending_requests.items.find(p=>p.can_review)?.full_name;
 const displayed=await page.locator('.sa-stats .sa-stat strong').allTextContents();
 assert.deepEqual(displayed.map(s=>Number(s.replaceAll(',',''))),['administrators','doctors','patients','children'].map(k=>data.metrics[k].total));
 await page.screenshot({path:'../test-results/superadmin-dashboard-desktop.png',fullPage:true});
 await page.getByRole('combobox',{name:'User growth period'}).selectOption('3');assert.equal(await page.locator('.sa-chart-values tbody tr').count(),3);
 await page.getByRole('button',{name:'Collapse sidebar',exact:true}).click();await page.waitForFunction(()=>document.querySelector('.sa-workspace')?.classList.contains('sa-collapsed'));
 await page.getByRole('button',{name:'Expand sidebar',exact:true}).click();
 await page.getByRole('textbox',{name:'Search doctors, patients, administrators'}).fill('Neha');
 await page.getByRole('region',{name:'Search results'}).getByRole('link').first().waitFor();
 assert((await page.getByRole('region',{name:'Search results'}).innerText()).includes('Neha Sharma'));
 await page.getByRole('textbox',{name:'Search doctors, patients, administrators'}).fill('');
 if(reviewName){await page.getByRole('button',{name:'Approve '+reviewName,exact:true}).click();
 await page.getByRole('button',{name:'Confirm approval',exact:true}).click();
 await page.getByText('Request approved.',{exact:true}).waitFor();
 await page.getByRole('button',{name:'Approve '+reviewName,exact:true}).waitFor({state:'hidden'});}
 await page.getByRole('link',{name:'Growth Reports',exact:true}).click();
 await page.getByRole('heading',{name:'Care that follows every milestone'}).waitFor();
 await page.goto('http://localhost:3006/superadmin/dashboard',{waitUntil:'domcontentloaded',timeout:60000});
 await page.getByRole('heading',{name:'User Growth',exact:true}).waitFor();
 await page.locator('.language-selector select').first().waitFor();
 await page.locator('.sa-stats .sa-stat strong').first().filter({hasText:/[0-9]/}).waitFor();
 await page.setViewportSize({width:390,height:844});
 await page.waitForFunction(()=>document.documentElement.scrollWidth<=innerWidth+1);
 const dimensions=await page.evaluate(()=>({width:window.innerWidth,scroll:document.documentElement.scrollWidth,overflow:[...document.querySelectorAll('body *')].filter(n=>n.getBoundingClientRect().right>innerWidth+1).slice(0,8).map(n=>({name:n.className,right:n.getBoundingClientRect().right}))}));assert(dimensions.scroll<=dimensions.width+1,JSON.stringify(dimensions));
 await page.getByRole('button',{name:'Open navigation',exact:true}).click();
 await page.locator('.sa-sidebar.is-open').waitFor({state:'visible'});
 await page.getByRole('button',{name:'Close navigation',exact:true}).last().click();
 await page.screenshot({path:'../test-results/superadmin-dashboard-mobile.png',fullPage:true});
 assert.deepEqual(errors,[]);
 console.log('PASS real dashboard totals, monthly chart selector, global search, authorized approval, coverage page, sidebar collapse and mobile layout');
}finally{await browser.close();}
