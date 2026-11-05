import {chromium} from '@playwright/test';
import assert from 'node:assert/strict';
const base=process.env.CUSTOMER_FIT_URL||'http://127.0.0.1:5178';
const browser=await chromium.launch({channel:'chrome',headless:true});
const childPages=['dashboard','vaccination','history','growth','consultation','care','reports','settings'];
const adultPages=['dashboard','bp','glucose','lipids','medicine','lifestyle','screening','history','reports','consultation_request','reminder','settings','sharing','planner'];
const womenPages=['dashboard','health','cycle','pcos','pregnancy','fertility','symptoms','nutrition','screening','records','consultation','settings','sharing','planner'];
const long='Synthetic record with a very long description '+ 'longfilename'.repeat(8);
const profiles=['child','adult','women'].map((module,i)=>({id:module+'-fit',module,profile_type:i===1?'self':'member',full_name:'Example '+module+' family member',date_of_birth:i===0?'2020-02-21':'1995-02-28',created_at:'2026-01-01',family_access:true}));
const reports=[{id:'report-fit',name:long+'.pdf',created_at:'2026-11-03T00:00:00Z',category:'Lab tests',size_bytes:1000}];
const childRecords=['growth','history','nutrition','care','consultation'].map((kind,i)=>({id:'child-record-'+i,kind,title:long,date:'2026-10-20',status:'Recorded',notes:long,weight:'23',height:'115',meal:'Lunch'}));
const adultRecords=['bp','glucose','lipids','medicine','lifestyle','screening','history','reminder'].map((kind,i)=>({id:'adult-record-'+i,kind,title:long,date:'2026-10-20',notes:long,status:'Planned',systolic:120,diastolic:80,glucose:90,total:180}));
const womenRecords=womenPages.filter(id=>!['dashboard','records','sharing','planner','settings','consultation'].includes(id)).map((section,i)=>({id:'women-record-'+i,section,title:long,date:'2026-10-20',notes:long,category:'Other',version:'0'}));
const routes=['/customer/dashboard','/customer/dashboard?view=notes',...childPages.map(p=>'/customer/child/'+p),...adultPages.map(p=>'/customer/adult/'+p),...womenPages.map(p=>'/customer/women/'+p)];
const failures=[];
try{for(const width of (process.env.FIT_WIDTHS||'320,390,768,1366').split(',').map(Number)){
 const page=await browser.newPage({viewport:{width,height:900},reducedMotion:'reduce'});page.setDefaultTimeout(12000);let errors=[];
 page.on('pageerror',e=>errors.push(e.message));
 await page.route('**/api/v1/**',route=>{const url=new URL(route.request().url()),path=url.pathname;let data={items:[],total:0};
  if(path.endsWith('/patients/me'))data={user:{id:'fit-owner',role:'PATIENT',full_name:'Example Family',email:'family@example.com'}};
  else if(path.endsWith('/patients/profiles')){const module=url.searchParams.get('module');const items=profiles.filter(p=>!module||p.module===module);data={items,total:items.length};}
  else if(profiles.some(p=>path.endsWith('/patients/profiles/'+p.id)))data={profile:profiles.find(p=>path.endsWith('/'+p.id))};
  else if(path.endsWith('/reports'))data={items:reports,total:1};
  else if(path.endsWith('/workspace'))data={owner:true,permissions:Object.fromEntries(womenPages.map(p=>[p,'edit'])),profile:{id:'women-fit',name:'Example women',dob:'1995-02-28'},records:womenRecords,access_expires_at:null};
  else if(path.endsWith('/sharing'))data={tabs:{health:'My Health',reports:'Medical Records',consultation:'Doctor Consultation'},recipients:[{id:'doctor-fit',name:'Example Registered Doctor',role:'DOCTOR'}],grants:[]};
  else if(path.endsWith('/pregnancy-care'))data={settings:null,guide:null};
  else if(path.endsWith('/vaccination-context'))data={context:{}};
  else if(path.endsWith('/children/child-fit/dashboard'))data={counts:{vaccination:0},vaccination:{status:'NOT_AVAILABLE',message:'No schedule'},child:{age:{display:'6 years'}}};
  else if(path.endsWith('/age'))data={age:{display:'6 years'}};
  else if(path.endsWith('/reminders'))data={items:[],preferences:{in_app:true}};
  else if(path.endsWith('/health-guide'))data={status:'NOT_AVAILABLE',message:'No published guide'};
  else if(path.endsWith('/growth-nutrition-guide'))data={active:true,status:'NOT_AVAILABLE',child:{age:{display:'6 years'}},age_band:null,guide:null};
  else if(path.endsWith('/patients/adults/adult-fit/records'))data={items:adultRecords,total:adultRecords.length};
  else if(path.endsWith('/records')&&path.includes('/children/'))data={items:childRecords,total:childRecords.length};
  else if(path.endsWith('/patients/doctor-directory'))data={items:[{id:'doctor-fit',name:'Example Registered Doctor',specialization:'General Medicine',qualification:'MBBS',experience:10,rating:4.8,review_count:3,referral_id:'D000001'}],total:1};
  else if(path.endsWith('/text'))data={status:'NOT_REQUESTED',text:'',language:'en'};
  else if(path.endsWith('/report-text/options'))data={languages:[{code:'en',name:'English'}]};
  return route.fulfill({json:data});
 });
 const selected=(width>=768?routes.filter(path=>/dashboard|sharing|consultation|records|reports|growth|pregnancy/.test(path)):routes).filter(path=>!process.env.FIT_ROUTE||path===process.env.FIT_ROUTE);
 for(const path of selected){
  errors=[];await page.goto(base+path);
  try{await page.locator('.fh-main,.ch-content,.ah-content').first().waitFor();await page.waitForTimeout(180);
   const bad=await page.evaluate(()=>{
    const nodes=[...document.querySelectorAll('.fh-main,.ch-content,.ah-content,.ch-topbar,.ah-header')].flatMap(root=>[root,...root.querySelectorAll('*')]);
    return nodes.filter(el=>{const r=el.getBoundingClientRect(),style=getComputedStyle(el);return r.width>0&&r.height>0&&style.visibility!=='hidden'&&!el.closest('[hidden]')&&!(el.tagName==='INPUT'&&el.type==='file')&&(r.left< -1||r.right>innerWidth+1);}).slice(0,12).map(el=>({tag:el.tagName,cls:typeof el.className==='string'?el.className:el.tagName,text:el.textContent?.slice(0,35),right:Math.round(el.getBoundingClientRect().right)}));
   });
   const scroll=await page.evaluate(()=>({root:document.documentElement.scrollWidth,viewport:innerWidth}));
   if(bad.length||errors.length||scroll.root>scroll.viewport+1){const extra=await page.evaluate(()=>[...document.querySelectorAll('body *')].filter(el=>{const r=el.getBoundingClientRect();return r.width>0&&r.right>innerWidth+1;}).slice(0,12).map(el=>({tag:el.tagName,cls:el.getAttribute('class'),parent:el.parentElement?.getAttribute('class'),text:el.textContent?.slice(0,35)})));failures.push({width,path,bad,scroll,extra,errors:[...errors]});}
   if(width===390&&['/customer/dashboard','/customer/child/growth','/customer/adult/dashboard','/customer/women/dashboard'].includes(path))await page.screenshot({path:'.preview/customer-fit-'+path.split('/').slice(2).join('-')+'.png',fullPage:true});
   if(width<=390){
    const add=page.getByRole('button',{name:/^(Add record|Log period|Add measurement|Add note|Add vaccination record)$/}).first();
    if(await add.count()&&await add.isVisible()){
     await add.click();await page.waitForTimeout(80);
     const formBad=await page.locator('.ch-entry-form,.wh-modal,.ah-form,.profile-planner form').evaluateAll(forms=>forms.flatMap(form=>[form,...form.querySelectorAll('input,select,textarea,button,label')]).filter(el=>{const r=el.getBoundingClientRect();return r.width>0&&(r.left< -1||r.right>innerWidth+1);}).map(el=>({tag:el.tagName,cls:el.className})));
     if(formBad.length)failures.push({width,path,formBad});
    }
   }
  }catch(e){failures.push({width,path,error:e.message.slice(0,200),errors:[...errors]});}
 }
 await page.close();console.log(`${width}px: ${selected.length} customer pages checked`);
}
console.log(JSON.stringify(failures,null,2));assert.deepEqual(failures,[],'Customer pages must fit the viewport without clipping or runtime errors');
}finally{await browser.close();}
