// Run after npm run build. Uses isolated SQLite fixtures, never Supabase or SMTP.
import assert from 'node:assert/strict';
import {spawn} from 'node:child_process';
import {fileURLToPath} from 'node:url';
import path from 'node:path';
import {createHmac} from 'node:crypto';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const backend=path.resolve(root,'../backend');
const python=process.platform==='win32'?path.join(backend,'venv/Scripts/python.exe'):path.join(backend,'venv/bin/python');
const apiProcess=spawn(python,[path.join(backend,'tests/frontend_fixture.py')],{cwd:backend,stdio:'pipe'});
const appProcess=spawn(process.execPath,[path.join(root,'node_modules/next/dist/bin/next'),'start','--port','3006'],{cwd:root,env:{...process.env,BACKEND_URL:'http://127.0.0.1:5501'},stdio:'pipe'});
let logs='';for(const p of [apiProcess,appProcess]){p.stderr.on('data',b=>{logs+=b.toString();});p.on('error',e=>{logs+=e.message;});}
const base='http://localhost:3006';const jar=new Map();
async function request(route,body,origin=base){const headers={Cookie:[...jar].map(([k,v])=>`${k}=${v}`).join('; ')};if(body!==undefined)Object.assign(headers,{'Content-Type':'application/json','Origin':origin,'X-Requested-With':'FamilyCare'});const r=await fetch(base+route,{method:body!==undefined?'POST':'GET',headers,body:body===undefined?undefined:JSON.stringify(body),redirect:'manual'});for(const cookie of r.headers.getSetCookie()){const [pair]=cookie.split(';');const i=pair.indexOf('=');const name=pair.slice(0,i),value=pair.slice(i+1);if(value)jar.set(name,value);else jar.delete(name);}return r;}
async function assertRedirect(route){const r=await request(route);if([307,308].includes(r.status)){assert.ok(r.headers.get('location'));return;}assert.equal(r.status,200);const html=await r.text();assert.match(html,/NEXT_REDIRECT|http-equiv="refresh"/);assert.ok(!html.includes('Care starts with you'));}
async function wait(url){for(let i=0;i<90;i++){try{if((await fetch(url)).ok)return;}catch{}await new Promise(r=>setTimeout(r,500));}throw new Error('Test service did not become ready');}
function otp(token){const {cid}=JSON.parse(Buffer.from(token.split('.')[1],'base64url'));const key='frontend-smoke-otp-'+'b'.repeat(48);let raw=createHmac('sha256',key).update('code:'+cid).digest(),index=0;while(true){const n=raw.readUInt32BE();if(n<Math.floor(2**32/1000000)*1000000)return String(n%1000000).padStart(6,'0');index++;raw=createHmac('sha256',key).update(Buffer.concat([raw,Buffer.from(String(index))])).digest();}}
try{
 await Promise.all([wait('http://127.0.0.1:5501/health'),wait(base)]);
 const loginPage=await request('/');assert.equal(loginPage.status,200);const loginHtml=await loginPage.text();assert.ok(!loginHtml.includes('Need organization-wide access?'));assert.ok(!loginHtml.includes('Superadmin sign in'));assert.ok(loginHtml.includes('Register as admin'));assert.equal((await request('/register')).status,200);assert.equal((await request('/superadmin')).status,200);
 await assertRedirect('/dashboard');
 let signup=await request('/api/v1/admin/register',{full_name:'New Admin',email:'new-admin@example.com',mobile_number:'+919876543210',password:'SmokePassword8!',confirm_password:'SmokePassword8!'});assert.equal(signup.status,202);const challenge=await signup.json();assert.equal(challenge.user_id,null);signup=await request('/api/v1/admin/verify-email',{challenge_token:challenge.challenge_token,otp:otp(challenge.challenge_token)});assert.equal(signup.status,202);const candidate=(await signup.json()).user;assert.equal(candidate.approval_status,'PENDING_APPROVAL');assert.equal((await request('/api/v1/admin/login',{email:'new-admin@example.com',password:'SmokePassword8!'})).status,403);
 assert.equal((await request('/api/v1/admin/login',{email:'admin@example.com',password:'SmokePassword8!'},'https://untrusted.example')).status,403);
 let response=await request('/api/v1/admin/login',{email:'admin@example.com',password:'SmokePassword8!'});assert.equal(response.status,200);let data=await response.json();assert.equal(data.user.role,'ADMIN');assert.equal(data.challenge_token,undefined);assert.equal(data.access_token,undefined);assert.equal(data.csrf_token,undefined);
 assert.ok(response.headers.getSetCookie().some(c=>c.startsWith('fc_access=')&&/Path=\//.test(c)&&/HttpOnly/i.test(c)));assert.ok(jar.has('fc_csrf'));
 assert.equal((await request('/dashboard')).status,200);assert.equal((await request('/doctors')).status,200);await assertRedirect('/superadmin/dashboard');
 response=await request('/api/v1/admin/patients');assert.equal(response.status,200);assert.equal((await response.json()).total,1);
 assert.equal((await request('/api/v1/admin/doctors/D_TEST/approve',{})).status,200);
 assert.equal((await request('/api/v1/admin/doctors/D_TEST/suspend',{})).status,200);
 assert.equal((await request('/api/v1/admin/doctors/D_TEST/reactivate',{})).status,200);
 assert.equal((await request('/api/v1/auth/refresh',{})).status,200);
 assert.equal((await request('/api/v1/auth/logout',{})).status,200);assert.equal(jar.has('fc_access'),false);
 response=await request('/api/v1/superadmin/login',{email:'super@example.com',password:'SmokePassword8!'});assert.equal(response.status,200);assert.equal((await response.json()).user.role,'SUPERADMIN');assert.equal((await request('/superadmin/dashboard')).status,200);assert.equal((await request('/api/v1/superadmin/admins')).status,200);await assertRedirect('/dashboard');
 assert.equal((await request(`/api/v1/superadmin/admins/${candidate.public_id}/approve`,{})).status,200);assert.equal((await request('/api/v1/auth/logout',{})).status,200);assert.equal((await request('/api/v1/admin/login',{email:'new-admin@example.com',password:'SmokePassword8!'})).status,200);
 console.log('PASS: registration OTP and superadmin approval, login pages, route protection, cross-origin rejection, password-only login, HttpOnly sessions, CSRF, directories, doctor actions, refresh, logout and superadmin login.');
}catch(error){console.error(error.stack || error.message);console.error(logs.slice(-2000));process.exitCode=1;}finally{apiProcess.kill();appProcess.kill();}
