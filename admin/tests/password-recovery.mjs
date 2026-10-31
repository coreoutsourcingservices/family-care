// Start backend/tests/admin_reset_fixture.py first. SMTP and real accounts are never used.
import {chromium} from 'playwright';
import assert from 'node:assert/strict';
const browser=await chromium.launch({channel:'msedge',headless:true});
try{
 const context=await browser.newContext();
 await context.route('**/api/v1/**',async route=>{
  const url=new URL(route.request().url());url.hostname='127.0.0.1';url.port='5510';
  const response=await route.fetch({url:url.toString(),headers:{...route.request().headers(),'x-auth-transport':'cookie'}});
  await route.fulfill({response});
 });
 // The dashboard SSR uses the production backend; this isolated UI test stops at a neutral page.
 await context.route('**/dashboard',route=>route.fulfill({contentType:'text/html',body:'<h1>Signed in</h1>'}));
 const page=await context.newPage();const errors=[];page.on('pageerror',e=>errors.push(e.message));
 await page.addInitScript(()=>localStorage.setItem('familycare-language','en'));
 await page.goto('http://localhost:3005',{waitUntil:'domcontentloaded',timeout:60000});
 await page.locator('.language-selector select').first().waitFor({timeout:60000});
 await page.getByLabel('Email address',{exact:true}).fill('admin@example.com');
 await page.getByRole('button',{name:'Forgot password?',exact:true}).click();
 assert.equal(await page.getByLabel('Email address',{exact:true}).inputValue(),'admin@example.com');
 await page.getByRole('button',{name:'Send reset code',exact:true}).click();
 await page.getByLabel('Verification code',{exact:true}).waitFor();
 const code=await(await fetch('http://127.0.0.1:5510/__test/reset-code')).json();
 await page.getByLabel('Verification code',{exact:true}).fill(code.otp);
 await page.getByLabel('New password',{exact:true}).fill('RecoveredPassword8!');
 await page.getByLabel('Confirm new password',{exact:true}).fill('RecoveredPassword8!');
 await page.getByRole('button',{name:'Reset password',exact:true}).click();
 await page.getByText('Password reset. Sign in with your new password.',{exact:true}).waitFor();
 assert.equal(await page.getByLabel('Password',{exact:true}).inputValue(),'');
 assert.equal(await page.locator('.language-selector .error-text').count(),0);
 await page.screenshot({path:'../test-results/admin-password-recovery.png',fullPage:true});
 await page.getByLabel('Password',{exact:true}).fill('RecoveredPassword8!');
 const loggedIn=page.waitForResponse(r=>r.url().endsWith('/api/v1/admin/login')&&r.request().method()==='POST');
 await page.getByRole('button',{name:'Sign in',exact:true}).click();
 assert.equal((await loggedIn).status(),200);
 await page.waitForURL('**/dashboard');
 assert.deepEqual(errors,[]);
 console.log('PASS admin forgot-password form, OTP reset via real isolated API, new-password login and bundled English fallback');
}finally{await browser.close();}
