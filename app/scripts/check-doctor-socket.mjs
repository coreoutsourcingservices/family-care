import {build} from 'esbuild';
import {chromium} from 'playwright';
import assert from 'node:assert/strict';

const result=await build({stdin:{contents:"import {connectDoctorNotifications} from './app/src/lib/notificationSocket'; window.connectNotifications=connectDoctorNotifications;",resolveDir:process.cwd()},bundle:true,write:false,define:{'import.meta.env.DEV':'true','import.meta.env.VITE_API_BASE_URL':'""','import.meta.env.VITE_NOTIFICATION_WS_URL':'undefined'}});
const browser=await chromium.launch({channel:'chrome',headless:true});
try{
  const page=await browser.newPage();let tickets=0,refreshes=0;
  await page.route('**/doctor/socket-test',r=>r.fulfill({contentType:'text/html',body:'<main>Socket test</main>'}));
  await page.route('**/api/v1/**',r=>{
    assert.equal(r.request().headers()['x-familycare-portal'],'doctor');
    if(r.request().url().endsWith('/auth/refresh')){refreshes++;return r.fulfill({json:{csrf_token:'renewed-doctor-csrf'}});}
    tickets++;return r.fulfill({json:{ticket:'synthetic-ticket-'+tickets}});
  });
  await page.goto('http://127.0.0.1:5173/doctor/socket-test');
  await page.evaluate(()=>{
    window.sockets=[];window.updates=0;window.states=[];
    window.WebSocket=class{
      constructor(url){this.url=url;window.sockets.push(this);setTimeout(()=>this.onopen?.(),0);}
      send(text){this.frame=JSON.parse(text);setTimeout(()=>this.onmessage?.({data:JSON.stringify({type:'ready'})}),0);}
      close(){this.onclose?.({code:1000});}
    };
  });
  await page.addScriptTag({content:result.outputFiles[0].text});
  await page.evaluate(()=>{window.disconnect=window.connectNotifications(()=>window.updates++,s=>window.states.push(s));});
  await page.waitForFunction(()=>window.states.includes('Live'));
  assert.deepEqual(await page.evaluate(()=>window.sockets[0].frame),{type:'auth',ticket:'synthetic-ticket-1'});
  assert.equal(await page.evaluate(()=>window.sockets[0].url),'ws://127.0.0.1:5002/ws/notifications');
  await page.evaluate(()=>window.sockets[0].onmessage({data:JSON.stringify({type:'notification',notification:{id:1}})}));
  assert.equal(await page.evaluate(()=>window.updates),2);
  await page.evaluate(()=>window.sockets[0].onclose({code:4401}));
  await page.waitForFunction(()=>window.sockets.length===2&&window.states.filter(s=>s==='Live').length===2);
  assert.equal(refreshes,1);assert.equal(tickets,2);
  await page.evaluate(()=>window.disconnect());
  assert.equal(await page.evaluate(()=>window.states.at(-1)),'Live');
  console.log('PASS doctor socket ticket auth, live event refresh, expired-session recovery and cleanup');
}finally{await browser.close();}
