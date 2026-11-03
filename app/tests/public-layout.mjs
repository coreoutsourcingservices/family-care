// Read-only checks against the running local portals.
import {chromium,expect} from '@playwright/test';
const browser=await chromium.launch({channel:'chrome',headless:true});
try{
 const page=await browser.newPage();
 await page.route(/fonts\.googleapis\.com|fonts\.gstatic\.com/,route=>route.abort());
 for(const width of [360,390,768,1366,1920,2560]){
  await page.setViewportSize({width,height:900});
  for(const route of ['/','/services','/privacy','/terms','/customer/login','/doctor/login']){
   await page.goto('http://127.0.0.1:5173'+route,{waitUntil:'domcontentloaded',timeout:60000});
   await expect(page.locator('h1').first()).toBeVisible({timeout:30000});
   expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1),route+' overflow at '+width).toBe(true);
   if(route==='/privacy')await expect(page.getByText('Privacy and your information',{exact:true})).toBeVisible();
   if([390,1920].includes(width)&&route==='/')await page.screenshot({path:'.preview/public-home-'+width+'.png',fullPage:true});
  }
 }
 await page.close();console.log('PASS: live public, services, privacy, terms and both login pages fit 360–2560px');
}finally{await browser.close()}
