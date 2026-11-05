import {chromium,expect} from '@playwright/test';
import assert from 'node:assert/strict';
import {mkdir} from 'node:fs/promises';

const browser=await chromium.launch({channel:'chrome',headless:true});
const base=process.env.REPORT_TEST_URL||'http://127.0.0.1:5173';
try{
 const page=await browser.newPage({viewport:{width:1366,height:900},reducedMotion:'reduce'});
 const errors=[],attempts=new Map(),reports=[{id:'existing',name:'existing-report.pdf',category:'Lab tests',created_at:'2026-10-29T00:00:00Z',size_bytes:100}];
 const profile={id:'report-child',profile_type:'member',module:'child',full_name:'Example Child',date_of_birth:'2020-02-21',created_at:'2026-01-01',family_access:true};
 page.on('pageerror',error=>errors.push(error.message));
 await page.route('**/api/v1/**',async route=>{
  const request=route.request(),url=new URL(request.url()),path=url.pathname;
  const json=data=>route.fulfill({json:data});
  if(path==='/api/v1/patients/me')return json({user:{id:'report-owner',role:'PATIENT',full_name:'Example Owner'}});
  if(path==='/api/v1/patients/profiles')return json({items:[profile],total:1});
  if(path==='/api/v1/patients/profiles/report-child')return json({profile});
  if(path==='/api/v1/patients/profiles/report-child/reports'){
   if(request.method()==='GET')return json({items:reports,total:reports.length});
   const form=await new Request(request.url(),{method:'POST',body:request.postDataBuffer(),headers:{'content-type':request.headers()['content-type']}}).formData();
   assert.equal(form.getAll('file').length,1,'Each request must contain exactly one private report');
   const file=form.get('file'),count=(attempts.get(file.name)||0)+1;attempts.set(file.name,count);
   if(file.name==='retry-this.pdf'&&count===1)return route.fulfill({status:502,json:{error:{code:'report_upload_failed',message:'Storage temporarily unavailable. Retry this report.'}}});
   if(file.name==='limited-once.pdf'&&count===1)return route.fulfill({status:429,json:{error:{code:'too_many_requests',message:'Wait one minute before uploading more reports.'}}});
   assert.equal(form.get('category'),'Lab tests');
   const report={id:'saved-'+reports.length,name:file.name,category:form.get('category'),size_bytes:file.size,created_at:new Date().toISOString()};reports.push(report);
   return route.fulfill({status:201,json:{report,text_extraction:{status:'UNAVAILABLE',message:'Report uploaded. Text reading can be retried later.'}}});
  }
  if(path.endsWith('/dashboard'))return json({child:{age:{display:'6 years'}},counts:{},vaccination:{status:'NOT_AVAILABLE',message:''}});
  if(path.endsWith('/age'))return json({age:{display:'6 years'}});
  if(path.endsWith('/reminders'))return json({items:[],preferences:{in_app:true}});
  return json({items:[],total:0,unread_count:0});
 });
 await page.goto(base+'/customer/child/reports');
 await expect(page.locator('.ch-reference-report-grid>article')).toHaveCount(1);
 await page.getByRole('button',{name:'Upload reports',exact:true}).click();
 await page.getByLabel('Category for new files').selectOption('Lab tests');
 const file=index=>({name:`synthetic-report-${index}.pdf`,mimeType:'application/pdf',buffer:Buffer.from('%PDF-1.7 synthetic test only')});
 await page.getByLabel('Choose report files',{exact:true}).setInputFiles([
  ...Array.from({length:12},(_,index)=>file(index)),
  {name:'retry-this.pdf',mimeType:'application/octet-stream',buffer:Buffer.from('%PDF-1.7 synthetic retry')},
  {name:'unsupported.txt',mimeType:'text/plain',buffer:Buffer.from('Not a report')},
 ]);
 await expect(page.locator('.cr-upload-queue>li')).toHaveCount(14);
 await page.getByRole('button',{name:'Upload 13 reports',exact:true}).click();
 await expect(page.locator('.cr-upload-actions [role=status]')).toContainText('12 uploaded, 2 need attention');
 assert.equal(attempts.size,13,'Invalid files should not block valid uploads or reach the backend');
 await expect(page.locator('.ch-reference-report-grid>article')).toHaveCount(13);
 await page.getByRole('button',{name:'Retry retry-this.pdf',exact:true}).click();
 await expect(page.locator('.cr-upload-actions [role=status]')).toContainText('13 uploaded, 1 need attention');
 assert.equal(attempts.get('retry-this.pdf'),2);
 assert([...attempts.entries()].every(([name,count])=>name==='retry-this.pdf'||count===1),'A successful report was uploaded twice');
 await page.getByLabel('Choose report files',{exact:true}).setInputFiles([file(20),file(21)]);
 await page.getByRole('button',{name:'Upload 2 reports',exact:true}).click();
 await expect(page.locator('.ch-reference-report-grid>article')).toHaveCount(16);
 await expect(page.locator('.cr-upload-actions [role=status]')).toContainText('15 uploaded, 1 need attention');
 await expect(page.locator('.cr-upload-queue')).toContainText('Report uploaded. Text reading can be retried later.');
 await page.getByLabel('Choose report files',{exact:true}).setInputFiles([
  {name:'limited-once.pdf',mimeType:'application/pdf',buffer:Buffer.from('%PDF-1.7 synthetic')},
  {name:'after-limit.pdf',mimeType:'application/pdf',buffer:Buffer.from('%PDF-1.7 synthetic')},
 ]);
 await page.getByRole('button',{name:'Upload 2 reports',exact:true}).click();
 await expect(page.locator('.ch-error[role=alert]')).toContainText('Wait one minute');
 assert.equal(attempts.has('after-limit.pdf'),false,'The batch must pause when rate-limited');
 await page.getByRole('button',{name:'Upload 2 reports',exact:true}).click();
 await expect(page.locator('.ch-reference-report-grid>article')).toHaveCount(18);
 assert.equal(attempts.get('limited-once.pdf'),2);
 assert.equal(attempts.get('after-limit.pdf'),1);
 for(const width of [390,1366]){
  await page.setViewportSize({width,height:900});await page.evaluate(()=>scrollTo(0,0));
  await mkdir('app/.preview',{recursive:true});
  await page.screenshot({path:`app/.preview/report-batch-${width}.png`,fullPage:true});
  const fits=await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1);assert(fits,`Upload panel overflows at ${width}px`);
 }
 assert.deepEqual(errors,[]);
 console.log('PASS: 13-file batch, invalid-file isolation, continued uploads after storage failure, retry without duplicates, rate-limit pause/resume, adding files, OCR unavailable warning, saved list and responsive layouts.');
}finally{await browser.close();}
