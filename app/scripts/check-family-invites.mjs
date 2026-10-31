// Requires tests/family_invite_fixture.py on 5508 and Vite on 5173.
import {chromium} from 'playwright';
import assert from 'node:assert/strict';
const browser=await chromium.launch({channel:'msedge',headless:true});
try{
 const context=await browser.newContext();
 await context.route('**/api/**',async route=>{
   const url=new URL(route.request().url());url.port='5508';
   const response=await route.fetch({url:url.toString()});await route.fulfill({response});
 });
 const page=await context.newPage();const errors=[];page.on('pageerror',e=>errors.push(e.message));
 await page.goto('http://127.0.0.1:5173/customer/login');
 await page.evaluate(async()=>{const response=await fetch('/api/v1/patients/login',{method:'POST',credentials:'include',headers:{'Content-Type':'application/json','X-Auth-Transport':'cookie','X-Requested-With':'FamilyCare','X-FamilyCare-Portal':'patient'},body:JSON.stringify({email:'family@example.com',password:'FamilyPassword8!'})});const data=await response.json();if(!response.ok)throw Error(JSON.stringify(data));sessionStorage.setItem('familycare_csrf_patient',data.csrf_token);});
 await page.goto('http://127.0.0.1:5173/customer/dashboard');
 const panel=page.locator('.family-invitations');await panel.getByLabel('Member name',{exact:true}).fill('Example Member');
 await panel.getByLabel('Member email',{exact:true}).fill('member@example.com');
 await panel.getByLabel('Care area').selectOption('women');await panel.getByLabel('Relationship').selectOption('Mother');
 await panel.getByRole('button',{name:'Send invite email',exact:true}).click();
 await panel.getByRole('status').waitFor();
 const mail=await (await fetch('http://127.0.0.1:5508/__test/mail')).json();assert.equal(mail.items[0].email,'member@example.com');
 const link=mail.items[0].body.match(/http:\/\/127[^\s]+/)[0];
 await context.clearCookies();await page.goto(link);
 await page.getByText('Example Family',{exact:true}).waitFor();
 assert.equal(await page.getByLabel('Name',{exact:true}).inputValue(),'Example Member');
 assert.equal(await page.getByLabel('Email',{exact:true}).inputValue(),'member@example.com');
 assert(await page.getByLabel('Email',{exact:true}).evaluate(el=>el.readOnly));
 await page.getByLabel('Mobile number').fill('+919876543211');await page.getByLabel('Date of birth').fill('1995-02-28');
 await page.getByLabel('Password',{exact:true}).fill('MemberPassword8!');await page.getByLabel('Confirm password').fill('MemberPassword8!');
 await page.getByRole('checkbox').check();await page.getByRole('button',{name:'Send approval OTP to family',exact:true}).click();
 await page.getByLabel('Family approval OTP',{exact:true}).waitFor();
 const otpMail=await (await fetch('http://127.0.0.1:5508/__test/mail')).json();assert.equal(otpMail.items.at(-1).email,'family@example.com');
 const code=otpMail.items.at(-1).body.match(/OTP with that member only: (\d{6})/)[1];
 await page.getByLabel('Family approval OTP',{exact:true}).fill(code);await page.getByRole('button',{name:'Verify and create my profile',exact:true}).click();
 await page.getByRole('heading',{name:'Your profile is ready'}).waitFor();
 await page.screenshot({path:'test-results/family-invite-complete.png',fullPage:true});
 await page.getByRole('link',{name:'Sign in',exact:true}).click();
 const result=await page.evaluate(async()=>{const response=await fetch('/api/v1/patients/login',{method:'POST',credentials:'include',headers:{'Content-Type':'application/json','X-Auth-Transport':'cookie','X-Requested-With':'FamilyCare','X-FamilyCare-Portal':'patient'},body:JSON.stringify({email:'member@example.com',password:'MemberPassword8!'})});return {status:response.status,data:await response.json()};});
 assert.equal(result.status,200);assert.equal(result.data.user.email,'member@example.com');
 await page.goto('http://127.0.0.1:5173/customer/women/dashboard');await page.getByRole('heading',{name:/Example Member/}).first().waitFor({timeout:30000}).catch(async()=>{assert((await page.locator('body').innerText()).includes('Example Member'));});
 assert.deepEqual(errors,[]);
 console.log('PASS: family invite form, member email link, locked identity, family OTP, member verification/login and linked women workspace');
}finally{await browser.close();}
