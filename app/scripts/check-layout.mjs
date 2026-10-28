import { chromium } from '@playwright/test';
import { mkdir } from 'node:fs/promises';

// Run against an already running public website: node app/scripts/check-layout.mjs
const browser = await chromium.launch({ channel: 'chrome', headless: true });
const page = await browser.newPage();
const failures = [];
page.on('pageerror', error => failures.push(error.message));
const base = process.env.PREVIEW_URL || 'http://127.0.0.1:5173';
await mkdir('app/.preview', { recursive: true });
try {
  for (const width of [360, 390, 768, 1024, 1366, 1440, 1920]) {
    await page.setViewportSize({ width, height: 900 });
    await page.goto(base, { waitUntil: 'networkidle' });
    await page.waitForTimeout(1000);
    const layout = await page.evaluate(() => ({
      viewport: innerWidth,
      edgeAligned: document.querySelector('.site-shell').getBoundingClientRect().left === 0 && document.querySelector('.site-shell').getBoundingClientRect().right === document.documentElement.clientWidth,
      maternityHeadingClear: document.querySelector('.pink h2').getBoundingClientRect().bottom <= document.querySelector('.pink .card-photo').getBoundingClientRect().top,
      document: document.documentElement.scrollWidth,
      imagesLoaded: [...document.querySelectorAll('main img')].every(img => img.complete && img.naturalWidth > 0),
      heroBadgeVisible: document.querySelector('.floating-note').getBoundingClientRect().bottom <= document.querySelector('.hero').getBoundingClientRect().bottom,
      cards: [...document.querySelectorAll('.care-card')].map(card => {
        const bounds = card.getBoundingClientRect();
        const button = card.querySelector('.care-button').getBoundingClientRect();
        return button.bottom <= bounds.bottom && button.right <= bounds.right;
      }),
    }));
    if (layout.document > width || !layout.edgeAligned || !layout.maternityHeadingClear || !layout.imagesLoaded || !layout.heroBadgeVisible || layout.cards.some(valid => !valid)) failures.push(`Layout failure at ${width}: ${JSON.stringify(layout)}`);
    if ([390, 1366, 1920].includes(width)) await page.screenshot({ path: `app/.preview/home-${width}.png`, fullPage: true });
    console.log(`Home ${width}px: ${JSON.stringify(layout)}`);
  }
  await page.setViewportSize({ width: 1366, height: 900 });
  await page.goto(base, { waitUntil: 'networkidle' });
  await page.getByRole('link', { name: 'Explore Child Care', exact: true }).click();
  await page.waitForTimeout(500);
  if (!page.url().endsWith('#child') || (await page.locator('#child').boundingBox()).y < -5) failures.push('Service card anchor failed');
  await page.getByRole('button', { name: 'Search services', exact: true }).click();
  await page.getByLabel('Search our services').fill('pregnancy');
  if (await page.locator('.search-results a').count() !== 1) failures.push('Service search failed');
  await page.keyboard.press('Escape');
  if (await page.getByRole('dialog').count()) failures.push('Escape did not close dialog');
  await page.goto(`${base}/about`, { waitUntil: 'networkidle' });
  if (await page.getByRole('heading', { name: 'One family. A lifetime of care.' }).count() !== 1) failures.push('About page failed');
  if (await page.locator('.care-grid').count()) failures.push('About should not repeat the Home service cards');
  for (const width of [390, 1366]) {
    await page.setViewportSize({ width, height: 900 });
    await page.goto(`${base}/services`, { waitUntil: 'networkidle' });
    if (await page.locator('.hero').count() || await page.locator('.care-grid').count()) failures.push('Services should have its own content');
    if (await page.locator('.module-detail').count() !== 3) failures.push('Services sections missing');
    if (await page.locator('.module-features article').count() !== 36) failures.push('Module feature lists incomplete');
    if (await page.evaluate(() => document.documentElement.scrollWidth > innerWidth)) failures.push(`Services overflow at ${width}`);
    await page.getByRole('navigation', { name: 'Service categories' }).getByRole('link', { name: 'Women’s Health' }).click();
    if (!page.url().endsWith('#women')) failures.push('Service category navigation failed');
  }
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto(base, { waitUntil: 'networkidle' });
  await page.getByRole('button', { name: 'Toggle navigation' }).click();
  await page.getByRole('navigation').getByRole('link', { name: 'About Us', exact: true }).click();
  if (!page.url().endsWith('/about')) failures.push('Mobile navigation failed');
  await page.emulateMedia({ reducedMotion: 'reduce' });
  await page.goto(base, { waitUntil: 'networkidle' });
  if (await page.locator('.ambient-scene canvas').count()) failures.push('Reduced-motion scene should be disabled');
  if (failures.length) throw new Error(failures.join('\n'));
  console.log('PASS: responsive layouts, assets, navigation, service anchors, search, dialogs and reduced motion.');
} finally { await browser.close(); }
