import { chromium, expect } from '@playwright/test';
const browser=await chromium.launch({channel:'chrome',headless:true});
const page=await browser.newPage();
const errors=[],brokenAssets=[];
page.on('pageerror',e=>errors.push(e.message));
page.on('response',response=>{if(response.status()>=400 && /\.(js|css)(\?|$)/.test(response.url()))brokenAssets.push(response.url());});
try{
 for(const width of [390,1366]){
  await page.setViewportSize({width,height:900});
  for(const route of ['/','/about','/services','/customer/login','/doctor/login']){
   const response=await page.goto('http://127.0.0.1:5178'+route,{waitUntil:'domcontentloaded',timeout:60000});
   expect(response.status()).toBe(200);
   await expect(page.locator('h1').first()).toBeVisible();
   expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1),route+' overflow').toBeTruthy();
  }
 }
 expect(errors).toEqual([]);expect(brokenAssets).toEqual([]);
 console.log('PASS production app/dist, direct route reloads, JS/CSS assets and desktop/mobile public/auth pages');
}finally{await browser.close();}
