import {chromium} from '@playwright/test';
import assert from 'node:assert/strict';
const browser=await chromium.launch({channel:'chrome',headless:true});
const self={id:'self-id',profile_type:'self',module:'adult',full_name:'Example Family',date_of_birth:'1995-02-28',created_at:'2026-01-01'};
const reports=[{id:'report',name:'Synthetic detailed medical report '+ 'longword'.repeat(15),created_at:'2026-11-02T00:00:00Z',category:'Lab tests'}];
for(const width of [280,320,360,390,440]){
 const page=await browser.newPage({viewport:{width,height:844},isMobile:true,hasTouch:true,deviceScaleFactor:3});
 await page.route('**/api/v1/**',route=>{const path=new URL(route.request().url()).pathname;let data={items:[],total:0};
 if(path.endsWith('/patients/me'))data={user:{id:'owner',role:'PATIENT',full_name:'Example Family',email:'family@example.com'}};
 else if(path.endsWith('/patients/profiles'))data={items:[self,...Array.from({length:6},(_,i)=>({id:'member-'+i,profile_type:'member',module:['child','women','adult'][i%3],full_name:'Example Family Member '+i,created_at:'2026-01-01',family_access:false}))],total:7};
 else if(path.endsWith('/self-id'))data={profile:self};
 else if(path.endsWith('/reports'))data={items:reports,total:1};
 return route.fulfill({json:data});});
 await page.goto('http://127.0.0.1:5173/customer/dashboard');await page.getByRole('heading',{name:'Recent reports',exact:true}).waitFor();await page.getByText(reports[0].name,{exact:true}).waitFor();
 await page.addStyleTag({content:'#root { min-width: 520px; }'});
 const bad=await page.evaluate(()=>[...document.querySelectorAll('.fh-main,.fh-main *')].filter(el=>el instanceof HTMLElement).filter(el=>{const r=el.getBoundingClientRect();return r.width>0&&(r.left< -1||r.right>document.documentElement.clientWidth+1||el.scrollWidth>el.clientWidth+2)}).map(el=>({tag:el.tagName,cls:el.className,width:el.clientWidth,scroll:el.scrollWidth,text:el.textContent?.slice(0,30)})));
 assert.deepEqual(bad,[],`Clipped elements at ${width}: ${JSON.stringify(bad)}`);
 await page.getByRole('heading',{name:'Quick actions',exact:true}).scrollIntoViewIfNeeded();
 await page.evaluate(()=>window.scrollBy(200,0));assert.equal(await page.evaluate(()=>scrollX),0);
 const arrow=await page.getByRole('button',{name:'Go back',exact:true}).boundingBox();assert.ok(arrow.y>=65&&arrow.y<140,`Back is not at top: ${JSON.stringify(arrow)}`);
 const textBad=await page.evaluate(()=>[...document.querySelectorAll('.fh-right p,.fh-quick button,.fh-overview p,.fh-report strong')].flatMap(el=>[...el.childNodes].filter(n=>n.nodeType===Node.TEXT_NODE&&n.textContent.trim()).flatMap(n=>{const range=document.createRange();range.selectNodeContents(n);return [...range.getClientRects()].filter(r=>r.left< -1||r.right>innerWidth+1).map(r=>({text:n.textContent,right:r.right}));})));
 assert.deepEqual(textBad,[],`Clipped text at ${width}`);
 await page.screenshot({path:`.preview/family-mobile-fit-${width}.png`});
 if(width===390){await page.getByRole('button',{name:'Open navigation',exact:true}).click();await page.screenshot({path:'.preview/family-mobile-drawer-fit.png'});}
 await page.close();console.log(`Mobile ${width}px: oversized parent, cards/text fit, no horizontal scroll, top Back passed`);
}
await browser.close();
