import {chromium,expect} from '@playwright/test';
import assert from 'node:assert/strict';
import {mkdir} from 'node:fs/promises';
const base=process.env.MARKETING_TEST_URL||'http://127.0.0.1:5173';
const browser=await chromium.launch({channel:'chrome',headless:true});
await mkdir('app/.preview',{recursive:true});
async function setup(page,published=false){
 const errors=[];page.on('pageerror',e=>errors.push(e.message));
 await page.route('**/api/v1/**',route=>route.fulfill({json:{items:published&&route.request().url().includes('audience=child')?[{title:'Published family care update',content:'This is the complete published educational article.',audience:'child'}]:[]}}));
 return errors;
}
try{
 for(const width of [360,390,768,1366,1920]){
  const page=await browser.newPage({viewport:{width,height:900},reducedMotion:'reduce'});const errors=await setup(page);
  for(const path of ['/','/about']){
   await page.goto(base+path);await expect(page.locator('.mc-hero h1')).toBeVisible();
   await page.evaluate(()=>document.querySelectorAll('img').forEach(image=>image.loading='eager'));
   await page.locator('.mc-footer').scrollIntoViewIfNeeded();
   await expect.poll(()=>page.evaluate(()=>[...document.images].filter(i=>!i.complete||!i.naturalWidth).map(i=>i.src))).toEqual([]);
   assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),'Horizontal overflow: '+path+' '+width);
   await page.evaluate(()=>scrollTo(0,0));
   await page.screenshot({path:`app/.preview/marketing-${path==='/'?'home':'about'}-${width}.png`,fullPage:true});
  }
  if(width===390){
   await page.getByRole('button',{name:'Open navigation'}).click();await expect(page.locator('#marketing-navigation')).toBeVisible();
   await page.locator('#marketing-navigation').getByRole('link',{name:'Home',exact:true}).click();await expect(page).toHaveURL(base+'/');
   await expect(page.getByRole('button',{name:'Open navigation'})).toBeVisible();
  }
  assert.deepEqual(errors,[]);await page.close();console.log('PASS responsive home/about '+width+'px, images, runtime');
 }
 const page=await browser.newPage({viewport:{width:1366,height:900}});const errors=await setup(page,true);
 await page.goto(base);await page.getByRole('button',{name:'Search care services'}).click();
 const search=page.getByRole('dialog',{name:'How can we help your family?'});await expect(search).toBeVisible();
 await page.getByRole('searchbox').fill('nutrition');await expect(search.getByRole('link')).toHaveCount(1);await expect(search.getByRole('link')).toContainText('Child Care');
 await page.keyboard.press('Escape');await expect(search).not.toBeVisible();
 await expect(page.getByRole('button',{name:'Search care services'})).toBeFocused();
 await page.locator('.mc-services-menu summary').click();await expect(page.locator('.mc-services-menu a').first()).toBeVisible();
 const before=await page.locator('.mc-story-quote p').textContent();await page.getByRole('button',{name:'Next care story'}).click();assert.notEqual(await page.locator('.mc-story-quote p').textContent(),before);
 await page.getByRole('button',{name:'Published family care update'}).click();await expect(page.getByRole('dialog',{name:'Published family care update'})).toBeVisible();await expect(page.locator('.mc-article-body')).toContainText('complete published');
 await page.getByRole('button',{name:'Close article'}).click();await expect(page.locator('.mc-article-dialog')).not.toBeVisible();
 assert.match(await page.locator('.mc-service-child').evaluate(e=>getComputedStyle(e).backgroundImage),/230, 243, 255/);
 await expect(page.locator('.mc-header-book')).toHaveAttribute('href','/customer/login');
 assert.deepEqual(errors,[]);console.log('PASS search, focus, services menu, carousel, published article, blue child care, visit route');
 await page.close();
}finally{await browser.close();}
