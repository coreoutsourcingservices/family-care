import { chromium } from '@playwright/test';
import { mkdir } from 'node:fs/promises';

const browser = await chromium.launch({ channel: 'chrome', headless: true });
const page = await browser.newPage({ reducedMotion: 'reduce' });
const base = process.env.PREVIEW_URL || 'http://127.0.0.1:5173';
const errors = [];
page.on('pageerror', error => errors.push(error.message));
const assert = (condition, text) => { if (!condition) throw new Error(text); };
await mkdir('app/.preview', { recursive: true });
try {
  for (const route of ['/', '/about', '/services']) {
    for (const width of [360, 768, 1366, 1920]) {
      await page.setViewportSize({ width, height: 900 });
      await page.goto(base + route, { waitUntil: 'networkidle' });
      const layout = await page.evaluate(() => ({
        width: innerWidth, document: document.documentElement.scrollWidth,
        overflow: [...document.querySelectorAll('main *')].filter(element => element.getBoundingClientRect().right > innerWidth + 1 && getComputedStyle(element).position !== 'absolute').slice(0, 5).map(element => element.className),
      }));
      assert(layout.width === layout.document, `${route} ${width}: ${JSON.stringify(layout)}`);
      assert(await page.locator('main h1').count() === 1, `${route}: expected a single page heading`);
      await page.evaluate(() => window.scrollTo(0, 600));
      assert(Math.abs((await page.locator('header').boundingBox()).y) < 1, 'Header is not sticky');
      console.log(`PASS ${route} at ${width}px`);
    }
  }
  await page.setViewportSize({ width: 1366, height: 900 });
  await page.goto(base, { waitUntil: 'networkidle' });
  await page.getByRole('button', { name: 'Get Started', exact: true }).click();
  await page.waitForURL('**/customer/signup');
  await page.goBack({ waitUntil: 'networkidle' });
  await page.getByRole('button', { name: 'Complete a profile', exact: false }).click();
  assert((await page.locator('.step-explanation').innerText()).includes('guardian'), 'Step explanation did not update');
  await page.getByRole('button', { name: 'Women’s Health', exact: true }).click();
  assert(await page.locator('.cycle-calendar').isVisible(), 'Cycle preview missing');
  await page.getByRole('button', { name: 'Pregnancy', exact: true }).click();
  assert((await page.locator('.tracker-example').innerText()).includes('trimester'), 'Pregnancy preview missing');
  await page.getByRole('button', { name: 'PCOS', exact: true }).click();
  assert((await page.locator('.tracker-example').innerText()).includes('diagnosis'), 'PCOS preview missing');
  await page.getByRole('button', { name: 'Adult Health', exact: true }).click();
  await page.getByRole('button', { name: 'Glucose', exact: true }).click();
  assert((await page.locator('.chart-caption').innerText()).includes('Glucose'), 'Glucose preview missing');
  await page.locator('.dashboard-preview').screenshot({ path: 'app/.preview/dashboard-desktop.png' });
  await page.getByRole('button', { name: 'R Raj', exact: true }).click();
  assert((await page.locator('.profile-detail').innerText()).includes('Explicit adult authorization'), 'Family profile selection failed');
  const reminder = page.getByRole('switch', { name: 'Vaccination review preview' });
  const before = await reminder.getAttribute('aria-checked');
  await reminder.click();
  assert((await reminder.getAttribute('aria-checked')) !== before, 'Reminder preview switch failed');
  await page.locator('.faq-list summary').first().click();
  assert(await page.locator('.faq-list details').first().getAttribute('open') !== null, 'FAQ failed');
  await page.getByRole('button', { name: 'Register as a Doctor', exact: true }).click();
  await page.waitForURL('**/doctor/signup');
  for (const path of ['/services/child-care', '/services/womens-health', '/services/adult-health']) {
    await page.goto(base + path, { waitUntil: 'networkidle' });
    assert(await page.locator('.module-features article').count() === 12, `${path}: features missing`);
  }
  await page.goto(`${base}/services/child-care`, { waitUntil: 'networkidle' });
  await page.locator('.site-footer').getByRole('link', { name: 'Women’s Health', exact: true }).click();
  await page.waitForURL('**/services/womens-health');
  await page.waitForFunction(() => document.querySelector('.dashboard-top')?.textContent?.includes('Women’s Health'));
  assert((await page.locator('.dashboard-top').innerText()).includes('Women’s Health'), 'Module preview did not reset after detail-route navigation');
  for (const path of ['/for-doctors', '/contact', '/privacy', '/terms']) {
    await page.goto(base + path, { waitUntil: 'networkidle' });
    assert(await page.getByRole('heading', { name: 'Page not found', exact: true }).count() === 0, `${path}: broken footer link`);
  }
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto(base, { waitUntil: 'networkidle' });
  await page.locator('.dashboard-preview').screenshot({ path: 'app/.preview/dashboard-mobile.png' });
  await page.locator('.site-footer').screenshot({ path: 'app/.preview/footer-mobile.png' });
  assert(errors.length === 0, errors.join('\n'));
  console.log('PASS: sticky header, CTA dialogs, module and tracker tabs, family profiles, reminder switches, FAQ and all new routes.');
} finally { await browser.close(); }
